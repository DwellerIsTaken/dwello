from __future__ import annotations

from typing import Any

import discord
from discord.app_commands import Choice
from discord.ext import commands

import constants as cs
from core import BaseCog, Context, Dwello, Embed
from utils import HandleHTTPException, member_check


class StandardModeration(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)

    async def cog_check(self, ctx: Context) -> bool:
        return ctx.guild is not None

    @commands.hybrid_command(name="ban", help="Bans users with bad behaviour.", with_app_command=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def ban(
        self,
        ctx: Context,
        member: discord.Member,
        *,
        reason: str | None = None,
    ) -> discord.Message | None:
        async with ctx.typing(ephemeral=True):
            if await member_check(ctx, member, self.bot) is not True:  # redo member_check later (?)
                return

            if not reason:
                reason = "Not specified"

            embed: Embed = Embed(
                title="Permanently banned",
                description=f"Greetings! \nYou have been banned from **{ctx.channel.guild.name}**. "
                "You must have done something wrong or it's just an administrator whom is playing with his toys. "
                f"In any way, it's an embezzlement kerfuffle out here.\n \n Reason: **{reason}**",
            )

            embed.set_image(url="https://media1.tenor.com/images/05186cf068c1d8e4b6e6d81025602215/tenor.gif?itemid=14108167")
            embed.set_footer(text=cs.FOOTER)
            embed.timestamp = discord.utils.utcnow()

            async with HandleHTTPException(ctx, title=f"Failed to ban {member}"):
                await member.ban(reason=reason)

            try:
                await member.send(embed=embed)

            except discord.HTTPException as e:
                print(e)

            embed: Embed = Embed(
                title="User banned!",
                description=f"*Banned by:* {ctx.author.mention}\n"
                f"\n**{member}** has been succesfully banned from this server! \nReason: `{reason}`",
                color=cs.WARNING_COLOR,
            )

            return await ctx.channel.send(embed=embed)

    @commands.hybrid_command(name="unban", help="Unbans users for good behaviour.", with_app_command=True)
    @commands.bot_has_permissions(send_messages=True, view_audit_log=True, ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx: Context, member: str) -> discord.Message | discord.InteractionMessage | None:
        if member.isdigit():
            member_id = int(member, base=10)
            try:
                ban_entry = await ctx.guild.fetch_ban(discord.Object(id=member_id))
                member = ban_entry.user
            except discord.NotFound:
                await ctx.reply("The provided member doesn't exist or isn't banned.", user_mistake=True)
        else:
            async for entry in ctx.guild.bans():
                if member in {
                    str(entry.user),
                    str(entry.user.id),
                    entry.user.name,
                    entry.user.display_name,
                    entry.user.mention,
                }:
                    member = entry.user
                    break

        if not isinstance(member, discord.User | discord.Object):
            return await ctx.reply("The provided member doesn't exist or isn't banned.", user_mistake=True)

        async with ctx.typing(ephemeral=True):
            async with HandleHTTPException(ctx, title=f"Failed to unban {member}"):
                await ctx.guild.unban(member)

            return await ctx.reply(
                embed=Embed(
                    description="The provided member is un-banned.",
                ),
                permission_cmd=True,
            )

    @unban.autocomplete("member")
    async def autocomplete_callback(self, interaction: discord.Interaction, current: str):
        item = len(current)
        choices = []

        async for entry in interaction.guild.bans(limit=None):
            if current.startswith(str(entry.user.name).lower()[:item]):  # noqa: SIM114
                choices.append(Choice(name=str(entry.user.name), value=str(entry.user.id)))
            elif current.startswith(str(entry.user.id)[:item]):
                choices.append(Choice(name=str(entry.user.name), value=str(entry.user.id)))
        return choices[:5] if len(choices) > 5 else choices

    @commands.hybrid_command(
        name="kick",
        help="Kick a member for bad behaviour.",
        aliases=["rename"],
        with_app_command=True,
    )
    @commands.bot_has_permissions(send_messages=True, kick_members=True)
    @commands.has_permissions(kick_members=True)
    async def kick(
        self,
        ctx: Context,
        member: discord.Member,
        *,
        reason: str | None = None,
    ) -> discord.Message | None:
        async with ctx.typing(ephemeral=True):
            if await member_check(ctx, member, self.bot) is not True:
                return

            if not reason:
                reason = "Not specified"

            embed: Embed = Embed(
                title="User kicked!",
                description=f"*Kicked by:* {ctx.author.mention}\n"
                f"\n**{member}** has been succesfully kicked from this server! \nReason: `{reason}`",
                color=cs.WARNING_COLOR,
            )

            async with HandleHTTPException(ctx, title=f"Failed to kick {member}"):
                await member.kick(reason=reason)

            return await ctx.channel.send(embed=embed)

    @commands.hybrid_command(
        name="nick",
        help="Changes the nickname of a provided member.",
        with_app_command=True,
    )
    @commands.bot_has_guild_permissions(manage_nicknames=True)
    @commands.has_guild_permissions(manage_nicknames=True)
    async def nick(
        self,
        ctx: Context,
        member: discord.Member,
        *,
        nickname: str | None = None,
    ) -> discord.Message | None:
        async with ctx.typing(ephemeral=True):
            if not nickname and not member.nick:
                return await ctx.reply(f"**{member}** has no nickname to remove.", user_mistake=True)

            elif nickname and len(nickname) > 32:
                return await ctx.reply(f"Nickname is too long! ({len(nickname)}/32)", user_mistake=True)

            message = "Changed nickname of **{user}** to **{nick}**.' if nickname else 'Removed nickname of **{user}**."
            embed: Embed = Embed(
                title="Member renamed",
                description=message.format(user=member, nick=nickname),
                color=cs.WARNING_COLOR,
            )

            async with HandleHTTPException(ctx, title=f"Failed to set nickname for {member}."):
                await member.edit(nick=nickname)

            return await ctx.channel.send(embed=embed)
