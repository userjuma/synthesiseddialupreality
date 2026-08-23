import asyncio
import json
import logging
import os
from typing import Set
from aiohttp import web

log = logging.getLogger("WebServer")


class WebDashboardServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.clients: Set[web.WebSocketResponse] = set()
        self.runner: web.AppRunner = None
        self.site: web.TCPSite = None

        self._setup_routes()

    def _setup_routes(self):
        static_dir = os.path.join(os.path.dirname(__file__), "web")
        self.app.router.add_get("/ws", self._ws_handler)
        self.app.router.add_static("/", path=static_dir, show_index=True)

    async def _ws_handler(self, req: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(req)
        self.clients.add(ws)
        log.info(f"WebSocket client connected. Total: {len(self.clients)}")

        try:
            async for msg in ws:
                pass
        finally:
            self.clients.discard(ws)
            log.info(f"WebSocket client disconnected. Total: {len(self.clients)}")

        return ws

    async def broadcast(self, data: dict):
        if not self.clients:
            return

        # Convert numpy arrays to lists for JSON serialization
        payload = {}
        for k, v in data.items():
            if hasattr(v, "tolist"):
                payload[k] = v.tolist()
            elif isinstance(v, dict):
                payload[k] = {
                    sub_k: (sub_v.tolist() if hasattr(sub_v, "tolist") else sub_v)
                    for sub_k, sub_v in v.items()
                }
            else:
                payload[k] = v

        msg_str = json.dumps(payload)
        dead = []
        for ws in self.clients:
            try:
                await ws.send_str(msg_str)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.clients.discard(ws)

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        log.info(f"Web Dashboard online at http://localhost:{self.port}")

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()
