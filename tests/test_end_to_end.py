"""
End-to-End Pipeline Integration Tests.
Verifies complete flow: Data Ingest -> FSK Modulation -> Glitch Degradation -> DSP Listening -> JSON Reconstruction.
"""

import json
import unittest

from src.config import AudioConfig, GLITCH_PRESETS
from src.ingest.live_feed import get_feed_provider
from src.modulator.fsk_encoder import FSKEncoder
from src.modulator.glitch_engine import GlitchEngine
from src.listener.dsp_tools import AnalyzeAudio
from src.listener.decoder import PacketDecoder


class TestEndToEndPipeline(unittest.TestCase):

    def setUp(self):
        self.config = AudioConfig(sample_rate=22050, baud_rate=600)
        self.encoder = FSKEncoder(config=self.config)
        self.decoder = PacketDecoder(config=self.config)

    def _run_pipeline_cycle(self, feed_type: str, glitch_preset: str):
        # 1. Ingest
        provider = get_feed_provider(feed_type)
        payload = provider.fetch_payload()
        json_bytes = json.dumps(payload, separators=(',', ':')).encode("utf-8")

        # 2. Modulate
        clean_audio, packet, bits = self.encoder.encode_payload(json_bytes, seq_id=payload.get("seq", 1))

        # 3. Corrupt
        glitch_engine = GlitchEngine(profile=GLITCH_PRESETS[glitch_preset], sample_rate=self.config.sample_rate)
        corrupted_audio, glitch_metrics = glitch_engine.process(clean_audio)

        # 4. DSP Listen & Demodulate
        analysis = AnalyzeAudio(corrupted_audio, config=self.config)

        # 5. Decode & Reconstruct
        recovery = self.decoder.decode_frame(analysis["bits"])
        return payload, recovery, glitch_metrics

    def test_crypto_feed_pristine(self):
        orig, recovery, metrics = self._run_pipeline_cycle("crypto", "pristine")
        self.assertTrue(recovery["success"])
        self.assertEqual(recovery["status"], "CLEAN_RECOVERY")
        self.assertEqual(recovery["payload"]["source"], orig["source"])

    def test_weather_feed_medium_glitch(self):
        orig, recovery, metrics = self._run_pipeline_cycle("weather", "medium")
        self.assertTrue(recovery["success"])
        self.assertIn("weather", recovery["payload"])

    def test_nasa_feed_low_glitch(self):
        orig, recovery, metrics = self._run_pipeline_cycle("nasa", "low")
        self.assertTrue(recovery["success"])
        self.assertIn("iss", recovery["payload"])

    def test_synthetic_feed_medium_glitch(self):
        orig, recovery, metrics = self._run_pipeline_cycle("synthetic", "medium")
        self.assertTrue(recovery["success"])
        self.assertIn("telemetry", recovery["payload"])


if __name__ == "__main__":
    unittest.main()
