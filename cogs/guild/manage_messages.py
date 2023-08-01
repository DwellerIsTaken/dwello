from __future__ import annotations

from typing import Any

import discord
from discord.ext import commands

from core import BaseCog, Context, Dwello


class Messages(BaseCog):  # RENAME CLASS
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)

    @commands.hybrid_command(
        name="clear",
        help="Purges messages.",
        aliases=["purge", "cleanup"],
        with_app_command=True,
    )
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: Context, limit: int = 5, member: discord.Member = None) -> discord.Message | None:
        async with ctx.typing(ephemeral=True):
            msg = []

            if member is None:
                await ctx.channel.purge(limit=limit + 1)
                # print(f"{limit}" + " messages deleted by {0}".format(ctx.message.author))

                return await ctx.send(f"Purged {limit} messages", delete_after=3)

            async for m in ctx.channel.history():
                if len(msg) == limit:
                    break

                if m.author == member:
                    msg.append(m)

            await ctx.channel.delete_messages(msg)
            return await ctx.send(f"Purged {limit} messages of {member.mention}", delete_after=3)
