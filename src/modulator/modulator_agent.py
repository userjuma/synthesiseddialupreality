import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

from src.config import AudioConfig, GLITCH_PRESETS, GlitchProfile
from src.modulator.fsk_encoder import FSKEncoder
from src.modulator.glitch_engine import GlitchEngine

log = logging.getLogger("AcousticModulator")


class AcousticModulatorAgent:
    def __init__(
        self,
        audio_config: Optional[AudioConfig] = None,
        glitch_profile: Optional[GlitchProfile] = None,
        input_queue: Optional[asyncio.Queue] = None,
        output_queue: Optional[asyncio.Queue] = None,
    ):
        self.audio_cfg = audio_config or AudioConfig()
        self.glitch_profile = glitch_profile or GLITCH_PRESETS["medium"]
        self.input_queue = input_queue or asyncio.Queue()
        self.output_queue = output_queue or asyncio.Queue()

        self.encoder = FSKEncoder(config=self.audio_cfg)
        self.glitch_engine = GlitchEngine(profile=self.glitch_profile, sample_rate=self.audio_cfg.sample_rate)

        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.total_modulated = 0
        self.latest_transmission: Optional[Dict[str, Any]] = None

    def process_payload(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        seq = msg.get("seq", self.total_modulated + 1)
        raw_json = json.dumps(msg, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

        clean_sig, pkt, _ = self.encoder.encode_payload(raw_json, seq_id=seq)
        noisy_sig, metrics = self.glitch_engine.process(clean_sig)

        self.total_modulated += 1
        tx = {
            "seq": seq,
            "timestamp": time.time(),
            "source_payload": msg,
            "raw_bytes_len": len(raw_json),
            "clean_audio": clean_sig,
            "audio_signal": noisy_sig,
            "sample_rate": self.audio_cfg.sample_rate,
            "baud_rate": self.audio_cfg.baud_rate,
            "duration_sec": round(len(noisy_sig) / self.audio_cfg.sample_rate, 3),
            "glitch_metrics": metrics,
            "framed_packet": pkt,
        }
        self.latest_transmission = tx
        return tx

    modulate_and_corrupt = process_payload

    async def run(self):
        self.running = True
        log.info(f"Modulator started [{self.glitch_profile.name}]")

        while self.running:
            try:
                msg = await self.input_queue.get()
                loop = asyncio.get_running_loop()
                tx = await loop.run_in_executor(None, self.process_payload, msg)
                await self.output_queue.put(tx)
                self.input_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.warning(f"Modulator error: {e}")

    def start(self) -> asyncio.Task:
        self.running = True
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run())
        return self._task

    async def stop(self):
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
