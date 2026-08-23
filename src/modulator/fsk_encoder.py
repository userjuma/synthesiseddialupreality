"""
Bell 103 / AFSK Audio Frequency Shift Keying Modulator.
Converts structured data / JSON bytes into continuous-phase acoustic audio waveforms.
"""

import math
import struct
from typing import Tuple, List, Optional
import numpy as np

from src.config import AudioConfig


def calculate_crc16(data: bytes) -> int:
    """CRC-16-CCITT (poly 0x1021, init 0xFFFF)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


class FSKEncoder:
    """
    Continuous-Phase Frequency Shift Keying (CPFSK) Audio Modulator.
    Implements Bell 103 standard tones (1070 Hz Space / 1270 Hz Mark).
    """

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.sample_rate = self.config.sample_rate
        self.mark_freq = self.config.mark_freq
        self.space_freq = self.config.space_freq
        self.baud_rate = self.config.baud_rate
        self.samples_per_bit = int(self.sample_rate / self.baud_rate)
        self.sync_word = self.config.sync_word

    def frame_packet(self, payload: bytes, seq_id: int = 0) -> bytes:
        """
        Creates a framed packet:
        [SYNC (2 bytes)] [SEQ (2 bytes)] [LEN (2 bytes)] [PAYLOAD (N bytes)] [CRC16 (2 bytes)]
        """
        length = len(payload)
        header = self.sync_word + struct.pack(">HH", seq_id & 0xFFFF, length)
        body = header + payload
        crc = calculate_crc16(body)
        packet = body + struct.pack(">H", crc)
        return packet

    def bytes_to_bits(self, data: bytes) -> List[int]:
        """
        Converts bytes into a list of UART-framed bits (1 start bit [0], 8 data bits [LSB first], 1 stop bit [1]).
        """
        bits = []
        # Preamble carrier: continuous Mark tone (1) for carrier lock
        for _ in range(self.config.preamble_bits):
            bits.append(1)

        for byte in data:
            if self.config.use_start_stop_bits:
                # 1 Start bit (Space = 0)
                bits.append(0)
                # 8 Data bits (LSB first)
                for i in range(8):
                    bits.append((byte >> i) & 1)
                # 1 Stop bit (Mark = 1)
                bits.append(1)
            else:
                # Direct MSB-first raw bits
                for i in range(7, -1, -1):
                    bits.append((byte >> i) & 1)

        # Postamble carrier
        for _ in range(self.config.postamble_bits):
            bits.append(1)

        return bits

    def modulate_bits(self, bits: List[int]) -> np.ndarray:
        """
        Synthesizes a continuous-phase FSK acoustic audio waveform from bitstream.
        Returns 1D float32 numpy array normalized to [-1.0, 1.0].
        """
        total_samples = len(bits) * self.samples_per_bit
        audio = np.zeros(total_samples, dtype=np.float32)

        phase = 0.0
        two_pi = 2.0 * math.pi
        sr = float(self.sample_rate)

        write_idx = 0
        for bit in bits:
            freq = self.mark_freq if bit == 1 else self.space_freq
            phase_inc = (two_pi * freq) / sr

            n = np.arange(self.samples_per_bit)
            symbol_phase = phase + (n * phase_inc)
            audio[write_idx : write_idx + self.samples_per_bit] = self.config.amplitude * np.sin(symbol_phase)

            phase = (phase + (self.samples_per_bit * phase_inc)) % two_pi
            write_idx += self.samples_per_bit

        return audio

    def encode_payload(self, payload_bytes: bytes, seq_id: int = 0) -> Tuple[np.ndarray, bytes, List[int]]:
        """
        High-level helper: Frames payload bytes, generates bitstream, and synthesizes audio waveform.
        Returns: (audio_waveform, packet_bytes, bits)
        """
        packet = self.frame_packet(payload_bytes, seq_id=seq_id)
        bits = self.bytes_to_bits(packet)
        audio = self.modulate_bits(bits)
        return audio, packet, bits
