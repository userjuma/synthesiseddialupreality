"""
Tests for Bell 103 FSK Modulation & CRC Calculation.
"""

import unittest
import numpy as np

from src.config import AudioConfig
from src.modulator.fsk_encoder import FSKEncoder, calculate_crc16


class TestFSKModulator(unittest.TestCase):

    def setUp(self):
        self.config = AudioConfig(sample_rate=22050, baud_rate=600)
        self.encoder = FSKEncoder(config=self.config)

    def test_crc16_deterministic(self):
        data = b"HELLO_1990S_DIALUP"
        crc1 = calculate_crc16(data)
        crc2 = calculate_crc16(data)
        self.assertEqual(crc1, crc2)
        self.assertIsInstance(crc1, int)
        self.assertTrue(0 <= crc1 <= 0xFFFF)

    def test_frame_packet_structure(self):
        payload = b'{"temp":21.5}'
        packet = self.encoder.frame_packet(payload, seq_id=42)

        # Sync marker check
        self.assertTrue(packet.startswith(self.config.sync_word))
        # Total size: Sync(2) + Seq(2) + Len(2) + Payload(len) + CRC(2)
        expected_len = 2 + 2 + 2 + len(payload) + 2
        self.assertEqual(len(packet), expected_len)

    def test_audio_waveform_synthesis(self):
        payload = b'{"status":"ok"}'
        audio, packet, bits = self.encoder.encode_payload(payload, seq_id=1)

        self.assertIsInstance(audio, np.ndarray)
        self.assertEqual(audio.dtype, np.float32)
        self.assertTrue(len(audio) > 0)
        # Check peak amplitude bounds
        self.assertLessEqual(np.max(np.abs(audio)), 1.0)
        self.assertGreater(np.max(np.abs(audio)), 0.1)


if __name__ == "__main__":
    unittest.main()
