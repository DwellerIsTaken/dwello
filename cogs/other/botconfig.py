from __future__ import annotations

from typing import Any

from typing_extensions import Self

from bot import Dwello
from utils import BaseCog


class BotConfig(BaseCog):
    def __init__(self: Self, bot: Dwello, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        # self.prefixc: PrefixCommands = PrefixCommands(self.bot)
