from __future__ import annotations

from discord.ext import commands, tasks
from datetime import datetime
from pytz import timezone
import asyncpg, asyncio

import text_variables as tv

from bot import Dwello
from typing import Any
from utils import BaseCog

class Tasks(BaseCog):

    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        self.stats_loop.start()
        self.eco_loop.start() # maybe start it in bot_base.py instead

    @tasks.loop(minutes = 10)
    async def stats_loop(self):

        for guild in self.bot.guilds:
            await self.bot.otherutils.exe_sql(guild) # in case join/leave won't work because of rate limitations

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
                conn: asyncpg.Connection
                async with conn.transaction():
                    await conn.execute("UPDATE users SET worked = 0")

    @eco_loop.before_loop
    async def before_curr(self):
        await self.bot.wait_until_ready()