from __future__ import annotations

from typing import Optional

import asyncpg
import discord
from discord.ext import commands

import constants as cs
from core import BaseCog, Dwello, DwelloContext

from .shared import SharedEcoUtils


class BotEcoUtils:
    def __init__(self, bot: Dwello):
        self.bot = bot

    async def balance_check(self, ctx: DwelloContext, amount: int, name: str) -> Optional[bool]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                row = await conn.fetchrow(
                    "SELECT money FROM users WHERE user_id = $1 AND guild_id = $2 AND event_type = $3",
                    ctx.author.id,
                    not None if name == "bot" else ctx.guild.id,
                    name,
                )

                money = int(row[0]) if row else None

                if money < amount:
                    return await ctx.reply(
                        embed=discord.Embed(
                            title="Permission denied",
                            description="You don't have enough currency to execute this action!",
                            color=cs.RANDOM_COLOR,
                        )
                    )

        return True


class Bot_Economy(BaseCog):
    def __init__(self, bot: Dwello):
        self.bot = bot
        self.be: BotEcoUtils = BotEcoUtils(self.bot)
        self.se: SharedEcoUtils = SharedEcoUtils(self.bot)

    @commands.hybrid_command(
        name="work",
        description="A boring job with a basic income. Gives some of the bot's currency in return.",
    )
    async def work_bot(self, ctx: DwelloContext):
        return await self.se.work(ctx, "bot")
