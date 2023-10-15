from __future__ import annotations

import datetime
from typing import Any
from contextlib import suppress
from durations_nlp import Duration, exceptions

import discord
from discord.app_commands import Choice
from discord.ext import commands

import constants as cs
from core import BaseCog, Context, Dwello, Embed
from utils import HandleHTTPException
from .standard import member_check


async def tempmute(
    ctx: Context,
    member: discord.Member,
    period: str | None = None,
    reason: str = "Not specified",
) -> discord.Message | None:

    try:
        _period = Duration(period or "5 hours").to_milliseconds()
    except exceptions.InvalidTokenError or exceptions.ScaleFormatError:
        return await ctx.reply("Invalid duration string.", user_mistake=True)

    time_delta = datetime.timedelta(milliseconds=_period)

    if not await member_check(ctx, member):
        return

    if member.is_timed_out():
        return await ctx.reply("Provided member is already timed out!", user_mistake=True)

    with suppress(discord.HTTPException):
        await member.send(
            embed=Embed(
                timestamp=discord.utils.utcnow(),
                color=cs.WARNING_COLOR,
                title="Timed out",
                description=(
                    f"Guten tag! \nYou have been timed out in **{ctx.channel.guild.name}**, in case you were wondering. "
                    f"You must have said something wrong or it's just an administrator whom is playing with his toys. "
                    f"In any way, Make Yourself Great Again.\n \n Reason: **{reason}**\n\nTimed out for: `{time_delta}`"
                ),
            ).set_image(url="https://c.tenor.com/vZiLS-HKM90AAAAC/thanos-balance.gif"),
        )

    async with HandleHTTPException(ctx, title=f"Failed to mute {member}"):
        await member.timeout(time_delta, reason=reason)

    return await ctx.reply(
        embed=Embed(
            timestamp=discord.utils.utcnow(),
            color=cs.WARNING_COLOR,
            title="User is timed out!",
            description=(
                f"*Timed out by:* {ctx.author.mention}\n"
                f"\n**{member}** has been successfully timed out for awhile from this server! \nReason: `{reason}`"
            ),
        ).set_footer(text=f"Timed out for {time_delta}"),
    )


class Timeout(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)

    @commands.command(name="mute", brief="Mutes the member.")
    @commands.check_any(
        commands.guild_only(),
        commands.bot_has_permissions(moderate_members=True),
        commands.has_guild_permissions(moderate_members=True),
    )
    async def mute(self, ctx: Context, member: discord.Member, period: str, *, reason: str = "Not specified") -> None:
        """
        Mute a chosen member for a specified duration.
        When using the command with a prefix, provide the member's name first,
        followed by the duration as a single string without spaces (e.g., '1w2d1h18m2s', '5hours').
        You can then include a detailed reason with spaces. When using the slash command,
        enter the duration as a number and select the desired mute period for the member.
        """

        return await tempmute(ctx, member, period, reason)
    
    @discord.app_commands.command(name="mute", description="Mutes the member.")
    @discord.app_commands.choices(
        period=[
            Choice(name="Milliseconds", value="milliseconds"),
            Choice(name="Seconds", value="seconds"),
            Choice(name="Minutes", value="minutes"),
            Choice(name="Hours", value="hours"),
            Choice(name="Days", value="days"),
            Choice(name="Weeks", value="weeks"),
        ]
    )
    @commands.check_any(
        commands.guild_only(),
        commands.bot_has_permissions(moderate_members=True),
        commands.has_guild_permissions(moderate_members=True),
    )
    async def app_mute(
        self,
        ctx: Context,
        member: discord.Member,
        duration: int,
        period: Choice[str],
        *,
        reason: str = "Not specified",
    ) -> None:
        """
        Mute a chosen member for a specified duration.
        When using the command with a prefix, provide the member's name first,
        followed by the duration as a single string without spaces (e.g., '1w2d1h18m2s', '5hours').
        You can then include a detailed reason with spaces. When using the slash command,
        enter the duration as a number and select the desired mute period for the member.
        """

        return await tempmute(ctx, member, duration + period.value, reason)

    @commands.hybrid_command(name="unmute", brief="Unmutes member.", description="Unmutes member.")
    @commands.check_any(
        commands.guild_only(),
        commands.bot_has_permissions(moderate_members=True),
        commands.has_guild_permissions(moderate_members=True),
    )
    async def unmute(self, ctx: Context, member: discord.Member, *, reason: str = "Not specified") -> discord.Message | None:
        """Revoke the member's timeout (unmute)."""

        if member.id == self.bot.user.id:
            return await ctx.reply(
                embed=Embed(
                    title="Permission Denied.",
                    description="**I'm no hannibal Lector though, no need to unmute.**", # ?
                    color=cs.WARNING_COLOR,
                ), user_mistake=True,
            )

        if member.is_timed_out() is False:
            return await ctx.reply("The provided member isn't timed out.", ephemeral=True)

        if ctx.author == member:
            return await ctx.reply(
                embed=Embed(
                    title="Permission Denied.",
                    description="Don't try to unmute yourself if you aren't muted.",
                    color=cs.WARNING_COLOR,
                ), user_mistake=True,
            )

        async with HandleHTTPException(ctx, title=f"Failed to unmute {member}"):
            await member.timeout(None, reason=reason)

        return await ctx.reply(
            embed=Embed(
                title="Unmuted",
                description=f"{member} is unmuted.",
            ), permission_cmd=True,
        )

    @commands.hybrid_command(
        name="muted",
        aliases=["timed_out"],
        brief="Shows everyone who is currently timed out.",
        description="Shows everyone who is currently timed out.",
    )
    @commands.check_any(
        commands.guild_only(),
        commands.bot_has_permissions(view_audit_log=True),
    )
    async def timed_out(self, ctx: Context, member: discord.Member | None = None) -> discord.Message | None:
        """
        Displays a list of members who have been timed out within this guild or
        checks whether the provided member is currently timed out.
        """

        if member:
            return await ctx.reply(
                embed=Embed(
                    description=(
                        f"{member.name} is timed out until {discord.utils.format_dt(member.timed_out_until)}."
                        if member.is_timed_out() else f"{member.name} isn't muted."
                    ),
                ),
            )

        timed_out_list: list[discord.Member] = []
        reason_list: list[str] = []

        # three for-loops is kinda unoptimized
        member_updates: dict[int | str, discord.AuditLogEntry | Any] = {}
        async for entry in ctx.guild.audit_logs(action=discord.AuditLogAction.member_update):
            if entry.target in ctx.guild.members:
                member_updates[entry.target.id] = entry

        for member in ctx.guild.members:
            if member.is_timed_out():
                if entry := member_updates.get(member.id):
                    reason = entry.reason or "Not specified"
                    reason_list.append(str(reason))
                timed_out_list.append(member)

        embed: Embed = Embed(
            title="Timed out list",
            description="Nobody is timed out." if not timed_out_list else None,
        )

        for num, _member in enumerate(timed_out_list):
            if num > 4:
                embed.add_field(
                    name="\u2800",
                    value=f"There are/is **{len(timed_out_list) - 5}** more muted members out there.",
                    inline=False,
                )
                break
            embed.add_field(
                name=f"{_member.name}",
                value=f"*ID: {_member.id}*\nReason: `{reason_list[num]}`",
                inline=False,
            )

        return await ctx.reply(embed=embed, permission_cmd=True)
