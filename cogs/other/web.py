from aiohttp import web

from discord.ext import commands
import discord

from utils import BaseCog, Twitch

from typing import Any

app = web.Application()

class AiohttpWeb(BaseCog):

    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        self.twitch: Twitch = Twitch(self.bot)
        #self.app: web.Application = web.Application()

        app.router.add_post('/api/post', self.handle_post)

    async def handle_post(self, request):
        data = await request.json()

        print(0, data)

        await self.twitch.twitch_to_discord(data)
        
        return web.json_response({"message": "data received by aiohttp: {}".format(data)})

if __name__ == '__main__':
    web.run_app(app, port=8081)