from __future__ import annotations

from discord.ext import commands

from .config import Config
from .manage_channels import Channels
from .manage_messages import Messages

class Guild(Config, Channels, Messages):
    pass

async def setup(bot: commands.Bot):
    await bot.add_cog(Guild(bot))
