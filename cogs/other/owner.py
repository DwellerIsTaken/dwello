# ESTABLISH OWNER ON VPS SOMEHOW
# MAKE THIS A FILE FILLED WITH COMMANDS FOR OWNER

from __future__ import annotations

from typing import Set, Literal, Optional

import asyncpg
import discord
from discord.ext import commands

from core import Context, Dwello, Embed


async def setup(bot: Dwello):
    await bot.add_cog(Owner(bot))


mk = discord.utils.escape_markdown


class Owner(commands.Cog):
    """
    🌐
    Commands only the bot's owners can use.
    """

    # it could also inherrit from other classes and whatnot

    def __init__(self, bot: Dwello) -> None:
        self.bot = bot

        self.select_emoji = "🌐"
        self.select_brief = "Owners' tools."

        self.additional_cmds: Set[str] = {"news"}

    @commands.is_owner()
    @commands.group(name="blacklist", invoke_without_command=True, hidden=True)
    async def blacklist_group(
        self,
        ctx: Context,
        user: discord.User = None,
        *,
        reason: str = None,
    ):
        if user:
            return await self.add(ctx, user, reason=reason)

        return await self.display(ctx)

    @commands.is_owner()
    @blacklist_group.command(name="add", hidden=True)
    async def add(
        self,
        ctx: Context,
        user: discord.User,
        *,
        reason: str = None,
    ) -> discord.Message:
        try:
            async with self.bot.safe_connection() as conn:
                await conn.execute(
                    "INSERT INTO blacklist(user_id, reason) VALUES($1, $2)",
                    user.id,
                    reason,
                )
        except asyncpg.exceptions.UniqueViolationError:
            return await ctx.reply("Already blacklisted.")

        # store as orm in dict instead?
        self.bot.blacklisted_users[user.id] = reason
        return await ctx.reply(f"Blacklisted **{mk(user.name, as_needed=False)}** successfully.")

    @commands.is_owner()
    @blacklist_group.command(name="display", hidden=True)
    async def display(self, ctx: Context) -> discord.Message:
        records = await self.bot.pool.fetch("SELECT * FROM blacklist")

        embed: Embed = Embed(
            title="Blacklisted users",
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
    async def remove(self, ctx: Context, user: discord.User) -> discord.Message:
        async with ctx.bot.safe_connection() as conn:
            query = """
            WITH deleted AS (
                DELETE FROM blacklist WHERE user_id = $1 RETURNING *
            ) SELECT COUNT(*) FROM deleted
            """
            await conn.execute(query, user.id)

        del self.bot.blacklisted_users[user.id]
        return await ctx.reply(
            f"**{mk(self.bot.get_user(user).name if isinstance(user, int) else user.name)}**"
            f" is removed from the blacklist."
        )

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: Context) -> Optional[discord.Message]:
        return await ctx.send(f"Synced {len(await self.bot.tree.sync())} global commands")

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def umbra_sync(
        self,
        ctx: Context,
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

    # REDO
    """@commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def list_eventsubs(self, ctx: Context):
        return self.bot.twitch.event_subscription_list()

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def wipe_all_eventsubs(self, ctx: Context):
        return self.bot.twitch.unsubscribe_from_all_eventsubs()"""
