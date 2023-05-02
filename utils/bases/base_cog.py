from __future__ import annotations

from discord.ext import commands
from typing import Any
from bot import Dwello

class BaseCog(commands.Cog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        self.bot: Dwello = bot
        super().__init__(*args, **kwargs)