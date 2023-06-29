# ESTABLISH OWNER ON VPS SOMEHOW
# MAKE THIS A FILE FILLED WITH COMMANDS FOR OWNER

from __future__ import annotations

from typing import Any, Literal, Optional, Union

import asyncpg
import discord
from discord.ext import commands
from typing_extensions import Self

import constants as cs
from bot import Dwello, DwelloContext
from utils import BaseCog


async def setup(bot: Dwello):
    await bot.add_cog(Owner(bot))


mk = discord.utils.escape_markdown


class Owner(BaseCog):
    # make it a separate vog that will inhirrit from other owner classes?

    def __init__(self: Self, bot: Dwello, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)

    @commands.is_owner()
    @commands.group(name="blacklist", invoke_without_command=True, hidden=True)
    async def blacklist_group(
        self: Self,
        ctx: DwelloContext,
        user: Union[discord.User, int] = None,
        *,
        reason: str = None,
    ):
        if user:
            return await self.add(ctx, user, reason=reason)

        return await self.display(ctx)

    @commands.is_owner()
    @blacklist_group.command(name="add", hidden=True)
    async def add(
        self: Self,
        ctx: DwelloContext,
        user: Union[discord.User, int],
        *,
        reason: str = None,
    ) -> discord.Message:
        if isinstance(user, int):
            user = self.bot.get_user(user)
            if not user:
                return await ctx.reply("Couldn't find the user.")
        user_id = user.id
        try:
            async with self.bot.safe_connection() as conn:
                await conn.execute(
                    "INSERT INTO blacklist(user_id, reason) VALUES($1, $2)",
                    user_id,
                    reason,
                )
        except asyncpg.exceptions.UniqueViolationError:
            return await ctx.reply("Already blacklisted.")

        self.bot.blacklisted_users[user_id] = reason
        return await ctx.reply(f"Blacklisted **{mk(user.name, as_needed=False)}** successfully.")

    @commands.is_owner()
    @blacklist_group.command(name="display", hidden=True)
    async def display(self: Self, ctx: DwelloContext) -> discord.Message:
        records = await self.bot.pool.fetch("SELECT * FROM blacklist")

        embed: discord.Embed = discord.Embed(
            title="Blacklisted users",
            color=cs.RANDOM_COLOR,
        )

        if records:
            for record in records:
                embed.add_field(
                    name=mk(self.bot.get_user(record["user_id"]).name),
                    value=record["reason"],
                )
        else:
            embed.description = "Blacklist is empty."

        return await ctx.reply(embed=embed)

    @commands.is_owner()
    @blacklist_group.command(name="remove", hidden=True)
    async def remove(self: Self, ctx: DwelloContext, user: Union[discord.User, int]) -> discord.Message:
        user_id = user if isinstance(user, int) else user.id
        async with ctx.bot.safe_connection() as conn:
            query = """
            WITH deleted AS (
                DELETE FROM blacklist WHERE user_id = $1 RETURNING *
            ) SELECT COUNT(*) FROM deleted
            """
            await conn.execute(query, user_id)

        del self.bot.blacklisted_users[user_id]
        return await ctx.reply(
            f"**{mk(self.bot.get_user(user).name if isinstance(user, int) else user.name)}**"
            f" is removed from the blacklist."
        )

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def sync(
        self: Self,
        ctx: DwelloContext,
        guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None,
    ) -> Optional[discord.Message]:
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

            await ctx.send(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}")
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
    async def list_eventsubs(self: Self, ctx: DwelloContext):
        return self.bot.twitch.event_subscription_list()

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def wipe_all_eventsubs(self: Self, ctx: DwelloContext):
        return self.bot.twitch.unsubscribe_from_all_eventsubs()
