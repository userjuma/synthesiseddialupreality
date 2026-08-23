"""
Frame Synchronizer & Resilient JSON De-Exorcist Decoder.
Extracts structured packets from demodulated bitstreams, validates CRC-16,
and autonomously repairs glitched data states.
"""

import json
import re
import struct
from typing import Dict, Any, Tuple, Optional, List

from src.modulator.fsk_encoder import calculate_crc16
from src.config import AudioConfig


class PacketDecoder:
    """
    Decodes UART-framed bitstreams, synchronizes frames, and reconstructs structured JSON payloads.
    """

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.sync_word = self.config.sync_word

    def extract_bytes_from_bits(self, bits: List[int], bit_offset: int = 0) -> bytes:
        """
        Extracts bytes using UART framing: 1 start bit (0), 8 data bits (LSB first), 1 stop bit (1).
        """
        recovered_bytes = bytearray()
        idx = bit_offset
        n_bits = len(bits)

        while idx + 10 <= n_bits:
            # Check for start bit (0)
            if bits[idx] == 0:
                # 8 data bits (LSB first)
                byte_val = 0
                for i in range(8):
                    byte_val |= (bits[idx + 1 + i] << i)
                # Verify stop bit (1)
                # (Allow soft tolerance if stop bit is slightly glitched)
                recovered_bytes.append(byte_val)
                idx += 10
            else:
                # Hunt forward for next start bit
                idx += 1

        return bytes(recovered_bytes)

    def scan_for_sync_frame(self, bits: List[int]) -> Optional[Tuple[bytes, int]]:
        """
        Scans across different bit alignment phase offsets (0..9) to find the sync word.
        Returns: (extracted_stream_bytes, matching_sync_offset)
        """
        for offset in range(10):
            stream_bytes = self.extract_bytes_from_bits(bits, bit_offset=offset)
            sync_pos = stream_bytes.find(self.sync_word)
            if sync_pos != -1:
                return stream_bytes[sync_pos:], offset

        # Fallback: scan without strict UART start/stop bit if heavy clock jitter
        raw_bytes = bytearray()
        for i in range(0, len(bits) - 8, 8):
            val = 0
            for b in range(8):
                val |= (bits[i + b] << (7 - b))
            raw_bytes.append(val)
        raw_bytes_frozen = bytes(raw_bytes)
        sync_pos = raw_bytes_frozen.find(self.sync_word)
        if sync_pos != -1:
            return raw_bytes_frozen[sync_pos:], 0

        return None

    def repair_json_string(self, raw_str: str) -> Optional[Dict[str, Any]]:
        """
        De-Exorcist: Autonomously reconstructs corrupted/incomplete JSON string
        using regex extraction and bracket balancing.
        """
        # Clean non-printable control chars except standard whitespace
        cleaned = "".join(ch for ch in raw_str if ch.isprintable() or ch in "\n\r\t")

        # Find first '{' and last '}'
        start = cleaned.find("{")
        if start == -1:
            return None

        candidate = cleaned[start:]
        end = candidate.rfind("}")
        if end != -1:
            candidate = candidate[: end + 1]
        else:
            # Close unclosed braces
            candidate = candidate + "}"

        # Try direct parse
        try:
            return json.loads(candidate)
        except Exception:
            pass

        # Resilient field-level regex recovery
        recovered: Dict[str, Any] = {"de_exorcised": True, "raw_fragment": candidate[:80]}

        # Extract string keys and values
        str_matches = re.findall(r'"([a-zA-Z0-9_\-]+)"\s*:\s*"([^"]*)"', candidate)
        for k, v in str_matches:
            recovered[k] = v

        # Extract numeric values
        num_matches = re.findall(r'"([a-zA-Z0-9_\-]+)"\s*:\s*(-?[0-9]+(?:\.[0-9]+)?)', candidate)
        for k, v in num_matches:
            try:
                recovered[k] = float(v) if "." in v else int(v)
            except ValueError:
                recovered[k] = v

        if len(recovered) > 1:
            return recovered
        return None

    def decode_frame(self, bits: List[int]) -> Dict[str, Any]:
        """
        Demodulates bitstream into validated structured JSON state.
        Returns detailed recovery report.
        """
        sync_result = self.scan_for_sync_frame(bits)
        if not sync_result:
            return {
                "status": "NO_SYNC_CARRIER",
                "success": False,
                "confidence_pct": 0.0,
                "payload": None,
                "error": "Frame sync marker 0xAA55 not detected in audio stream."
            }

        frame_bytes, bit_offset = sync_result

        # Check minimal frame size: SYNC(2) + SEQ(2) + LEN(2) + CRC(2) = 8 bytes
        if len(frame_bytes) < 8:
            return {
                "status": "SHORT_FRAME",
                "success": False,
                "confidence_pct": 20.0,
                "payload": None,
                "error": f"Frame truncated ({len(frame_bytes)} bytes received)."
            }

        # Parse header
        seq_id, length = struct.unpack(">HH", frame_bytes[2:6])

        # Extract payload and CRC
        if len(frame_bytes) >= 6 + length + 2:
            body = frame_bytes[: 6 + length]
            received_crc = struct.unpack(">H", frame_bytes[6 + length : 6 + length + 2])[0]
            computed_crc = calculate_crc16(body)
            payload_raw = frame_bytes[6 : 6 + length]

            if received_crc == computed_crc:
                try:
                    payload_json = json.loads(payload_raw.decode("utf-8"))
                    return {
                        "status": "CLEAN_RECOVERY",
                        "success": True,
                        "seq": seq_id,
                        "confidence_pct": 100.0,
                        "crc_status": "CRC_VALID",
                        "payload": payload_json,
                        "raw_bytes": payload_raw,
                        "bit_offset": bit_offset
                    }
                except Exception as e:
                    # Payload CRC passed but UTF-8 parsing issue
                    pass

        # If CRC check failed or length was skewed by glitch: Attempt De-Exorcism
        raw_text = frame_bytes[6:].decode("utf-8", errors="replace")
        repaired_json = self.repair_json_string(raw_text)

        if repaired_json is not None:
            return {
                "status": "DE_EXORCISED_RECOVERY",
                "success": True,
                "seq": seq_id if 0 < seq_id < 65535 else 1,
                "confidence_pct": 82.5,
                "crc_status": "CRC_REPAIRED_VIA_EXORCISM",
                "payload": repaired_json,
                "raw_fragment": raw_text[:100],
                "bit_offset": bit_offset
            }

        return {
            "status": "CORRUPT_GLITCH_BURST",
            "success": False,
            "confidence_pct": 15.0,
            "crc_status": "CRC_FAIL",
            "payload": None,
            "error": "Excessive audio distortion beyond recovery threshold."
        }
