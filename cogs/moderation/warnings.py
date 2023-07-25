from __future__ import annotations

from typing import List, Optional

import asyncpg
import discord
import contextlib
from discord.ext import commands
from discord.ui import Button, button
from discord.app_commands import Choice

import constants as cs
from core import BaseCog, Context, Dwello, Embed, Member, View
from utils import Warning, apostrophize, interaction_check, member_check

from .timeout import tempmute


class TimeoutSuggestion(View):
    def __init__(
        self,
        bot: Dwello,
        ctx: Context,
        member: Member,
        reason: str,
        **kwargs,
    ):
        super().__init__(**kwargs)
        
        self.bot = bot
        self.ctx = ctx
        self.member = member
        self.reason = reason
        
    @button(label="Yes", style=discord.ButtonStyle.green)
    async def _yes(self, interaction: discord.Interaction, button: Button) -> None:
        await interaction_check(interaction, self.ctx.author)

        # await self.ctx.interaction.response.defer()
        await tempmute(self.bot, self.ctx, self.member, 12, None, self.reason)

        self.finish()
        return await interaction.message.delete()

    @button(label="No", style=discord.ButtonStyle.red)
    async def _no(self, interaction: discord.Interaction, button: Button) -> None:
        await interaction_check(interaction, self.ctx.author)

        self.finish()
        return await interaction.message.delete()


class Warnings(BaseCog):
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot
        
    async def cog_check(self, ctx: Context) -> bool:
        return ctx.guild is not None
        
    async def _warn(
        self,
        ctx: Context,
        member: Member,
        reason: Optional[str] = "Not specified",
    ) -> Optional[discord.Message]:
            
        if not await member_check(ctx, member, self.bot):
            return

        await member.warn(ctx, reason)
        warns: int = len(await member.get_warnings(ctx))
        with contextlib.suppress(discord.HTTPException):
            await member.send(
                embed=Embed(
                    title="Warned",
                    description=(
                        "Goede morgen!\n"
                        "You have been warned. Try to avoid being warned next time or it might get bad...\n\n"
                        f"Reason: **{reason}**\n\nYour amount of warnings: `{warns}`"
                    ),
                    color=cs.WARNING_COLOR,
                    timestamp=discord.utils.utcnow(),
                )
                .set_footer(text=cs.FOOTER)
                .set_image(url="https://c.tenor.com/GDm0wZykMA4AAAAd/thanos-vs-vision-thanos.gif"),
            )
            
        return await ctx.send(
            embed=Embed(
                title="User is warned!",
                description=(
                    f"*Warned by:* {ctx.author.mention}\n"
                    f"\n**{member}** has been successfully warned! \nReason: `{reason}`"
                ),
                color=cs.WARNING_COLOR,
                timestamp=discord.utils.utcnow(),
            )
            .set_footer(text=f"Amount of warnings: {warns}"),
        )
    
    async def _warnings(self, ctx: Context, member: Member = commands.Author) -> Optional[discord.Message]:
        warnings: List[Warning] = await member.get_warnings(ctx)

        embed: Embed = Embed(timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=f"{member.display_avatar}")
        embed.set_footer(text=cs.FOOTER)
        embed.set_author(
            name=f"{apostrophize(member.name)} warnings",
            icon_url=str(member.display_avatar),
        )

        warns = 0
        for warning in warnings:
            if reason := warning.reason:
                embed.add_field(
                    name=f"Warning #{warns+1}",
                    value=(
                        f"Reason: *{reason}*\n"
                        f"Date: {discord.utils.format_dt(warning.created_at)}"
                    ),
                    inline=False,
                )
                warns += 1

        if not warns:
            embed=Embed(description=f"{'You have' if member == ctx.author else 'This user has'} no warnings yet.")
            
        await ctx.defer() # because view can be called (?)
        await ctx.reply(embed=embed, mention_author=False)

        if member != ctx.author and warns > 3 and ctx.author.guild_permissions.moderate_members:
            return await ctx.send(
                embed=Embed(
                    title="A lot of warnings",
                    description=f"Would you like to time **{member}** out for 12 hours?",
                    color=cs.WARNING_COLOR,
                ),
                view=TimeoutSuggestion(self.bot, ctx, member, "Too many warnings!"),
            )
    
    @commands.command(name='warn', help='Gives member a warning.')
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx: Context, member: Member, reason: Optional[str]) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            print(member.name, type(member))
            return await self._warn(ctx, member, reason)
        
    @commands.command(name='warnings', help="Shows member's warnings.")
    @commands.has_permissions(moderate_members=True)
    async def warnings(self, ctx: Context, member: Member = commands.Author) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            return await self._warnings(ctx, member)
        
    @commands.hybrid_group(name='warning', invoke_without_command=True, with_app_command=True)
    async def warning(self, ctx: Context):
        return await ctx.send_help(ctx.command)
    
    @warning.command(name="warn", help="Gives member a warning.", with_app_command=True)
    @commands.has_permissions(moderate_members=True)
    async def hybrid_warn(self, ctx: Context, member: Member, reason: Optional[str]) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            return await self._warn(ctx, member, reason)
        
    @warning.command(name="warnings", aliases=['show', 'display'], help="Shows member's warnings.", with_app_command=True)
    async def hybrid_warnings(self, ctx: Context, member: Member = commands.Author) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            return await self._warnings(ctx, member)

    @warning.command(name="remove", help="Removes selected warnings.", with_app_command=True)
    @commands.has_permissions(moderate_members=True)
    async def remove_warn(self, ctx: Context, member: Member, warning: str) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            async with self.bot.pool.acquire() as conn:
                conn: asyncpg.Connection
                async with conn.transaction():
                    if member == ctx.author:
                        return await ctx.reply(
                            embed=Embed(
                                title="Permission Denied.",
                                description="**Do. Not. Attempt.**",
                                color=cs.WARNING_COLOR,
                            ),
                            user_mistake=True,
                        )

                    if not await member_check(ctx, member, self.bot):
                        return

                    """
                    records = await conn.fetch("SELECT * FROM warnings WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)

                    warnings = await conn.fetch("SELECT COUNT(*) FROM warnings WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)
                    warns = 0
                    for result in records:
                        if result["warn_text"]:
                            warns += 1

                    if warning == "all":
                        warnings = await conn.fetch("SELECT COUNT(*) FROM warnings WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)
                        await conn.execute("DELETE FROM warnings WHERE warn_text IS NOT NULL AND guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)

                    else:
                        await conn.execute("DELETE FROM warnings WHERE warn_text = $1 AND guild_id = $2 AND user_id = $3", warning, ctx.guild.id, member.id)
                        warnings += 1"""  # noqa: E501

                    if warning == "all":
                        warnings = await conn.fetchval(
                            "DELETE FROM warnings WHERE warn_text IS NOT NULL AND guild_id = $1 AND user_id = $2 RETURNING COUNT(*)",  # noqa: E501
                            ctx.guild.id,
                            member.id,
                        )

                    else:
                        await conn.execute(
                            "DELETE FROM warnings WHERE warn_text = $1 AND guild_id = $2 AND user_id = $3",
                            warning,
                            ctx.guild.id,
                            member.id,
                        )
                        warnings = 1

            embed: Embed = Embed(
                title="Removed",
                description=(
                    f"*Removed by:* {ctx.author.mention} \n \nSuccessfully removed *{warnings}* warning(s) from {member}."
                ),
                timestamp=discord.utils.utcnow(),
            )
            return await ctx.reply(embed=embed, permission_cmd=True)

    @remove_warn.autocomplete("warning")
    async def autocomplete_callback(self, interaction: discord.Interaction, current: str) -> List[Choice]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():  # REDO: DONT FETCH ON AUTOCOMPLETE
                member = interaction.namespace["member"]
                # member = interaction.guild.get_member(int(member.id))

                member = discord.Object(member.id)

                # temporary
                results = await conn.fetch(
                    "SELECT * FROM warnings WHERE guild_id = $1 AND user_id = $2",
                    interaction.guild.id,
                    member.id,
                )

                item = len(current)
                choices = [Choice(name="all", value="all")]

                for result in results:
                    text = result["warn_text"]
                    date = result["created_at"]

                    if text is None and date is None:
                        continue

                    name = str(text)  # {str(date)[:10]}

                    if current.startswith(str(text).lower()[:item]):  # noqa: SIM114
                        choices.append(Choice(name=name, value=name))
                    elif current.startswith(str(date)[:item]):
                        choices.append(Choice(name=name, value=name))
                if len(choices) > 5:
                    return choices[:5]

        return choices
