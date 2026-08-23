import asyncio
import logging
import time
from typing import Any, Dict, Optional
import numpy as np

from src.config import AudioConfig
from src.listener.decoder import PacketDecoder
from src.listener.dsp_tools import AnalyzeAudio

log = logging.getLogger("ReconstructiveListener")


class ReconstructiveListenerAgent:
    def __init__(
        self,
        audio_config: Optional[AudioConfig] = None,
        input_queue: Optional[asyncio.Queue] = None,
        output_queue: Optional[asyncio.Queue] = None,
    ):
        self.audio_cfg = audio_config or AudioConfig()
        self.input_queue = input_queue or asyncio.Queue()
        self.output_queue = output_queue or asyncio.Queue()

        self.decoder = PacketDecoder(config=self.audio_cfg)
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.total_processed = 0
        self.successful = 0
        self.latest_result: Optional[Dict[str, Any]] = None

    def process_transmission(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.time()
        audio_sig = tx.get("audio_signal")
        seq = tx.get("seq", 0)

        analysis = AnalyzeAudio(audio_sig, config=self.audio_cfg)
        decoded = self.decoder.decode_frame(analysis["bits"])

        elapsed_ms = round((time.time() - t0) * 1000.0, 2)
        self.total_processed += 1
        if decoded.get("success", False):
            self.successful += 1

        rec = {
            "seq": seq,
            "timestamp": time.time(),
            "decode_status": decoded.get("status"),
            "success": decoded.get("success", False),
            "confidence_pct": decoded.get("confidence_pct", 0.0),
            "crc_status": decoded.get("crc_status", "UNKNOWN"),
            "recovery_method": decoded.get("recovery_method", "MATCHED_FILTER"),
            "reconstructed_json": decoded.get("payload"),
            "original_json": tx.get("source_payload"),
            "glitch_metrics": tx.get("glitch_metrics", {}),
            "dsp_metrics": {
                "snr_est_db": analysis.get("snr_est_db", 0.0),
                "space_corr": analysis.get("space_corr", 0.0),
                "mark_corr": analysis.get("mark_corr", 0.0),
                "total_bits_recovered": len(analysis["bits"]),
                "processing_time_ms": elapsed_ms,
                "success_rate_pct": round((self.successful / self.total_processed) * 100.0, 1),
            },
            "spectral_slice": {
                "freqs": analysis["spectrum_freqs"],
                "mag_db": analysis["spectrum_mag_db"],
            },
            "waveform_slice": analysis.get("waveform_slice", audio_sig[:512]),
        }
        self.latest_result = rec
        return rec

    reconstruct_from_audio = process_transmission

    async def run(self):
        self.running = True
        log.info("Listener online")

        while self.running:
            try:
                tx = await self.input_queue.get()
                loop = asyncio.get_running_loop()
                rec = await loop.run_in_executor(None, self.process_transmission, tx)
                await self.output_queue.put(rec)
                self.input_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.warning(f"Listener error: {e}")

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
