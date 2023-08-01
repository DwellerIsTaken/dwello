from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from .automod import AutoMod
from .standard import StandardModeration
from .timeout import Timeout
from .warnings import Warnings

if TYPE_CHECKING:
    from core import Dwello


class Moderation(
    AutoMod,
    StandardModeration,
    Timeout,
    Warnings,
    name="Moderation",
):
    """
    🛡️
    Tools for server moderation, as well as various utilities designed specifically for administrators and moderators.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.select_emoji = "🛡️"
        self.select_brief = "Various moderation tools."

    async def cog_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True


async def setup(bot: Dwello) -> None:
    await bot.add_cog(Moderation(bot))
