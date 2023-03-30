import discord
from discord.ext import commands

from typing import Optional

class Bot(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #MAKE 
    @commands.hybrid_command(name = 'source', description="Shows bot's source", with_app_command=True) 
    async def stats(self, ctx: commands.Context) -> Optional[discord.Message]:
        async with ctx.typing():
            return await ctx.reply("https://github.com/DwellerIsTaken/discordbot/")