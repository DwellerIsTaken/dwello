# ESTABLISH OWNER ON VPS SOMEHOW
# MAKE THIS A FILE FILLED WITH COMMANDS FOR OWNER

from __future__ import annotations

import discord, asyncpg
from discord.ext import commands

from typing import Any, Optional, Literal
from utils import BaseCog
from bot import Dwello, DwelloContext

class OwnerCommands(BaseCog):

    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def sync(
    self, ctx: DwelloContext, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        bot = self.bot
        if not guilds:
            if spec == "~":
                synced = await bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                bot.tree.copy_global_to(guild=ctx.guild)
                synced = await bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                bot.tree.clear_commands(guild=ctx.guild)
                await bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await bot.tree.sync(guild=guild)
                
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def list_eventsubs(self, ctx: DwelloContext):

        return self.bot.twitch.event_subscription_list()

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def wipe_all_eventsubs(self, ctx: DwelloContext):

        return self.bot.twitch.unsubscribe_from_all_eventsubs()