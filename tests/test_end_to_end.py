import json
import unittest

from src.config import AudioConfig, GLITCH_PRESETS
from src.ingest.live_feed import get_feed_provider
from src.listener.decoder import PacketDecoder
from src.listener.dsp_tools import AnalyzeAudio
from src.modulator.fsk_encoder import FSKEncoder
from src.modulator.glitch_engine import GlitchEngine


class TestEndToEndPipeline(unittest.TestCase):
    def setUp(self):
        self.cfg = AudioConfig(sample_rate=22050, baud_rate=600)
        self.encoder = FSKEncoder(config=self.cfg)
        self.decoder = PacketDecoder(config=self.cfg)

    def _cycle(self, feed: str, preset: str):
        payload = get_feed_provider(feed).fetch()
        raw_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        clean_audio, _, _ = self.encoder.encode_payload(raw_bytes, seq_id=payload.get("seq", 1))

        glitch = GlitchEngine(profile=GLITCH_PRESETS[preset], sample_rate=self.cfg.sample_rate)
        noisy_audio, metrics = glitch.process(clean_audio)

        analysis = AnalyzeAudio(noisy_audio, config=self.cfg)
        rec = self.decoder.decode_frame(analysis["bits"])
        return payload, rec, metrics

    def test_crypto_feed_pristine(self):
        orig, rec, _ = self._cycle("crypto", "pristine")
        self.assertTrue(rec["success"])
        self.assertEqual(rec["status"], "MATCHED_FILTER_CLEAN")
        self.assertEqual(rec["payload"]["source"], orig["source"])

    def test_weather_feed_medium_glitch(self):
        _, rec, _ = self._cycle("weather", "medium")
        self.assertTrue(rec["success"])
        self.assertTrue("weather" in rec["payload"] or "temp_c" in rec["payload"])

    def test_nasa_feed_low_glitch(self):
        _, rec, _ = self._cycle("nasa", "low")
        self.assertTrue(rec["success"])
        self.assertTrue("iss" in rec["payload"] or "lat" in rec["payload"])

    def test_synthetic_feed_medium_glitch(self):
        _, rec, _ = self._cycle("synthetic", "medium")
        self.assertTrue(rec["success"])
        self.assertTrue("telemetry" in rec["payload"] or "flux_mhz" in rec["payload"])


if __name__ == "__main__":
    unittest.main()
