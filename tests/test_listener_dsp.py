import json
import unittest

from src.config import AudioConfig
from src.listener.decoder import PacketDecoder
from src.listener.dsp_tools import AnalyzeAudio, AudioDSPAnalyzer
from src.modulator.fsk_encoder import FSKEncoder


class TestListenerDSP(unittest.TestCase):
    def setUp(self):
        self.cfg = AudioConfig(sample_rate=22050, baud_rate=600)
        self.encoder = FSKEncoder(config=self.cfg)
        self.analyzer = AudioDSPAnalyzer(config=self.cfg)
        self.decoder = PacketDecoder(config=self.cfg)

    def test_analyze_audio_tool(self):
        payload = b'{"node":"alpha","val":120}'
        audio, packet, bits = self.encoder.encode_payload(payload, seq_id=10)
        res = AnalyzeAudio(audio, config=self.cfg)

        self.assertIn("bits", res)
        self.assertIn("spectrum_freqs", res)
        self.assertIn("spectrum_mag_db", res)
        self.assertGreater(len(res["bits"]), len(payload))

    def test_decode_clean_frame(self):
        data = {"source": "STATION_90", "alt": 420.5, "active": True}
        raw_bytes = json.dumps(data, separators=(",", ":")).encode("utf-8")
        audio, _, _ = self.encoder.encode_payload(raw_bytes, seq_id=7)

        analysis = AnalyzeAudio(audio, config=self.cfg)
        rec = self.decoder.decode_frame(analysis["bits"])

        self.assertTrue(rec["success"])
        self.assertEqual(rec["status"], "MATCHED_FILTER_CLEAN")
        self.assertEqual(rec["payload"], data)

    def test_resilient_json_salvage(self):
        corrupted = '##STATIC##{"source":"STATION_90","alt":420.5,"active":"true"}~~NOISE'
        repaired = self.decoder.repair_json(corrupted)
        self.assertIsNotNone(repaired)
        self.assertEqual(repaired.get("source"), "STATION_90")
        self.assertEqual(repaired.get("alt"), 420.5)


if __name__ == "__main__":
    unittest.main()
