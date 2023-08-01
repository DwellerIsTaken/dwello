from __future__ import annotations

from typing import Any, Literal

import discord
from discord.app_commands import Choice
from discord.ext import commands

from core import BaseCog, Context, Dwello, Embed
from utils import Prefix


class Customisation(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self._prefix: PrefixConfig = PrefixConfig(self.bot)

    async def cog_check(self, ctx: Context) -> bool:
        return ctx.guild is not None

    @commands.hybrid_group(aliases=["prefixes"], invoke_without_command=True, with_app_command=True)
    async def prefix(self, ctx: Context):
        async with ctx.typing():
            return await self._prefix.display_prefixes(ctx)

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @prefix.command(name="add", help="Adds bot prefix to the guild.")
    async def add_prefix(self, ctx: Context, *, prefix: str):
        _prefix: list[str] = prefix.split()
        if len(_prefix) > 1:
            return await ctx.reply("Prefix musn't contain whitespaces.", user_mistake=True)

        return await self._prefix.set_prefix(ctx, prefix)

    @prefix.command(name="display", help="Displays all prefixes.")
    async def display_prefix(self, ctx: Context):
        return await self._prefix.display_prefixes(ctx)

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @prefix.command(name="remove", description="Removes guild's prefix(es).")
    async def delete_prefix(self, ctx: Context, prefix: str):
        return await self._prefix.remove_prefix(ctx, prefix)

    @delete_prefix.autocomplete("prefix")
    async def autocomplete_callback_prefix(self, interaction: discord.Interaction, current: str):
        item = len(current)
        prefixes: list[Prefix] = await self.bot.db.get_prefixes(interaction.guild)
        choices: list[Choice[str]] = [Choice(name="all", value="all")] + [
            Choice(name=prefix.name, value=prefix.name)
            for prefix in prefixes
            if current.startswith(prefix.name.lower()[:item])
        ]
        if len(choices) > 10:
            return choices[:10]
        return choices


class PrefixConfig:
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot
        self.db = bot.db

    async def set_prefix(self, ctx: Context, _prefix: str) -> discord.Message | None:
        if not isinstance(prefix := await self.db.add_prefix(ctx.guild, _prefix, context=ctx), Prefix):
            return
        try:
            self.bot.guild_prefixes[ctx.guild.id].append(prefix.name)
        except KeyError:
            self.bot.guild_prefixes[ctx.guild.id] = [prefix.name]
        return await ctx.reply(embed=Embed(description=f"The prefix is set to `{prefix.name}`"), permission_cmd=True)

    async def display_prefixes(self, ctx: Context) -> discord.Message | None:
        default_prefixes: list[str] = self.bot.DEFAULT_PREFIXES + [f"<@!{self.bot.user.id}>"]
        prefixes = await self.db.get_prefixes(ctx.guild)

        embed: Embed = Embed(title="Prefixes").set_footer(text=None)

        if ctx.guild:
            embed.add_field(
                name="Guild's prefix(es)",
                value=", ".join(f"`{p.prefix}`" for p in prefixes) if prefixes else "`None` -> `dw.help prefix`",
                inline=False,
            )
        embed.add_field(
            name="Default prefixes",
            value=", ".join(p if str(self.bot.user.id) in p else f"`{p}`" for p in default_prefixes),
            inline=False,
        )
        return await ctx.reply(embed=embed, mention_author=False, ephemeral=False)

    async def remove_prefix(self, ctx: Context, prefix: str | Literal["all"]) -> discord.Message | None:
        if not (await self.db.get_prefixes(ctx.guild)):
            return await ctx.reply(
                "Prefix isn't yet set. \n```/prefix add [prefix]```",
                user_mistake=True,
            )
        count = len(await self.db.remove_prefix(prefix, ctx.guild, all=prefix == "all"))
        self.bot.guild_prefixes[ctx.guild.id].remove(prefix)
        return await ctx.reply(
            embed=Embed(
                description=f"{'Prefix has' if count == 1 else f'{count} prefixes have'} been removed.",
            ),
            permission_cmd=True,
        )
