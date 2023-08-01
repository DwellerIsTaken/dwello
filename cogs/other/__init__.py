from __future__ import annotations

from typing import TYPE_CHECKING

from discord import Message

from .botconfig import BotConfig
from .events import Events
from .tasks import Tasks
from .todo import Todo

if TYPE_CHECKING:
    from core import Dwello


class Other(Events, Tasks, BotConfig, Todo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_cache: dict[int, Message] = {}

    """Other Class"""


async def setup(bot: Dwello):
    await bot.add_cog(Other(bot))
