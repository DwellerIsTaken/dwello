from __future__ import annotations

from typing import TYPE_CHECKING

import asyncpg
import discord
from typing_extensions import Self

if TYPE_CHECKING:
    from bot import Dwello

else:
    from discord.ext.commands import Bot as Dwello


class OtherUtils:
    def __init__(self: Self, bot: Dwello) -> None:
        self.bot = bot

    async def exe_sql(self: Self, guild: discord.Guild) -> None:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                channels = await conn.fetch(
                    "SELECT channel_id, counter_name FROM server_data WHERE guild_id = $1 AND channel_id IS NOT NULL AND event_type = 'counter' AND counter_name != 'category'",
                    guild.id,
                )

                bot_counter_ = sum(member.bot for member in guild.members)
                member_counter_ = guild.member_count - bot_counter_

                counters = ["all", "member", "bot"]

                for row in channels:
                    channel_id, event_type = int(row["channel_id"]), str(row["counter_name"])

                    if event_type in counters:
                        channel: discord.VoiceChannel = self.bot.get_channel(channel_id)

                        try:  # suppress?
                            if event_type == counters[0]:
                                name = f"📊 All counter: {guild.member_count}"
                            elif event_type == counters[1]:
                                name = f"📊 Member counter: {member_counter_}"
                            elif event_type == counters[2]:
                                name = f"📊 Bot counter: {bot_counter_}"
                            if name and channel:
                                await channel.edit(name=name)

                        except Exception as e:  # handle type error
                            print(e, "exe_sql (utils/other.py)")
