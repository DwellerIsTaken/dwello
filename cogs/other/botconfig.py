from __future__ import annotations

from core import BaseCog, Dwello, DwelloContext  # noqa: F401


class BotConfig(BaseCog):
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot
