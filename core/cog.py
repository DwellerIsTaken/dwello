from __future__ import annotations

from typing import TYPE_CHECKING, Any
from discord.ext import commands

if TYPE_CHECKING:
    from core import Dwello

class BaseCog(commands.Cog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        self.bot: Dwello = bot
        super().__init__(*args, **kwargs)
        
        self.ON_TESTING = False # ?
