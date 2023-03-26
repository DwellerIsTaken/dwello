from discord.ext import commands, tasks
from datetime import datetime
import text_variables as tv
import discord, re, asqlite
from pytz import timezone

class EcoLoop(commands.Cog, name = "EcoLoop"):

    def __init__(self, bot):
        self.bot = bot
        self.curr_loop.start()
        super().__init__()

    '''date = str(datetime.now())
    date = re.split('-| ', date)

    my_datetime = datetime(int(date[0]), int(date[1]), int(date[2]), 10, 00, tzinfo = None) # UTC tzinfo = pytz.utc 9, 00
    #my_datetime_cet = my_datetime.astimezone(pytz.timezone('Europe/Amsterdam')).strftime('%Y-%m-%d %H:%M:%S %Z%z') #CET

    my_datetime = str(my_datetime).split(' ')
    time = str(my_datetime[-1])

    @tasks.loop(seconds = 1)
    async def curr_loop(self):

        disc_time = str(discord.utils.utcnow())
        disc_time = re.split(' ', disc_time)
        disc_time = str(disc_time[-1]).split('.')
        disc_time = str(disc_time[0])

        if self.time in disc_time:
            async with asqlite.connect(tv.sql_dir) as connector:
                async with connector.cursor() as cursor:
                    await cursor.execute("UPDATE users SET worked = ?", (int(False)))
                await connector.commit()'''
    
    @tasks.loop(seconds = 1)
    async def curr_loop(self):
        cet = timezone("Europe/Amsterdam")
        now = datetime.now(cet)
        if now.hour == 10 and now.minute == 0 and now.second == 0:
            async with asqlite.connect(tv.sql_dir) as connector:
                async with connector.cursor() as cursor:
                    await cursor.execute("UPDATE users SET worked = 0")
                await connector.commit()

    @curr_loop.before_loop
    async def before_curr(self):
        await self.bot.wait_until_ready()

async def setup(bot):
  await bot.add_cog(EcoLoop(bot))