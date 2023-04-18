from __future__ import annotations

from discord.ext import commands, tasks
from datetime import datetime
from pytz import timezone
import discord, asyncio

import text_variables as tv

from typing import Any
from utils import BaseCog, exe_sql

class Tasks(BaseCog):

    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        self.stats_loop.start()
        self.eco_loop.start()

    @tasks.loop(minutes = 10)
    async def stats_loop(self):

        for guild in self.bot.guilds:
            await exe_sql(self.bot, guild)

    @stats_loop.before_loop
    async def before_stats(self):
        await asyncio.sleep(10)
        await self.bot.wait_until_ready()

    @tasks.loop(seconds = 1)
    async def eco_loop(self):
        cet = timezone("Europe/Amsterdam")
        now = datetime.now(cet)

        if now.hour == 10 and now.minute == 0 and now.second == 0:
            async with self.bot.pool.acquire() as conn:
                async with conn.transaction(): 
                    await conn.execute("UPDATE users SET worked = 0")

    @eco_loop.before_loop
    async def before_curr(self):
        await self.bot.wait_until_ready()