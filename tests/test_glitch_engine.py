import unittest
import numpy as np

from src.config import GLITCH_PRESETS
from src.modulator.glitch_engine import GlitchEngine


class TestGlitchEngine(unittest.TestCase):
    def setUp(self):
        self.sr = 22050
        t = np.arange(self.sr, dtype=np.float32) / float(self.sr)
        self.clean = (0.8 * np.sin(2.0 * np.pi * 1200.0 * t)).astype(np.float32)

    def test_pristine_preserves_signal(self):
        engine = GlitchEngine(profile=GLITCH_PRESETS["pristine"], sample_rate=self.sr)
        corrupted, metrics = engine.process(self.clean)
        self.assertEqual(metrics["burst_events"], 0)
        self.assertGreaterEqual(metrics["snr_db"], 50.0)

    def test_medium_profile_noise(self):
        engine = GlitchEngine(profile=GLITCH_PRESETS["medium"], sample_rate=self.sr)
        corrupted, metrics = engine.process(self.clean)
        self.assertLess(metrics["snr_db"], 40.0)
        self.assertLessEqual(np.max(np.abs(corrupted)), 1.05)

    def test_bit_crushing_levels(self):
        engine = GlitchEngine(profile=GLITCH_PRESETS["demonic"], sample_rate=self.sr)
        crushed = engine.bit_crush(self.clean)
        unique_levels = len(np.unique(np.round(crushed, 2)))
        self.assertLess(unique_levels, 30)

    def test_telephony_bandpass_attenuation(self):
        engine = GlitchEngine(sample_rate=self.sr)
        t = np.arange(self.sr, dtype=np.float32) / float(self.sr)
        bass = np.sin(2.0 * np.pi * 50.0 * t).astype(np.float32)
        filtered = engine.bandpass(bass)
        self.assertLess(np.max(np.abs(filtered)), 0.15)


if __name__ == "__main__":
    unittest.main()
