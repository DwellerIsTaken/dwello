from __future__ import annotations

from typing import TYPE_CHECKING

from ._global import GlobalEconomy

if TYPE_CHECKING:
    from core import Dwello


class Economy(GlobalEconomy, name="Economy"):
    """
    💸
    Includes economy commands for both bot- and guild-side.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.select_emoji = "💸"
        self.select_brief = "Commands for managing an economy system."


async def setup(bot: Dwello) -> None:
    await bot.add_cog(Economy(bot))


# REDO ECO
# MAKE GLOBAL ECO
# MORE ADVANCED
# MORE ADVANCED SQL TOO
