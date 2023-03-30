from discord.ext import commands

from .bot_eco import Bot_Economy
from .guild_eco import Guild_Economy

class Entertainment(Bot_Economy, Guild_Economy):
    '''def __init__(self, bot):
        super().__init__(bot=bot)'''

async def setup(bot: commands.Bot):
    await bot.add_cog(Entertainment(bot))