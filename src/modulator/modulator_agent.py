"""
Agent B: The Acoustic Modulator & Glitch Engine.
Transforms structured JSON from Agent A into an encoded acoustic Bell 103 FSK waveform,
applies radical 1990s analog and digital degradation, and publishes the corrupted audio signal.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, Tuple
import numpy as np

from src.config import AudioConfig, GlitchProfile, GLITCH_PRESETS
from src.modulator.fsk_encoder import FSKEncoder
from src.modulator.glitch_engine import GlitchEngine

logger = logging.getLogger("AcousticModulatorAgent")


class AcousticModulatorAgent:
    """
    Agent B: Ingests JSON -> Encodes to Bell 103 FSK -> Corrupts via Glitch Engine -> Emits to audio_transmission stream.
    """

    def __init__(
        self,
        audio_config: Optional[AudioConfig] = None,
        glitch_profile: Optional[GlitchProfile] = None,
        input_queue: Optional[asyncio.Queue] = None,
        output_queue: Optional[asyncio.Queue] = None
    ):
        self.audio_config = audio_config or AudioConfig()
        self.glitch_profile = glitch_profile or GLITCH_PRESETS["medium"]
        self.input_queue = input_queue or asyncio.Queue()
        self.output_queue = output_queue or asyncio.Queue()

        self.encoder = FSKEncoder(config=self.audio_config)
        self.glitch_engine = GlitchEngine(
            profile=self.glitch_profile,
            sample_rate=self.audio_config.sample_rate
        )

        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.total_modulated = 0
        self.latest_transmission: Optional[Dict[str, Any]] = None

    def modulate_and_corrupt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous processing pipeline:
        JSON Dict -> JSON Bytes -> FSK Audio -> Glitch Engine -> Transmission Package
        """
        seq_id = payload.get("seq", self.total_modulated + 1)
        # Minified canonical JSON
        json_bytes = json.dumps(payload, separators=(',', ':'), ensure_ascii=True).encode("utf-8")

        # Step 1: Bell 103 FSK Modulation
        clean_audio, framed_packet, bits = self.encoder.encode_payload(json_bytes, seq_id=seq_id)

        # Step 2: Radical 1990s Analog & Digital Degradation
        corrupted_audio, glitch_metrics = self.glitch_engine.process(clean_audio)

        self.total_modulated += 1
        transmission = {
            "seq": seq_id,
            "timestamp": time.time(),
            "source_payload": payload,
            "raw_bytes_len": len(json_bytes),
            "clean_audio": clean_audio,
            "audio_signal": corrupted_audio,
            "sample_rate": self.audio_config.sample_rate,
            "baud_rate": self.audio_config.baud_rate,
            "duration_sec": round(len(corrupted_audio) / self.audio_config.sample_rate, 3),
            "glitch_metrics": glitch_metrics,
            "framed_packet": framed_packet
        }
        self.latest_transmission = transmission
        return transmission

    async def run(self):
        """Continuous consumer loop listening to input_data and pushing to audio_transmission."""
        self.is_running = True
        logger.info(f"AcousticModulatorAgent started with Glitch Profile: {self.glitch_profile.name}")

        while self.is_running:
            try:
                # Wait for structured payload from Agent A
                payload = await self.input_queue.get()
                loop = asyncio.get_running_loop()

                # Modulate and apply glitch corruption in thread pool
                transmission = await loop.run_in_executor(None, self.modulate_and_corrupt, payload)

                # Publish noisy signal to audio_transmission stream
                await self.output_queue.put(transmission)
                logger.debug(
                    f"[Agent B] Modulated seq={transmission['seq']}, "
                    f"duration={transmission['duration_sec']}s, "
                    f"SNR={transmission['glitch_metrics']['snr_db']}dB"
                )

                self.input_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Agent B] Modulation error: {e}")

        logger.info("AcousticModulatorAgent stopped.")

    def start(self) -> asyncio.Task:
        self.is_running = True
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run())
        return self._task

    async def stop(self):
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
