from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Any

from discord.ext import tasks
from pytz import timezone

from core import BaseCog, Dwello

if TYPE_CHECKING:
    from discord import Guild, VoiceChannel


class Tasks(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self.stats_loop.start()
        self.eco_loop.start()  # maybe start it in bot_base.py instead

    @tasks.loop(minutes=10)
    async def stats_loop(self) -> None:
        for guild in self.bot.guilds:
            await update_counters(self.bot, guild)  # in case join/leave won't work because of rate limitations

    @tasks.loop(seconds=1) # better way?
    async def eco_loop(self) -> None:
        cet = timezone("Europe/London")
        now = datetime.now(cet)

        if now.hour == 10 and now.minute == 0 and now.second == 0:
            async with self.bot.safe_connection() as conn:
                await conn.execute("UPDATE users SET worked = 0")

    @stats_loop.before_loop
    async def before_stats(self):
        await asyncio.sleep(10)
        await self.bot.wait_until_ready()

    @eco_loop.before_loop
    async def before_curr(self):
        await self.bot.wait_until_ready()

# maybe make a counter class and add this there
async def update_counters(bot: Dwello, guild: Guild) -> None:
    async with bot.safe_connection() as conn:
        query: str = """
            SELECT channel_id, counter_name FROM server_data WHERE guild_id = $1 AND channel_id IS NOT NULL
            AND event_type = 'counter' AND counter_name != 'category'
            """
        channels = await conn.fetch(
            query,
            guild.id,
        )

    bot_counter_ = sum(member.bot for member in guild.members)
    member_counter_ = len(guild.members) - bot_counter_  # type: ignore

    counters = ["all", "member", "bot"]

    for row in channels:
        channel_id, event_type = int(row["channel_id"]), str(row["counter_name"])

        if event_type in counters:
            channel: VoiceChannel = bot.get_channel(channel_id)  # type: ignore
            try:
                name = None
                if event_type == counters[0]:
                    name = f"\N{BAR CHART} All counter: {guild.member_count}"
                elif event_type == counters[1]:
                    name = f"\N{BAR CHART} Member counter: {member_counter_}"
                elif event_type == counters[2]:
                    name = f"\N{BAR CHART} Bot counter: {bot_counter_}"
                if name and channel:
                    await channel.edit(name=name)
                    
            except Exception as e:  # handle type error
                print(e, "exe_sql (utils/other.py)")
