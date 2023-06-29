from __future__ import annotations

from core import Bot

from .bot_eco import Bot_Economy
from .guild_eco import Guild_Economy


class Economy(Bot_Economy, Guild_Economy, name="Economy"):
    """
    💸 Includes economy commands for both bot- and guild-side.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.select_emoji = "💸"
        self.select_brief = "Commands for managing an economy system."


async def setup(bot: Bot):
    await bot.add_cog(Economy(bot))
