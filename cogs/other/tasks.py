from __future__ import annotations

import asyncio
from datetime import datetime

import asyncpg
from discord.ext import tasks
from pytz import timezone
from typing_extensions import Self

from core import BaseCog, Dwello

class Tasks(BaseCog):
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot
        self.stats_loop.start()
        self.eco_loop.start()  # maybe start it in bot_base.py instead

    @tasks.loop(minutes=10)
    async def stats_loop(self: Self) -> None:
        for guild in self.bot.guilds:
            await self.bot.otherutils.exe_sql(guild)  # in case join/leave won't work because of rate limitations

    @tasks.loop(seconds=1)
    async def eco_loop(self: Self) -> None:
        cet = timezone("Europe/Amsterdam")
        now = datetime.now(cet)

        if now.hour == 10 and now.minute == 0 and now.second == 0:
            async with self.bot.pool.acquire() as conn:
                conn: asyncpg.Connection
                async with conn.transaction():
                    await conn.execute("UPDATE users SET worked = 0")

    @stats_loop.before_loop
    async def before_stats(self: Self):
        await asyncio.sleep(10)
        await self.bot.wait_until_ready()

    @eco_loop.before_loop
    async def before_curr(self: Self):
        await self.bot.wait_until_ready()
