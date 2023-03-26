from discord.ext import commands
#from features.levelling.utils import levelling
from features.economy.utils.common_attributes import *

class Economy_commands_bot(commands.Cog, name = "Economy_commands_bot"):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name = "work", description = "A boring job with a basic income. Gives some of the bot's currency in return.")
    async def work_bot(self, ctx):
        await work(ctx, "bot")
    
async def setup(bot):
  await bot.add_cog(Economy_commands_bot(bot))