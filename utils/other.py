from __future__ import annotations

from discord.ext import commands
import discord

async def exe_sql(bot, guild: discord.Guild) -> None:
    async with bot.pool.acquire() as conn:
        async with conn.transaction(): 

            channels = await conn.fetch("SELECT channel_id, counter_name FROM server_data WHERE guild_id = $1 AND channel_id IS NOT NULL AND event_type = 'counter' AND counter_name != 'category'", guild.id)

            bot_counter_ = sum(member.bot for member in guild.members)
            member_counter_ = guild.member_count - bot_counter_

            counters = ["all", "member", "bot"]

            for row in channels:
                channel_id, event_type = int(row["channel_id"]), str(row["counter_name"])

                if event_type in counters:
                    try:
                        channel = guild.get_channel(channel_id)
                        if event_type == counters[0]:
                            name = f"📊 All counter: {guild.member_count}"
                        if event_type == counters[1]:
                            name = f"📊 Member counter: {member_counter_}"
                        if event_type == counters[2]:
                            name = f"📊 Bot counter: {bot_counter_}"
                        await channel.edit(name=name)

                    except Exception as e:
                        print(e)