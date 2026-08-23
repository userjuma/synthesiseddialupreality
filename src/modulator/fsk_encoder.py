import math
import struct
from typing import List, Optional, Tuple
import numpy as np

from src.config import AudioConfig


def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


calculate_crc16 = crc16_ccitt


class FSKEncoder:
    def __init__(self, config: Optional[AudioConfig] = None):
        self.cfg = config or AudioConfig()
        self.sr = self.cfg.sample_rate
        self.mark_freq = self.cfg.mark_freq
        self.space_freq = self.cfg.space_freq
        self.baud = self.cfg.baud_rate
        self.spb = int(self.sr / self.baud)
        self.sync_word = self.cfg.sync_word

    def frame(self, payload: bytes, seq: int = 0) -> bytes:
        hdr = self.sync_word + struct.pack(">HH", seq & 0xFFFF, len(payload))
        body = hdr + payload
        return body + struct.pack(">H", crc16_ccitt(body))

    def frame_packet(self, payload: bytes, seq_id: int = 0) -> bytes:
        return self.frame(payload, seq=seq_id)

    def to_bits(self, data: bytes) -> List[int]:
        bits = [1] * self.cfg.preamble_bits

        for byte in data:
            bits.append(0)  # Start bit
            for i in range(8):
                bits.append((byte >> i) & 1)
            bits.append(1)  # Stop bit

        bits.extend([1] * self.cfg.postamble_bits)
        return bits

    def bytes_to_bits(self, data: bytes) -> List[int]:
        return self.to_bits(data)

    def modulate(self, bits: List[int]) -> np.ndarray:
        audio = np.zeros(len(bits) * self.spb, dtype=np.float32)
        phase = 0.0
        two_pi = 2.0 * math.pi
        sr = float(self.sr)

        idx = 0
        for bit in bits:
            freq = self.mark_freq if bit == 1 else self.space_freq
            d_phase = (two_pi * freq) / sr

            n = np.arange(self.spb)
            audio[idx : idx + self.spb] = self.cfg.amplitude * np.sin(phase + n * d_phase)
            phase = (phase + self.spb * d_phase) % two_pi
            idx += self.spb

        return audio

    def modulate_bits(self, bits: List[int]) -> np.ndarray:
        return self.modulate(bits)

    def encode_payload(self, payload: bytes, seq_id: int = 0) -> Tuple[np.ndarray, bytes, List[int]]:
        pkt = self.frame(payload, seq=seq_id)
        bits = self.to_bits(pkt)
        audio = self.modulate(bits)
        return audio, pkt, bits
