from __future__ import annotations

from typing import List, Literal, Optional, Union  # noqa: F401

import contextlib

import discord
from discord.ext import commands

from core import BaseCog, Context, Dwello, Embed  # noqa: F401

class Info(BaseCog):
    def __init__(self, bot: Dwello) -> None:
        self.bot: Dwello = bot
        super().__init__(self.bot)

    async def cog_check(self, ctx: Context) -> bool:
        return ctx.guild is not None
    
    @commands.hybrid_group(invoke_without_command=True, with_app_command=True)
    async def guild(self, ctx: Context) -> Optional[discord.Message]:
        return await ctx.send_help(ctx.command)
    
    @guild.command(name='info', help='Shows info on a guild.')
    async def info(self, ctx: Context) -> Optional[discord.Message]:
        guild = ctx.guild

        invite_link = None
        with contextlib.suppress(commands.BotMissingPermissions, commands.MissingPermissions):
            invites = await guild.invites()
            invite_link = invites[0].url

        embed: Embed = Embed(
            timestamp=discord.utils.utcnow(),
            title=f"Info on {guild.name}",
            description=guild.description,
            url=guild.vanity_url or invite_link,
        ).set_footer(
            text=f"ID: {guild.id}", icon_url=guild.icon.url if guild.icon else None,
        ).set_thumbnail(
            url=guild.icon.url if guild.icon else None,
        )
        embed.add_field(name="Owner", value=guild.owner.name)
        embed.add_field(name="Created at", value=discord.utils.format_dt(guild.created_at, style='D'))
        embed.add_field(name="Total Members", value=guild.member_count if guild.member_count else len(guild.members))
        embed.add_field(name="MFA Level", value=str(guild.mfa_level)[:-9])
        embed.add_field(name="NSFW Level", value=str(guild.nsfw_level)[:-10])
        embed.add_field(name="Nitro Level", value=guild.premium_tier)
        embed.add_field(name="Text Channels", value=len(guild.text_channels))
        embed.add_field(name="Voice Channels", value=len(guild.voice_channels))
        embed.add_field(name="Public Threads", value=len(guild.threads))
        if guild.rules_channel:
            embed.add_field(name="Rules", value=guild.rules_channel.mention)
        embed.add_field(name="Sticker Limit", value=guild.sticker_limit)
        embed.add_field(name="Verification Level", value=guild.verification_level)
        if guild.scheduled_events:
            embed.add_field(
                name="Upcoming Events",
                value="\n".join(f"[{event.name}]({event.url})" for event in guild.scheduled_events[-5:])
            )
        '''if guild.roles:
            embed.add_field(
                name="Highest Roles",
                value="\n".join(role.name for role in guild.roles[-5:])
            )''' #looks bad
        if any((guild.icon, guild.banner)):
            embed.add_field(
                name="Assets",
                value=(
                    f"{f'[Icon]({guild.icon.url})' if guild.icon else ''}"
                    f"{f'[Banner]({guild.banner.url})' if guild.banner else ''}"
                ),
            )
        return await ctx.reply(embed=embed)
    

class PrefixConfig:
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot
        self.db = bot.db

    async def display_prefixes(self, ctx: Context) -> Optional[discord.Message]:
        default_prefixes: List[str] = self.bot.DEFAULT_PREFIXES + [f"<@!{self.bot.user.id}>"]
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

    async def remove_prefix(self, ctx: Context, prefix: Union[str, Literal["all"]]) -> Optional[discord.Message]:
        if not (await self.db.get_prefixes(ctx.guild)):
            return await ctx.reply(
                "Prefix isn't yet set. \n```/prefix add [prefix]```",
                user_mistake=True,
            )
        count = len(await self.db.remove_prefix(prefix, ctx.guild, all=prefix=='all'))
        self.bot.guild_prefixes[ctx.guild.id].remove(prefix)
        return await ctx.reply(
            embed=Embed(
                description=f"{'Prefix has' if count == 1 else f'{count} prefixes have'} been removed.",
            ),
            permission_cmd=True,
        )