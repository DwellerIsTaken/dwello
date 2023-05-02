from __future__ import annotations

import discord
from discord.ext import commands

from bot import Dwello
from typing import Optional, Any
from utils import BaseCog, DwelloContext

class BotConfig(BaseCog):

    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)

    #ABOUT CLASS help.py
    @commands.hybrid_command(name = 'source', description="Shows bot's source", with_app_command=True) 
    async def source(self, ctx: DwelloContext) -> Optional[discord.Message]:
        async with ctx.typing():
            return await ctx.reply("https://github.com/DwellerIsTaken/discordbot/")