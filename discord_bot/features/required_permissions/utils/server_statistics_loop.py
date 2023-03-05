from discord.ext import commands, tasks
import discord, asqlite, asyncio
import text_variables as tv

class StatsLoop(commands.Cog, name = "StatsLoop"):

    def __init__(self, bot):
        self.bot = bot
        self.stats_loop.start()
        super().__init__()

    async def exe_sql(self, guild) -> bool:
        async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:

                bot_counter = 0
                for member in guild.members:

                    if member.bot:
                        bot_counter += 1

                member_counter = int(member.guild.member_count) - int(bot_counter)

                await cursor.execute(f"SELECT channel_id FROM main WHERE guild_id = {guild.id}")
                all_counter = await cursor.fetchone()

                await cursor.execute(f"SELECT channel_id FROM main WHERE guild_id = {guild.id}")
                members_counter = await cursor.fetchone()

                await cursor.execute(f"SELECT channel_id FROM main WHERE guild_id = {guild.id}")
                bots_counter = await cursor.fetchone()

                try:

                    if all_counter[0] is None:
                        pass

                    else:
                        channel_ = discord.utils.get(guild.channels, id=int(all_counter[0]))
                        await channel_.edit(name=f"📊 All counter: {guild.member_count}")

                except:
                    pass

                try:

                    if members_counter[0] is None:
                        pass

                    else:
                        channel_ = discord.utils.get(guild.channels, id=int(members_counter[0]))
                        await channel_.edit(name=f"📊 Member counter: {member_counter}")

                except:
                    pass

                try:

                    if bots_counter[0] is None:
                        pass

                    else:
                        channel_ = discord.utils.get(guild.channels, id=int(bots_counter[0]))
                        await channel_.edit(name=f"📊 Bots counter: {bot_counter}")

                except:
                    pass

        return True

    @tasks.loop(minutes = 10)
    async def stats_loop(self):

        for guild in self.bot.guilds:
            await self.exe_sql(guild)

    @stats_loop.before_loop
    async def before_stats(self):
        await asyncio.sleep(10)
        await self.bot.wait_until_ready()

async def setup(bot):
  await bot.add_cog(StatsLoop(bot))