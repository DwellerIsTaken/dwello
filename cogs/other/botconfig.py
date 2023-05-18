from __future__ import annotations

import asyncpg
import discord

from discord.ext import commands

from typing import Literal, Optional, Union, Any, List
from typing_extensions import Self

import constants as cs
from utils import BaseCog
from bot import Dwello, DwelloContext

class PrefixCommands:

    def __init__(self: Self, bot: Dwello) -> None:
        self.bot = bot

    async def set_prefix(self: Self, ctx: DwelloContext, prefix: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                try:
                    await conn.execute("INSERT INTO prefixes(prefix, guild_id) VALUES($1, $2)", prefix, ctx.guild.id)

                except asyncpg.exceptions.StringDataRightTruncationError:
                    return await ctx.reply("This prefix is too long!", user_mistake=True) # add allowed prefix length
                
                except asyncpg.exceptions.UniqueViolationError:
                    return await ctx.reply("This prefix is already added!", user_mistake=True)
                
        await self.bot.db.fetch_table_data("prefixes")
        return await ctx.reply(embed = discord.Embed(description=f"The prefix is set to `{prefix}`", color=cs.RANDOM_COLOR), permission_cmd=True)
    
    async def display_prefixes(self: Self, ctx: DwelloContext) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():

                prefixes = await conn.fetch("SELECT prefix FROM prefixes WHERE guild_id = $1", ctx.guild.id)
                default_prefixes: List[str] = self.bot.DEFAULT_PREFIXES + [f"<@!{self.bot.user.id}>"]

                embed: discord.Embed= discord.Embed(title = "Prefixes", color=cs.RANDOM_COLOR)
                embed.add_field(
                    name="Guild's prefix(es)", 
                    value=(", ".join(f"`{p['prefix']}`" for p in prefixes) if prefixes else "`None` -> `dw.help prefix`"),
                    inline=False,
                )
                embed.add_field(
                    name="Default prefixes", 
                    value= ", ".join(p if str(self.bot.user.id) in p else f'`{p}`' for p in default_prefixes),
                inline=False,
                )
                embed.set_footer(text=None)

        return await ctx.reply(embed=embed, mention_author=False, ephemeral=False)
    
    async def remove_prefix(self: Self, ctx: DwelloContext, prefix: Union[str, Literal['all']]) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():

                prefixes = await conn.fetch("SELECT prefix FROM prefixes WHERE guild_id = $1", ctx.guild.id)

                if not (prefixes[0] if prefixes else None):
                    return await ctx.reply(f"Prefix isn't yet set. \n```/prefix add [prefix]```", user_mistake=True)
                
                count = len(prefixes)
                if prefix == "all":
                    await conn.execute("DELETE FROM prefixes WHERE guild_id = $1", ctx.guild.id)

                elif isinstance(prefix, str):
                    await conn.execute("DELETE FROM prefixes WHERE prefix = $1 AND guild_id = $2", prefix, ctx.guild.id)
                    count = 1

        await self.bot.db.fetch_table_data("prefixes")
        return await ctx.reply(embed=discord.Embed(description=f"{'Prefix has' if count == 1 else f'{count} prefixes have'} been removed.", color=cs.RANDOM_COLOR), permission_cmd=True)

class BotConfig(BaseCog):

    def __init__(self: Self, bot: Dwello, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        self.prefixc: PrefixCommands = PrefixCommands(self.bot)
        
    @commands.hybrid_group(invoke_without_command=True, with_app_command=False)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def prefix(self: Self, ctx: DwelloContext):
        async with ctx.typing():

            """if prefix is None:
                embed = discord.Embed(description="```$help prefix```", color=tv.warn_color)
                return await ctx.reply(embed=embed, user_mistake=True)"""
            
            return await self.prefixc.display_prefixes(ctx)

    @prefix.command(name="add", help="Adds bot prefix to the guild.")
    async def add_prefix(self: Self, ctx: DwelloContext, prefix: str):

        return await self.prefixc.set_prefix(ctx, prefix)

    @commands.has_permissions()
    @prefix.command(name="display", help="Displays all prefixes.", aliases=["prefixes"])
    async def display_prefix(self: Self, ctx: DwelloContext):

        return await self.prefixc.display_prefixes(ctx)
    
    @prefix.command(name="remove", description = "Removes guild's prefix(es).")
    async def delete_prefix(self: Self, ctx: DwelloContext, prefix: str):
            
        return await self.prefixc.remove_prefix(ctx, prefix)
    
    @delete_prefix.autocomplete('prefix')
    async def autocomplete_callback_(self: Self, interaction: discord.Interaction, current: str):
        
        return await self.bot.autocomplete.choice_autocomplete(interaction, current, "prefixes", "prefix", None, True)