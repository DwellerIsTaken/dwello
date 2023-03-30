from __future__ import annotations
#from typing import TYPE_CHECKING

from discord.ext import commands

from .events import Events
from .loops import Loops
from .bot import Bot

class Other(Events, Loops, Bot):
    '''Other Class'''

async def setup(bot: commands.Bot):
    await bot.add_cog(Other(bot))
