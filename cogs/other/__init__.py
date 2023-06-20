from __future__ import annotations
#from typing import TYPE_CHECKING

from bot import Dwello

from .owner import Owner
from .events import Events
from .tasks import Tasks
from .botconfig import BotConfig

class Other(Owner, Events, Tasks, BotConfig):
    '''Other Class'''

async def setup(bot: Dwello):
    await bot.add_cog(Other(bot))
