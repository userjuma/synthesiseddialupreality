import unittest
import numpy as np

from src.config import AudioConfig
from src.modulator.fsk_encoder import FSKEncoder, crc16_ccitt


class TestFSKModulator(unittest.TestCase):
    def setUp(self):
        self.cfg = AudioConfig(sample_rate=22050, baud_rate=600)
        self.encoder = FSKEncoder(config=self.cfg)

    def test_crc16_deterministic(self):
        data = b"DIALUP_TEST_1990S"
        self.assertEqual(crc16_ccitt(data), crc16_ccitt(data))
        self.assertTrue(0 <= crc16_ccitt(data) <= 0xFFFF)

    def test_frame_packet_structure(self):
        payload = b'{"temp":21.5}'
        packet = self.encoder.frame(payload, seq=42)
        self.assertTrue(packet.startswith(self.cfg.sync_word))
        # Sync(2) + Seq(2) + Len(2) + Payload + CRC(2)
        self.assertEqual(len(packet), 2 + 2 + 2 + len(payload) + 2)

    def test_audio_waveform_synthesis(self):
        audio, packet, bits = self.encoder.encode_payload(b'{"status":"ok"}', seq_id=1)
        self.assertEqual(audio.dtype, np.float32)
        self.assertTrue(0.1 < np.max(np.abs(audio)) <= 1.0)


if __name__ == "__main__":
    unittest.main()
