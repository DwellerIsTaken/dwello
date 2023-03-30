from __future__ import annotations

from discord.ext import commands

from .weather import Weather
from .user_info import UserInfo

class Information(UserInfo, Weather):
    '''Information Class'''

async def setup(bot: commands.Bot):
    await bot.add_cog(Information(bot))
