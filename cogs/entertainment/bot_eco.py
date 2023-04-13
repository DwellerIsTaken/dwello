from __future__ import annotations

from discord.ext import commands

from typing import Any
from utils import BotEcoUtils, BaseCog

class Bot_Economy(BaseCog):

    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        self.be = BotEcoUtils(self.bot)

    @commands.hybrid_command(name = "work", description = "A boring job with a basic income. Gives some of the bot's currency in return.")
    async def work_bot(self, ctx):

        return await self.be.work(ctx, "bot")