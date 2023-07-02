from __future__ import annotations

from typing import TYPE_CHECKING

from .botconfig import BotConfig
from .events import Events
from .tasks import Tasks

if TYPE_CHECKING:
    from core import Dwello


class Other(Events, Tasks, BotConfig):
    """Other Class"""


async def setup(bot: Dwello):
    await bot.add_cog(Other(bot))
