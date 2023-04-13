from __future__ import annotations

from discord.ext import commands
from typing import Any

class BaseCog(commands.Cog):
    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any) -> None:
        self.bot: commands.Bot = bot
        super().__init__(*args, **kwargs)