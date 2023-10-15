from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bot import Dwello

from aiohttp import web

#from utils import ENV, DataBaseOperations, Twitch  # noqa: F401, E402

# REDO


class AiohttpWeb:
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot
        self.app: web.Application = web.Application()
        self.app.router.add_post("/api/post", self.handle_post)

    async def handle_post(self, request):
        print(request)
        data = await request.json()
        print(data)

        await self.bot.twitch.twitch_to_discord(data)
        return web.json_response({"message": f"data received by aiohttp: {data}"})

    async def run(self, port: int = 8081):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", port)

        try:
            await self.bot.loop.create_task(site.start())

        except Exception as e:
            print(f"Failed to start web server: {e}")


