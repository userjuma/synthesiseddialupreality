"""
Agent C: The Reconstructive Listener (Feed 3: Exorcism).
Listens to corrupted audio stream, uses AnalyzeAudio(signal) DSP tools to detect
frequencies and symbols through noise, and autonomously reconstructs original structured JSON.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
import numpy as np

from src.config import AudioConfig
from src.listener.dsp_tools import AnalyzeAudio
from src.listener.decoder import PacketDecoder

logger = logging.getLogger("ReconstructiveListenerAgent")


class ReconstructiveListenerAgent:
    """
    Agent C: The Reconstructive Listener & Spectral Analyst.
    Consumes corrupted audio signal, performs spectral demodulation, and recovers structured data.
    """

    def __init__(
        self,
        audio_config: Optional[AudioConfig] = None,
        input_queue: Optional[asyncio.Queue] = None,
        output_queue: Optional[asyncio.Queue] = None
    ):
        self.audio_config = audio_config or AudioConfig()
        self.input_queue = input_queue or asyncio.Queue()
        self.output_queue = output_queue or asyncio.Queue()

        self.decoder = PacketDecoder(config=self.audio_config)
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.total_processed = 0
        self.successful_reconstructions = 0
        self.latest_result: Optional[Dict[str, Any]] = None

    def reconstruct_from_audio(self, transmission: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes corrupted audio signal using DSP AnalyzeAudio tool and reconstructs JSON.
        """
        start_time = time.time()
        audio_signal = transmission.get("audio_signal")
        seq = transmission.get("seq", 0)

        # Step 1: Execute AnalyzeAudio(signal) tool
        analysis_result = AnalyzeAudio(audio_signal, config=self.audio_config)

        # Step 2: Demodulate and decode frame
        bits = analysis_result["bits"]
        decode_result = self.decoder.decode_frame(bits)

        elapsed_ms = round((time.time() - start_time) * 1000.0, 2)
        self.total_processed += 1
        if decode_result.get("success", False):
            self.successful_reconstructions += 1

        recovery_packet = {
            "seq": seq,
            "timestamp": time.time(),
            "decode_status": decode_result.get("status"),
            "success": decode_result.get("success", False),
            "confidence_pct": decode_result.get("confidence_pct", 0.0),
            "crc_status": decode_result.get("crc_status", "UNKNOWN"),
            "reconstructed_json": decode_result.get("payload"),
            "original_json": transmission.get("source_payload"),
            "glitch_metrics": transmission.get("glitch_metrics", {}),
            "dsp_metrics": {
                "snr_est_db": analysis_result.get("snr_est_db", 0.0),
                "total_bits_recovered": len(bits),
                "processing_time_ms": elapsed_ms,
                "success_rate_pct": round((self.successful_reconstructions / self.total_processed) * 100.0, 1)
            },
            "spectral_slice": {
                "freqs": analysis_result["spectrum_freqs"],
                "mag_db": analysis_result["spectrum_mag_db"]
            },
            "waveform_slice": audio_signal[:512] if len(audio_signal) >= 512 else audio_signal
        }

        self.latest_result = recovery_packet
        return recovery_packet

    async def run(self):
        """Continuous listener loop consuming corrupted audio signals."""
        self.is_running = True
        logger.info("ReconstructiveListenerAgent (Agent C) online. Listening to noise stream...")

        while self.is_running:
            try:
                # Wait for audio transmission packet from Agent B
                transmission = await self.input_queue.get()
                loop = asyncio.get_running_loop()

                # Run DSP spectral analysis and de-exorcism in thread pool
                recovery_packet = await loop.run_in_executor(None, self.reconstruct_from_audio, transmission)

                # Publish reconstructed state to output queue for Agent D
                await self.output_queue.put(recovery_packet)

                status = recovery_packet["decode_status"]
                snr = recovery_packet["dsp_metrics"]["snr_est_db"]
                logger.debug(f"[Agent C] Reconstructed seq={recovery_packet['seq']}, status={status}, SNR={snr}dB")

                self.input_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Agent C] Spectral analysis error: {e}")

        logger.info("ReconstructiveListenerAgent stopped.")

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
