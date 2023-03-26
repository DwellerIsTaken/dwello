from discord.ext import commands, tasks
import discord, asyncpg, asyncio, os
import text_variables as tv

from datetime import datetime
from pytz import timezone

class Loops(commands.Cog):

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.stats_loop.start()
        self.eco_loop.start()

    async def exe_sql(self, guild: discord.Guild) -> None:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction(): 

                channels = await conn.fetch("SELECT channel_id, event_type FROM main WHERE guild_id = $1 AND channel_id NOT NULL AND event_type NOT NULL AND event_type NOT counter_category", guild.id)

                bot_counter_ = sum(member.bot for member in guild.members)
                member_counter_ = guild.member_count - bot_counter_

                counters = ["all_counter", "member_counter", "bot_counter"]

                for row in channels:
                    channel_id, event_type = int(row["channel_id"]), str(row["event_type"])

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

    @tasks.loop(minutes = 10)
    async def stats_loop(self):

        for guild in self.bot.guilds:
            await self.exe_sql(guild)

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

async def setup(bot: commands.Bot): # MAKE IT A SUBCOG -> IMPORT IN UTILS (?)
    await bot.add_cog(Loops(bot))