"""
Tests for 1990s Glitch Engine Degradation & Analog Channel Simulation.
"""

import unittest
import numpy as np

from src.config import GLITCH_PRESETS
from src.modulator.glitch_engine import GlitchEngine


class TestGlitchEngine(unittest.TestCase):

    def setUp(self):
        self.sample_rate = 22050
        # 1 second test sine wave at 1200 Hz
        t = np.arange(self.sample_rate, dtype=np.float32) / float(self.sample_rate)
        self.clean_audio = (0.8 * np.sin(2.0 * np.pi * 1200.0 * t)).astype(np.float32)

    def test_pristine_profile_preserves_signal(self):
        engine = GlitchEngine(profile=GLITCH_PRESETS["pristine"], sample_rate=self.sample_rate)
        corrupted, metrics = engine.process(self.clean_audio)
        self.assertEqual(metrics["burst_events"], 0)
        self.assertGreaterEqual(metrics["snr_db"], 50.0)

    def test_medium_profile_injects_realistic_noise(self):
        engine = GlitchEngine(profile=GLITCH_PRESETS["medium"], sample_rate=self.sample_rate)
        corrupted, metrics = engine.process(self.clean_audio)
        self.assertLess(metrics["snr_db"], 40.0)
        self.assertLessEqual(np.max(np.abs(corrupted)), 1.05)

    def test_bit_crushing_quantization(self):
        engine = GlitchEngine(profile=GLITCH_PRESETS["demonic"], sample_rate=self.sample_rate)
        crushed = engine.apply_bit_crushing(self.clean_audio)
        unique_levels = len(np.unique(np.round(crushed, 2)))
        self.assertLess(unique_levels, 30)

    def test_telephony_bandpass_attenuation(self):
        engine = GlitchEngine(sample_rate=self.sample_rate)
        # 50 Hz sub-bass (outside phone line band)
        t = np.arange(self.sample_rate, dtype=np.float32) / float(self.sample_rate)
        bass = np.sin(2.0 * np.pi * 50.0 * t).astype(np.float32)
        filtered = engine.apply_telephony_bandpass(bass)
        self.assertLess(np.max(np.abs(filtered)), 0.15)


if __name__ == "__main__":
    unittest.main()
