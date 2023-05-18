from __future__ import annotations

from aiohttp import web

from typing import TYPE_CHECKING
from typing_extensions import Self

if TYPE_CHECKING:
    from bot import Dwello 
    
else:
    from discord.ext.commands import Bot as Dwello

class AiohttpWeb:

    def __init__(self: Self, bot: Dwello):
        self.bot = bot
        self.app: web.Application = web.Application()
        self.app.router.add_post('/api/post', self.handle_post)

    async def handle_post(self: Self, request):
        print(request)
        data = await request.json()
        print(data)

        await self.bot.twitch.twitch_to_discord(data)
        return web.json_response({"message": "data received by aiohttp: {}".format(data)})

    async def run(self: Self, port: int = 8081):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", port)

        try:
            await self.bot.loop.create_task(site.start())
            self.bot.logger.info(f"Web server running on http://localhost:{port}")
            
        except Exception as e:
            print(f"Failed to start web server: {e}")