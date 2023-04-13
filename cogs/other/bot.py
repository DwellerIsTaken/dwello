from __future__ import annotations

import discord
from discord.ext import commands

from typing import Optional, Any
from utils import BaseCog

class BotConfig(BaseCog):

    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)

    #MAKE 
    @commands.hybrid_command(name = 'source', description="Shows bot's source", with_app_command=True) 
    async def source(self, ctx: commands.Context) -> Optional[discord.Message]:
        async with ctx.typing():
            return await ctx.reply("https://github.com/DwellerIsTaken/discordbot/")