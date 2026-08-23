import asyncio
import logging
import time
from typing import Any, Dict, Optional

from src.config import IngestConfig
from src.ingest.live_feed import get_feed_provider

log = logging.getLogger("LiveIngest")


class LiveIngestAgent:
    def __init__(self, config: Optional[IngestConfig] = None, output_queue: Optional[asyncio.Queue] = None):
        self.config = config or IngestConfig()
        self.output_queue = output_queue or asyncio.Queue()
        self.provider = get_feed_provider(self.config.feed_type, timeout=self.config.request_timeout_sec)
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.latest_payload: Optional[Dict[str, Any]] = None
        self.total_ingested = 0

    def fetch_once(self) -> Dict[str, Any]:
        payload = self.provider.fetch()
        self.latest_payload = payload
        self.total_ingested += 1
        return payload

    async def run(self):
        self.running = True
        log.info(f"Ingest started [{self.config.feed_type}] @ {self.config.poll_interval_sec}s")

        while self.running:
            t0 = time.time()
            try:
                loop = asyncio.get_running_loop()
                payload = await loop.run_in_executor(None, self.provider.fetch)
                self.latest_payload = payload
                self.total_ingested += 1
                await self.output_queue.put(payload)
            except Exception as e:
                log.warning(f"Ingest poll failed: {e}")

            elapsed = time.time() - t0
            sleep_time = max(0.1, self.config.poll_interval_sec - elapsed)
            try:
                await asyncio.sleep(sleep_time)
            except asyncio.CancelledError:
                break

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
