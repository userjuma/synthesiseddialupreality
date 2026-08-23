import asyncio
import logging
from typing import Optional

from rich.live import Live

from src.audio_output import AudioOutputPlayer
from src.config import PipelineConfig
from src.ingest.ingest_agent import LiveIngestAgent
from src.listener.listener_agent import ReconstructiveListenerAgent
from src.modulator.modulator_agent import AcousticModulatorAgent
from src.visualizer.tui_app import DialUpTUIApp

log = logging.getLogger("Pipeline")


class DialUpRealityPipeline:
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.cfg = config or PipelineConfig()

        self.q_input = asyncio.Queue()
        self.q_audio = asyncio.Queue()
        self.q_decoded = asyncio.Queue()

        self.agent_a = LiveIngestAgent(config=self.cfg.ingest, output_queue=self.q_input)
        self.agent_b = AcousticModulatorAgent(
            audio_config=self.cfg.audio,
            glitch_profile=self.cfg.glitch,
            input_queue=self.q_input,
            output_queue=self.q_audio,
        )
        self.agent_c = ReconstructiveListenerAgent(
            audio_config=self.cfg.audio,
            input_queue=self.q_audio,
            output_queue=self.q_decoded,
        )
        self.tui = DialUpTUIApp(
            feed_name=self.cfg.ingest.feed_type,
            glitch_name=self.cfg.glitch.name,
        )
        self.player = AudioOutputPlayer(
            sample_rate=self.cfg.audio.sample_rate,
            enabled=self.cfg.enable_audio_device,
        )
        self.running = False

    async def _dispatch(self):
        while self.running:
            try:
                rec = await self.q_decoded.get()
                self.tui.update_state(rec)

                if self.cfg.enable_audio_device and self.agent_b.latest_transmission:
                    sig = self.agent_b.latest_transmission.get("audio_signal")
                    if sig is not None:
                        self.player.play_signal(sig)

                self.q_decoded.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.warning(f"Dispatch error: {e}")

    async def run(self):
        self.running = True
        self.agent_a.start()
        self.agent_b.start()
        self.agent_c.start()
        disp_task = asyncio.create_task(self._dispatch())

        dt = 1.0 / max(10.0, self.cfg.tui_refresh_rate_hz)
        try:
            with Live(self.tui.render_layout(), refresh_per_second=int(self.cfg.tui_refresh_rate_hz), screen=True) as live:
                while self.running:
                    live.update(self.tui.render_layout())
                    await asyncio.sleep(dt)
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        finally:
            await self.stop()

    async def stop(self):
        self.running = False
        await self.agent_a.stop()
        await self.agent_b.stop()
        await self.agent_c.stop()
        self.player.stop()
