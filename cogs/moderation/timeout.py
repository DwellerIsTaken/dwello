from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Union

import discord
from discord.app_commands import Choice
from discord.ext import commands

import constants as cs
from utils import HandleHTTPException, member_check
from core import BaseCog, Dwello, Context, Embed


async def tempmute(
    bot: Dwello,
    ctx: Context,
    member: discord.Member,
    duration: int,
    period: Optional[str] = None,
    reason: Optional[str] = None,
) -> Optional[discord.Message]:  # remove bot param for member check
    time_period_dict = {
        "seconds": "seconds",
        "minutes": "minutes",
        "hours": "hours",
        "days": "days",
        "weeks": "weeks",
    }
    time_period = next((tp for tp in time_period_dict if tp in str(period)), "hours")
    time_delta = datetime.timedelta(**{time_period_dict[time_period]: duration})

    if not await member_check(ctx, member, bot):  # ?
        return

    if member.is_timed_out():
        message = "Provided member is already timed out!"
        return await ctx.reply(message, mention_author=True, ephemeral=True)

    embed: Embed = Embed(
        title="Timed out",
        description=(
            f"Guten tag! \nYou have been timed out in **{ctx.channel.guild.name}**, in case you were wondering. "
            f"You must have said something wrong or it's just an administrator whom is playing with his toys. "
            f"In any way, Make Yourself Great Again.\n \n Reason: **{reason}**\n\nTimed out for: `{time_delta}`"
        ),
        color=cs.WARNING_COLOR,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_image(url="https://c.tenor.com/vZiLS-HKM90AAAAC/thanos-balance.gif")
    embed.set_footer(text=cs.FOOTER)

    try:
        await member.send(embed=embed)

    except discord.HTTPException as e:
        print(e)

    embed: Embed = Embed(
        title="User is timed out!",
        description=f"*Timed out by:* {ctx.author.mention}\n"
        f"\n**{member}** has been successfully timed out for awhile from this server! \nReason: `{reason}`",
        color=cs.WARNING_COLOR,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text=f"Timed out for {time_delta}")

    async with HandleHTTPException(ctx, title=f"Failed to unban {member}"):
        await member.timeout(time_delta, reason=reason)

    return await ctx.send(embed=embed)


class Timeout(BaseCog):
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot

    @commands.hybrid_command(name="mute", help="Mutes member.", with_app_command=True)
    @discord.app_commands.choices(
        period=[
            Choice(name="Seconds", value="seconds"),
            Choice(name="Minutes", value="minutes"),
            Choice(name="Hours", value="hours"),
            Choice(name="Days", value="days"),
            Choice(name="Weeks", value="weeks"),
        ]
    )
    @commands.bot_has_permissions(moderate_members=True)
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def mute(
        self,
        ctx: Context,
        member: discord.Member,
        duration: int,
        period: Optional[Choice[str]],
        *,
        reason=None,
    ) -> None:
        async with ctx.typing(ephemeral=True):
            return await tempmute(self.bot, ctx, member, duration, period, reason)

    # LOOK INTO THIS:
    @mute.error
    async def mute_error(
        self,
        ctx: Context,
        error: Union[commands.MissingPermissions, commands.BotMissingPermissions, Any],
    ):
        if isinstance(error, commands.MissingPermissions):
            missing_permissions_embed = Embed(
                title="Permission Denied.",
                description=(
                    f"You (or the bot) don't have permission to use this command."
                    f"It should have __*{error.missing_permissions}*__ permission(s) to be able to use this command."
                ),
                color=cs.WARNING_COLOR,
            )
            missing_permissions_embed.set_image(url="https://cdn-images-1.medium.com/max/833/1*kmsuUjqrZUkh_WW-nDFRgQ.gif")
            missing_permissions_embed.set_footer(text=cs.FOOTER)

            if ctx.interaction is None:
                return await ctx.channel.send(embed=missing_permissions_embed)

            else:
                return await ctx.interaction.response.send_message(embed=missing_permissions_embed, ephemeral=True)

        elif isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.reply(
                "The provided argument could not be found or you forgot to provide one.",
                mention_author=True,
            )

        elif isinstance(error, commands.errors.BadArgument):
            return await ctx.reply(
                "Keep in mind that the time should be a number, the member should be mentioned.",
                mention_author=True,
            )

        elif isinstance(error, discord.errors.Forbidden):
            if ctx.interaction is None:
                return await ctx.reply("This member cannot be timed out.", mention_author=True)
            else:
                return await ctx.interaction.response.send_message("This member cannot be timed out.", ephemeral=True)

        else:
            raise error

    @commands.hybrid_command(name="unmute", help="Unmutes member.", with_app_command=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def unmute(self, ctx: Context, member: discord.Member) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            if member.id == self.bot.user.id:
                return await ctx.reply(
                    embed=Embed(
                        title="Permission Denied.",
                        description="**I'm no hannibal Lector though, no need to unmute.**",
                        color=cs.WARNING_COLOR,
                    ),
                    user_mistake=True,
                )

            elif member.is_timed_out() is False:
                return await ctx.reply("The provided member isn't timed out.", ephemeral=True)

            elif ctx.author == member:
                return await ctx.reply(
                    embed=Embed(
                        title="Permission Denied.",
                        description="Don't try to unmute yourself if you aren't muted.",
                        color=cs.WARNING_COLOR,
                    ),
                    user_mistake=True,
                )

            async with HandleHTTPException(ctx, title=f"Failed to unmute {member}"):
                await member.timeout(None, reason="Unmuted")

            return await ctx.reply(
                embed=Embed(
                    title="Unmuted",
                    description=f"{member} is unmuted.",
                ),
                permission_cmd=True,
            )

    @commands.hybrid_command(
        name="muted",
        aliases=["timed_out", "to"],
        help="Shows everyone who is timed out.",
        with_app_command=True,
    )  # MODERATION OR MEMBER-FRIENDLY (PERMS)?
    @commands.bot_has_permissions(view_audit_log=True)
    @commands.guild_only()
    async def timed_out(self, ctx: Context) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            timed_out_list: List[discord.Member] = []
            reason_list: List[str] = []

            member_updates: Dict[Union[int, str], Union[discord.AuditLogEntry, Any]] = {}
            async for entry in ctx.guild.audit_logs(action=discord.AuditLogAction.member_update):
                if entry.target in ctx.guild.members:
                    member_updates[entry.target.id] = entry

            for member in ctx.guild.members:
                if member.is_timed_out():
                    if entry := member_updates.get(member.id):
                        reason = entry.reason or "Not specified"
                        reason_list.append(str(reason))
                    timed_out_list.append(member)

            embed: Embed = Embed(title="Timed out list")

            if not timed_out_list:
                embed.add_field(name="\u2800", value="`Nobody is timed out.`")

            else:
                num = 0
                for i in timed_out_list:
                    if num > 4:
                        embed.add_field(
                            name="\u2800",
                            value=f"There are/is **{len(timed_out_list) - 5}** more muted members out there.",
                            inline=False,
                        )
                        break

                    embed.add_field(
                        name=f"{i.name}",
                        value=f"*ID: {i.id}*\nReason: `{reason_list[num]}`",
                        inline=False,
                    )  # *#{i.discriminator}*
                    num += 1

            return await ctx.reply(embed=embed, ephemeral=True, mention_author=False)
