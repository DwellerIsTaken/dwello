from __future__ import annotations

from typing import Any

import random
import discord
from discord.app_commands import Choice
from discord.ext import commands

from constants import MEMBER_CHECK_BOT_REPLIES, WARNING_COLOR
from core import BaseCog, Context, Dwello, Embed
from utils import HandleHTTPException


async def member_check(ctx: Context, member: discord.Member) -> bool:
    if ctx.author == member:
        await ctx.reply("https://media.tenor.com/qO9Gx8WTAGYAAAAC/get-some-help-stop-it.gif", user_mistake=True)
        return False

    if member.id == ctx.bot.user.id:
        await ctx.reply(random.choice(MEMBER_CHECK_BOT_REPLIES), user_mistake=True)
        return False

    if member.top_role > ctx.author.top_role: # check how top roles work
        await ctx.reply(
            f"You can't do that. {member.name} has a higher role than you do,"
            f"thus he is probably more important than you are. How utterly disheartening for you...",
            user_mistake=True,
        )
        return False
    return True


class StandardModeration(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)

    async def cog_check(self, ctx: Context) -> bool:
        return ctx.guild is not None

    @commands.hybrid_command(
        name="ban",
        brief="Bans members that don't behave.",
        description="Bans members that don't behave.",
    )
    @commands.check_any(
        commands.bot_has_permissions(ban_members=True),
        commands.has_permissions(ban_members=True),
    )
    async def ban(
        self,
        ctx: Context,
        member: discord.Member,
        *,
        reason: str | None = None,
    ) -> discord.Message | None:
        """Bans. Members."""

        if not await member_check(ctx, member):
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
            color=WARNING_COLOR,
        )

        return await ctx.channel.send(embed=embed)

    # somehow involve `send_messages=True` in overall functionality, so it wouldnt trigger any errors
    @commands.hybrid_command(name="unban", brief="Unbans users.", description="Unbans users.")
    @commands.check_any(
        commands.bot_has_permissions(ban_members=True, view_audit_log=True), # check `view_audit_log=True` only for slash maybe  # noqa: E501
        commands.has_guild_permissions(ban_members=True),
    )
    async def unban(self, ctx: Context, member: str) -> discord.Message | discord.InteractionMessage | None:
        """Unbans. Members. Accepts either user ID or name."""

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

        async with ctx.typing(ephemeral=True): # remove probably
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
            name = str(entry.user.name)
            id = str(entry.user.id)
            if (
                current.startswith(name.lower()[:item])
                or current.startswith(id[:item])
            ):
                choices.append(Choice(name=name, value=id))
        return choices[:5] if len(choices) > 5 else choices

    @commands.hybrid_command(
        name="kick",
        brief="Kick a member for not behaving.",
        description="Kick a member for not behaving.",
    )
    @commands.check_any(
        commands.bot_has_permissions(kick_members=True),
        commands.has_guild_permissions(kick_members=True),
    )
    async def kick(
        self,
        ctx: Context,
        member: discord.Member,
        *,
        reason: str | None = None,
    ) -> discord.Message | None:
        """Kicks. Members. Eh, these descriptions just keep getting more boring..."""

        if not await member_check(ctx, member):
            return

        if not reason:
            reason = "Not specified"

        embed: Embed = Embed(
            title="User kicked!",
            description=f"*Kicked by:* {ctx.author.mention}\n"
            f"\n**{member}** has been succesfully kicked from this server! \nReason: `{reason}`",
            color=WARNING_COLOR,
        )

        async with HandleHTTPException(ctx, title=f"Failed to kick {member}"):
            await member.kick(reason=reason)

        return await ctx.channel.send(embed=embed)

    @commands.hybrid_command(
        name="nick",
        aliases=["rename"],
        brief="Changes member's nickname.",
        description="Changes member's nickname.",
    )
    @commands.check_any(
        commands.bot_has_permissions(manage_nicknames=True),
        commands.has_guild_permissions(manage_nicknames=True),
    )
    async def nick(
        self,
        ctx: Context,
        member: discord.Member,
        *,
        nickname: str | None = None,
    ) -> discord.Message | None:
        """Nicks. Members. Bruh."""

        async with ctx.typing(ephemeral=True): # remove probably
            if not nickname and not member.nick:
                return await ctx.reply(f"**{member.name}** has no nickname to remove.", user_mistake=True)

            elif nickname and len(nickname) > 32:
                return await ctx.reply(f"Nickname is too long! ({len(nickname)}/32)", user_mistake=True)

            n = member.name
            message = f"Changed nickname of **{n}** to **{nickname}**." if nickname else f"Removed nickname of **{n}**."
            embed: Embed = Embed(
                title="Member renamed",
                description=message,
                color=discord.Colour.green() if nickname else WARNING_COLOR,
            )
            async with HandleHTTPException(ctx, title=f"Failed to set nickname for {member.name}."):
                await member.edit(nick=nickname)

            return await ctx.channel.send(embed=embed)
