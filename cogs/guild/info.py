from __future__ import annotations

import contextlib
from typing import Any, List, Literal, Optional, Union  # noqa: F401

import discord
from discord.ext import commands

from core import BaseCog, Context, Dwello, Embed  # noqa: F401


class Info(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)

    async def cog_check(self, ctx: Context) -> bool:
        return ctx.guild is not None

    @commands.hybrid_group(invoke_without_command=True, with_app_command=True)
    async def guild(self, ctx: Context) -> discord.Message | None:
        return await ctx.send_help(ctx.command)

    @guild.command(name="info", help="Shows info on a guild.")
    async def info(self, ctx: Context) -> discord.Message | None:
        guild = ctx.guild

        invite_link = None
        with contextlib.suppress(commands.BotMissingPermissions, commands.MissingPermissions):
            invites = await guild.invites()
            invite_link = invites[0].url

        embed: Embed = (
            (
                Embed(
                    timestamp=discord.utils.utcnow(),
                    title=f"Info on {guild.name}",
                    description=guild.description,
                    url=guild.vanity_url or invite_link,
                )
                .set_footer(
                    text=f"ID: {guild.id}",
                    icon_url=guild.icon.url if guild.icon else None,
                )
                .set_thumbnail(
                    url=guild.icon.url if guild.icon else None,
                )
            )
            .add_field(name="Owner", value=getattr(guild.owner, "name", "None"))  # owner could be None
            .add_field(name="Created at", value=discord.utils.format_dt(guild.created_at, style="D"))
            .add_field(name="Total Members", value=guild.member_count or len(guild.members))  # member_count could be None
            .add_field(name="MFA Level", value=str(guild.mfa_level)[9:])
            .add_field(name="NSFW Level", value=str(guild.nsfw_level)[10:])
            .add_field(name="Nitro Level", value=guild.premium_tier)
            .add_field(name="Text Channels", value=len(guild.text_channels))
            .add_field(name="Voice Channels", value=len(guild.voice_channels))
            .add_field(name="Public Threads", value=len(guild.threads))
        )
        if guild.rules_channel:
            embed.add_field(name="Rules", value=guild.rules_channel.mention)
        embed.add_field(name="Emoji Limit", value=guild.emoji_limit)
        embed.add_field(name="Verification Level", value=guild.verification_level)
        if guild.scheduled_events:
            embed.add_field(
                name="Upcoming Events",
                value="\n".join(f"[{event.name}]({event.url})" for event in guild.scheduled_events[-5:]),
            )
        """if guild.roles:
            embed.add_field(
                name="Highest Roles",
                value="\n".join(role.name for role in guild.roles[-5:])
            )"""  # looks bad
        if any((guild.icon, guild.banner)):
            embed.add_field(
                name="Assets",
                value=(
                    f"{f'[Icon]({guild.icon.url})' if guild.icon else ''}"
                    f"{f'[Banner]({guild.banner.url})' if guild.banner else ''}"
                ),
            )
        return await ctx.reply(embed=embed)
