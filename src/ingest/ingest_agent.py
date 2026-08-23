"""
Agent A: The Live Ingest Agent.
Continuously fetches real-time structured JSON feeds and publishes to input_data stream.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional

from src.config import IngestConfig
from src.ingest.live_feed import FeedProvider, get_feed_provider

logger = logging.getLogger("LiveIngestAgent")


class LiveIngestAgent:
    """
    Agent A: The Live Ingest Agent.
    Fetches real-time JSON payloads every poll_interval_sec and publishes them to the queue.
    """

    def __init__(self, config: Optional[IngestConfig] = None, output_queue: Optional[asyncio.Queue] = None):
        self.config = config or IngestConfig()
        self.output_queue = output_queue or asyncio.Queue()
        self.provider: FeedProvider = get_feed_provider(
            self.config.feed_type,
            timeout=self.config.request_timeout_sec
        )
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.latest_payload: Optional[Dict[str, Any]] = None
        self.total_ingested = 0

    def fetch_once(self) -> Dict[str, Any]:
        """Synchronously pull a single fresh payload from the provider."""
        payload = self.provider.fetch_payload()
        self.latest_payload = payload
        self.total_ingested += 1
        return payload

    async def run(self):
        """Continuous async ingest loop pulling payloads at configured interval."""
        self.is_running = True
        logger.info(f"LiveIngestAgent started. Feed: {self.config.feed_type}, Interval: {self.config.poll_interval_sec}s")

        while self.is_running:
            start_time = time.time()
            try:
                # Run the blocking fetch in a thread pool to avoid stalling the async event loop
                loop = asyncio.get_running_loop()
                payload = await loop.run_in_executor(None, self.provider.fetch_payload)
                self.latest_payload = payload
                self.total_ingested += 1

                # Put onto the output queue
                await self.output_queue.put(payload)
                logger.debug(f"[Agent A] Ingested seq={payload.get('seq')}, source={payload.get('source')}")

            except Exception as e:
                logger.error(f"[Agent A] Ingest error: {e}")

            # Sleep remaining time to maintain steady poll interval
            elapsed = time.time() - start_time
            sleep_duration = max(0.1, self.config.poll_interval_sec - elapsed)
            try:
                await asyncio.sleep(sleep_duration)
            except asyncio.CancelledError:
                break

        logger.info("LiveIngestAgent stopped.")

    def start(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> asyncio.Task:
        """Start agent in async task."""
        self.is_running = True
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run())
        return self._task

    async def stop(self):
        """Stop ingest loop cleanly."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
