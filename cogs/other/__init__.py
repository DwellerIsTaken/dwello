from __future__ import annotations

from core import Bot

from .botconfig import BotConfig
from .events import Events
from .owner import Owner
from .tasks import Tasks

# from typing import TYPE_CHECKING


class Other(Owner, Events, Tasks, BotConfig):
    """Other Class"""


async def setup(bot: Bot):
    await bot.add_cog(Other(bot))
