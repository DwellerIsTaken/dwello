from __future__ import annotations

from core import BaseCog, Dwello

# later maybe?
class BotConfig(BaseCog):
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot
