from __future__ import annotations

from typing import Any

from core import BaseCog, Dwello


# later maybe?
class BotConfig(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
