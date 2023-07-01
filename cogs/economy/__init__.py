from __future__ import annotations

from typing import TYPE_CHECKING

from .bot_eco import Bot_Economy
from .guild_eco import Guild_Economy

if TYPE_CHECKING:
    from core import Dwello


class Economy(Bot_Economy, Guild_Economy, name="Economy"):
    """
    💸
    Includes economy commands for both bot- and guild-side.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.select_emoji = "💸"
        self.select_brief = "Commands for managing an economy system."


async def setup(bot: Dwello):
    await bot.add_cog(Economy(bot))


# REDO ECO
# MAKE GLOBAL ECO
# MORE ADVANCED
# MORE ADVANCED SQL TOO
