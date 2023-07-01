from __future__ import annotations

from typing import TYPE_CHECKING

from .botconfig import BotConfig
from .events import Events
from .owner import Owner
from .tasks import Tasks

if TYPE_CHECKING:
    from core import Dwello


class Other(Owner, Events, Tasks, BotConfig):
    """Other Class"""


async def setup(bot: Dwello):
    await bot.add_cog(Other(bot))
