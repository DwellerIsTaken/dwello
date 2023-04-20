from __future__ import annotations
#from typing import TYPE_CHECKING

from discord.ext import commands

from .events import Events
from .tasks import Tasks
from .botconfig import BotConfig

class Other(Events, Tasks, BotConfig):
    '''Other Class'''

async def setup(bot: commands.Bot):
    await bot.add_cog(Other(bot))
