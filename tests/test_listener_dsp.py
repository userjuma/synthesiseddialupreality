"""
Tests for DSP Analysis Tooling, Demodulation, and Resilient JSON Reconstruction.
"""

import json
import unittest
import numpy as np

from src.config import AudioConfig
from src.modulator.fsk_encoder import FSKEncoder
from src.listener.dsp_tools import AnalyzeAudio, AudioDSPAnalyzer
from src.listener.decoder import PacketDecoder


class TestListenerDSP(unittest.TestCase):

    def setUp(self):
        self.config = AudioConfig(sample_rate=22050, baud_rate=600)
        self.encoder = FSKEncoder(config=self.config)
        self.analyzer = AudioDSPAnalyzer(config=self.config)
        self.decoder = PacketDecoder(config=self.config)

    def test_analyze_audio_tool_interface(self):
        payload = b'{"node":"alpha","val":120}'
        audio, packet, bits = self.encoder.encode_payload(payload, seq_id=10)

        # Execute AnalyzeAudio tool
        result = AnalyzeAudio(audio, config=self.config)

        self.assertIn("bits", result)
        self.assertIn("spectrum_freqs", result)
        self.assertIn("spectrum_mag_db", result)
        self.assertIn("snr_est_db", result)
        self.assertGreater(len(result["bits"]), len(payload))

    def test_decode_clean_frame(self):
        payload_dict = {"source": "TEST_STATION", "altitude": 420.5, "active": True}
        payload_bytes = json.dumps(payload_dict, separators=(',', ':')).encode("utf-8")
        audio, packet, bits = self.encoder.encode_payload(payload_bytes, seq_id=7)

        analysis = AnalyzeAudio(audio, config=self.config)
        decode_result = self.decoder.decode_frame(analysis["bits"])

        self.assertTrue(decode_result["success"])
        self.assertEqual(decode_result["status"], "CLEAN_RECOVERY")
        self.assertEqual(decode_result["payload"], payload_dict)

    def test_resilient_de_exorcism_repair(self):
        corrupted_text = '##NOISE##{"source":"TEST_STATION","altitude":420.5,"active":"true"}~~STATIC'
        repaired = self.decoder.repair_json_string(corrupted_text)

        self.assertIsNotNone(repaired)
        self.assertEqual(repaired.get("source"), "TEST_STATION")
        self.assertEqual(repaired.get("altitude"), 420.5)


if __name__ == "__main__":
    unittest.main()
