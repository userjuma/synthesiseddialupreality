"""
Multi-Stage Pipeline Orchestrator for Synthesised Dial-Up Reality.
Coordinates concurrent execution of:
- Agent A (Live Ingest) -> input_data stream
- Agent B (Acoustic Modulator & Glitch Engine) -> audio_transmission stream
- Agent C (Reconstructive Listener & AnalyzeAudio DSP) -> decoded_data stream
- Agent D (Esoteric TUI Visualizer & 3D Engine)
"""

import asyncio
import logging
import signal
import sys
import time
from typing import Optional

from rich.live import Live

from src.config import PipelineConfig
from src.ingest.ingest_agent import LiveIngestAgent
from src.modulator.modulator_agent import AcousticModulatorAgent
from src.listener.listener_agent import ReconstructiveListenerAgent
from src.visualizer.tui_app import DialUpTUIApp
from src.audio_output import AudioOutputPlayer

logger = logging.getLogger("PipelineOrchestrator")


class DialUpRealityPipeline:
    """
    End-to-end multi-agent pipeline orchestrating real-time data degradation and DSP reconstruction.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()

        # Inter-agent async streaming queues
        self.input_data_queue = asyncio.Queue()
        self.audio_transmission_queue = asyncio.Queue()
        self.decoded_data_queue = asyncio.Queue()

        # Agents
        self.agent_a = LiveIngestAgent(
            config=self.config.ingest,
            output_queue=self.input_data_queue
        )
        self.agent_b = AcousticModulatorAgent(
            audio_config=self.config.audio,
            glitch_profile=self.config.glitch,
            input_queue=self.input_data_queue,
            output_queue=self.audio_transmission_queue
        )
        self.agent_c = ReconstructiveListenerAgent(
            audio_config=self.config.audio,
            input_queue=self.audio_transmission_queue,
            output_queue=self.decoded_data_queue
        )

        # Agent D (TUI Visualizer)
        self.tui = DialUpTUIApp(
            feed_name=self.config.ingest.feed_type,
            glitch_name=self.config.glitch.name
        )

        # Audio Output
        self.audio_player = AudioOutputPlayer(
            sample_rate=self.config.audio.sample_rate,
            enabled=self.config.enable_audio_device
        )

        self.is_running = False

    async def _queue_consumer_loop(self):
        """Dispatches decoded states to TUI and audio player."""
        while self.is_running:
            try:
                recovery_packet = await self.decoded_data_queue.get()
                self.tui.update_state(recovery_packet)

                # Stream audio to physical speaker if enabled
                if self.config.enable_audio_device and self.agent_b.latest_transmission:
                    audio_sig = self.agent_b.latest_transmission.get("audio_signal")
                    if audio_sig is not None:
                        self.audio_player.play_signal(audio_sig)

                self.decoded_data_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consumer loop error: {e}")

    async def run(self):
        """Starts all agents and drives the TUI rendering loop."""
        self.is_running = True
        logger.info("Initializing Synthesised Dial-Up Reality pipeline...")

        # Start Agent tasks
        task_a = self.agent_a.start()
        task_b = self.agent_b.start()
        task_c = self.agent_c.start()
        task_consumer = asyncio.create_task(self._queue_consumer_loop())

        frame_interval = 1.0 / max(10.0, self.config.tui_refresh_rate_hz)

        try:
            with Live(self.tui.render_layout(), refresh_per_second=int(self.config.tui_refresh_rate_hz), screen=True) as live:
                while self.is_running:
                    live.update(self.tui.render_layout())
                    await asyncio.sleep(frame_interval)
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        finally:
            await self.stop()

    async def stop(self):
        """Gracefully shuts down all pipeline agents and hardware audio."""
        self.is_running = False
        await self.agent_a.stop()
        await self.agent_b.stop()
        await self.agent_c.stop()
        self.audio_player.stop()
        logger.info("Synthesised Dial-Up Reality pipeline cleanly terminated.")
