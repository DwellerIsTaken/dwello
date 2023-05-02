from __future__ import annotations
#from typing import TYPE_CHECKING

from bot import Dwello

from .events import Events
from .tasks import Tasks
from .botconfig import BotConfig
from .owner import OwnerCommands

class Other(Events, Tasks, OwnerCommands, BotConfig):
    '''Other Class'''

async def setup(bot: Dwello):
    await bot.add_cog(Other(bot))
