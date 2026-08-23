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

        # 20-bit UART framed sync word (0xAA 0x55)
        self.sync_bit_pattern = [0,  0,1,0,1,0,1,0,1,  1,  0,  1,0,1,0,1,0,1,0,  1]

    def find_sync_marker(self, bits: List[int], max_hamming_dist: int = 4) -> Tuple[int, int]:
        """
        Scans demodulated bitstream for the 20-bit framed sync word using sliding Hamming correlator.
        """
        pattern_len = len(self.sync_bit_pattern)
        best_pos = -1
        min_dist = 999

        for i in range(len(bits) - pattern_len):
            window = bits[i : i + pattern_len]
            dist = sum(b1 != b2 for b1, b2 in zip(window, self.sync_bit_pattern))
            if dist < min_dist:
                min_dist = dist
                best_pos = i
                if dist == 0:
                    break

        if min_dist <= max_hamming_dist:
            return best_pos, min_dist
        return -1, min_dist

    def extract_bytes_from_position(self, bits: List[int], start_bit: int) -> bytes:
        """
        Extracts consecutive bytes starting at start_bit using 10-bit UART framing.
        """
        raw_bytes = bytearray()
        idx = start_bit
        n_bits = len(bits)

        while idx + 10 <= n_bits:
            val = 0
            for b in range(8):
                val |= (bits[idx + 1 + b] << b)
            raw_bytes.append(val)
            idx += 10

        return bytes(raw_bytes)

    def repair_json_string(self, raw_str: str) -> Optional[Dict[str, Any]]:
        """
        De-Exorcist: Autonomously reconstructs corrupted/incomplete JSON string
        using regex extraction, bracket balancing, and nested token repair.
        """
        cleaned = "".join(ch for ch in raw_str if ch.isprintable() or ch in "\n\r\t")

        start = cleaned.find("{")
        if start == -1:
            return None

        candidate = cleaned[start:]
        end = candidate.rfind("}")
        if end != -1:
            candidate = candidate[: end + 1]
        else:
            # Count open vs close braces and balance
            open_count = candidate.count("{")
            close_count = candidate.count("}")
            candidate += "}" * max(1, open_count - close_count)

        # Attempt standard parse first
        try:
            return json.loads(candidate)
        except Exception:
            pass

        # Try auto-fixing quotes and trailing commas
        fixed = re.sub(r',\s*}', '}', candidate)
        fixed = re.sub(r',\s*]', ']', fixed)
        try:
            return json.loads(fixed)
        except Exception:
            pass

        # Field-level resilient recovery
        recovered: Dict[str, Any] = {"de_exorcised": True}

        # Match string values
        str_matches = re.findall(r'"([a-zA-Z0-9_\-]+)"\s*:\s*"([^"]*)"', candidate)
        for k, v in str_matches:
            recovered[k] = v

        # Match numeric values
        num_matches = re.findall(r'"([a-zA-Z0-9_\-]+)"\s*:\s*(-?[0-9]+(?:\.[0-9]+)?)', candidate)
        for k, v in num_matches:
            try:
                recovered[k] = float(v) if "." in v else int(v)
            except ValueError:
                recovered[k] = v

        # Reconstruct known namespaces if subfields are present
        if any(k in recovered for k in ["lat", "lon", "alt_km", "vel_kmh"]):
            recovered["iss"] = {
                k: recovered[k] for k in ["lat", "lon", "alt_km", "vel_kmh", "visibility"] if k in recovered
            }
        if any(k in recovered for k in ["temp_c", "humidity_pct", "pressure_hpa", "wind_kmh"]):
            recovered["weather"] = {
                k: recovered[k] for k in ["temp_c", "humidity_pct", "pressure_hpa", "wind_kmh"] if k in recovered
            }
        if any(k in recovered for k in ["flux_mhz", "core_temp_k", "containment_pct", "warp_factor"]):
            recovered["telemetry"] = {
                k: recovered[k] for k in ["flux_mhz", "core_temp_k", "containment_pct", "warp_factor", "entropy_bits"] if k in recovered
            }

        if len(recovered) > 1:
            return recovered
        return None

    def decode_frame(self, bits: List[int]) -> Dict[str, Any]:
        """
        Demodulates bitstream into validated structured JSON state.
        Returns detailed recovery report.
        """
        sync_pos, dist = self.find_sync_marker(bits, max_hamming_dist=4)
        if sync_pos == -1:
            return {
                "status": "NO_SYNC_CARRIER",
                "success": False,
                "confidence_pct": 0.0,
                "payload": None,
                "error": "Frame sync marker 0xAA55 not detected in audio stream."
            }

        frame_bytes = self.extract_bytes_from_position(bits, sync_pos)

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

        # Validate CRC and payload
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
                        "sync_distance": dist
                    }
                except Exception:
                    pass

        # Attempt De-Exorcism repair if noise burst corrupted individual bytes
        raw_text = frame_bytes[6:].decode("utf-8", errors="replace")
        repaired_json = self.repair_json_string(raw_text)

        if repaired_json is not None:
            return {
                "status": "DE_EXORCISED_RECOVERY",
                "success": True,
                "seq": seq_id if 0 < seq_id < 65535 else 1,
                "confidence_pct": max(60.0, 95.0 - (dist * 10.0)),
                "crc_status": "CRC_REPAIRED_VIA_EXORCISM",
                "payload": repaired_json,
                "raw_fragment": raw_text[:100],
                "sync_distance": dist
            }

        return {
            "status": "CORRUPT_GLITCH_BURST",
            "success": False,
            "confidence_pct": 15.0,
            "crc_status": "CRC_FAIL",
            "payload": None,
            "error": "Excessive audio distortion beyond recovery threshold."
        }
