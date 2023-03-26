from __future__ import annotations
#from typing import TYPE_CHECKING

from discord.ext import commands

from .standard import StandardModeration
from .timeout import Timeout
from .warnings import Warnings

class Moderation(StandardModeration, Timeout, Warnings):
    pass

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
