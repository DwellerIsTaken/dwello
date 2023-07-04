from __future__ import annotations

from typing import TYPE_CHECKING

from .botconfig import BotConfig
from .events import Events
from .tasks import Tasks
from .todo import Todo

if TYPE_CHECKING:
    from core import Dwello


class Other(Events, Tasks, BotConfig, Todo):
    """Other Class"""


async def setup(bot: Dwello):
    await bot.add_cog(Other(bot))
