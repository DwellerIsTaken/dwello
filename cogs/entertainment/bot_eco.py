from discord.ext import commands

from utils.economy import BotEcoUtils

class Bot_Economy():

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name = "work", description = "A boring job with a basic income. Gives some of the bot's currency in return.")
    async def work_bot(self, ctx):

        return await BotEcoUtils.work(ctx, "bot")