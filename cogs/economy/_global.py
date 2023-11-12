from __future__ import annotations

from typing import Any

import discord
import datetime
from discord.ext import commands

from utils import User
from core import BaseCog, Context, Dwello, Embed


class GlobalEconomy(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)

    @commands.hybrid_command(
        name="work",
        brief="A boring job with a basic income. Gives some of the bot's currency in return.",
        description="A boring job with a basic income. Gives some of the bot's currency in return.",
    )
    async def work(self, ctx: Context) -> discord.Message:
        user = await User.get(ctx.author.id, ctx.bot)

        if user.worked:
            my_datetime: datetime = (
                datetime.datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            )
            return await ctx.reply(
                embed=Embed(
                    title="→ \U0001d5e6\U0001d5fc\U0001d5ff\U0001d5ff\U0001d606 ←", #?
                    description=(
                        f"Your have already worked today!\n"
                        f"Your next workday begins in {discord.utils.format_dt(my_datetime, style='R')}"
                    ),
                )
            )
        
        amount = 250
        await user.increase_balance(ctx.message, amount, worked=True)
        # amount may depend on the job, but that isnt figured out yet

        return await ctx.reply(
            embed=Embed(
                timestamp=discord.utils.utcnow(),
                #title="→ \U0001d5e6\U0001d5ee\U0001d5f9\U0001d5ee\U0001d5ff\U0001d606 ←",  # 𝗦𝗮𝗹𝗮𝗿𝘆
                description=f"Your day was very successful. Your salary for today is *{amount}*.",
            )
            .set_footer(
                text=f"Your current balance: {user.balance}",
                icon_url=ctx.author.display_avatar.url,
            )
        )
    