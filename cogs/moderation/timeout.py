from __future__ import annotations

from discord.app_commands import Choice
from discord.ext import commands
import text_variables as tv
import discord, datetime

from contextlib import suppress

from utils import BaseCog, member_check, HandleHTTPException
from typing import Optional, Any

async def tempmute(self, ctx: commands.Context, member: discord.Member, duration: int, period: Optional[str] = None, reason: Optional[str] = None) -> Optional[discord.Embed]:

    time_period_dict = {
        "seconds": "seconds",
        "minutes": "minutes",
        "hours": "hours",
        "days": "days",
        "weeks": "weeks"
    }
    time_period = next((tp for tp in time_period_dict if tp in str(period)), "hours")
    time_delta = datetime.timedelta(**{time_period_dict[time_period]: duration})

    if not await member_check(ctx, member, self.bot): # ?
        return

    if member.is_timed_out():
        message = "Provided member is already timed out!"
        return await ctx.reply(message, mention_author=True, ephemeral=True)

    ban_embed = discord.Embed(
        title="Timed out",
        description=f"Guten tag! \nYou have been timed out in **{ctx.channel.guild.name}**, in case you were wondering. You must have said something wrong or it's just an administrator whom is playing with his toys. In any way, Make Yourself Great Again.\n \n Reason: **{reason}**\n\nTimed out for: `{time_delta}`",
        color=tv.warn_color,
        timestamp=discord.utils.utcnow()
    )
    ban_embed.set_image(url="https://c.tenor.com/vZiLS-HKM90AAAAC/thanos-balance.gif")
    ban_embed.set_footer(text=tv.footer)

    try:
        await member.send(embed=ban_embed)

    except TypeError as e:
        print(e)

    embed = discord.Embed(
        title="User is timed out!",
        description=f'*Timed out by:* {ctx.author.mention} \n \n**{member}** has been successfully timed out for awhile from this server! \nReason: `{reason}`',
        color=tv.warn_color,
        timestamp = discord.utils.utcnow()
    )
    embed.set_footer(text=f"Timed out for {time_delta}")

    async with HandleHTTPException(ctx, title=f'Failed to unban {member}'):
        await member.timeout(time_delta, reason=reason)

    return await ctx.send(embed=embed)

class Timeout(BaseCog):

    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)

    @commands.hybrid_command(name='mute', help="Mutes users whom are being dissidents. | Moderation ", with_app_command = True)
    @discord.app_commands.choices(period = [
        Choice(name="Seconds", value="seconds"), 
        Choice(name="Minutes", value="minutes"), 
        Choice(name="Hours", value="hours"),
        Choice(name="Days", value="days"),
        Choice(name="Weeks", value="weeks")]
        )
    @commands.bot_has_permissions(moderate_members = True)
    @commands.has_permissions(moderate_members = True)
    @commands.guild_only()
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: int, period: Optional[Choice[str]], *, reason=None) -> None:
        async with ctx.typing(ephemeral=True):

            return await tempmute(self, ctx, member, duration, period, reason)

    # LOOK INTO THIS:   
    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            missing_permissions_embed = discord.Embed(title = "Permission Denied.", description = f"You (or the bot) don't have permission to use this command. It should have __*{error.missing_permissions}*__ permission(s) to be able to use this command.", color = tv.warn_color)
            missing_permissions_embed.set_image(url = '\n https://cdn-images-1.medium.com/max/833/1*kmsuUjqrZUkh_WW-nDFRgQ.gif')
            missing_permissions_embed.set_footer(text=tv.footer)

            if ctx.interaction is None:
                return await ctx.channel.send(embed = missing_permissions_embed)
            
            else:
                return await ctx.interaction.response.send_message(embed = missing_permissions_embed, ephemeral = True)
        
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.reply("The provided argument could not be found or you forgot to provide one.", mention_author = True)

        elif isinstance(error, commands.errors.BadArgument):
            return await ctx.reply("Keep in mind that the time should be a number, the member should be mentioned.", mention_author = True)

        elif isinstance(error, discord.errors.Forbidden):
            if ctx.interaction is None:
                return await ctx.reply("This member cannot be timed out.", mention_author = True)
            else:
                return await ctx.interaction.response.send_message("This member cannot be timed out.", ephemeral = True)

        else:
            raise error

    @commands.hybrid_command(name='unmute', help="Unmutes users for good behaviour. | Moderation", with_app_command = True)
    @commands.bot_has_permissions(moderate_members = True)
    @commands.has_permissions(moderate_members = True)
    @commands.guild_only()
    async def unmute(self, ctx: commands.Context, member: discord.Member) -> Optional[discord.Embed]:
        async with ctx.typing(ephemeral=True):

            if member.id == self.bot.user.id:
                return await ctx.reply(embed= discord.Embed(title="Permission Denied.", description="**I'm no hannibal Lector though, no need to unmute.**", color=tv.color), ephemeral = True)

            elif member.is_timed_out() is False:
                return await ctx.reply("The provided member isn't timed out.", ephemeral = True)

            elif ctx.author == member:
                return await ctx.reply(embed = discord.Embed(title="Permission Denied.", description=f"Don't try to unmute yourself if you aren't muted.", color=tv.color), ephemeral = True)

            async with HandleHTTPException(ctx, title=f'Failed to unmute {member}'):
                await member.timeout(None, reason = "Unmuted")

            return await ctx.reply(embed= discord.Embed(title="Unmuted", description=f"{member} is unmuted.", color=tv.color), ephemeral = True)

    @commands.hybrid_command(name='timed_out', help="Shows everyone whom is timed out.", with_app_command = True) # MODERATION OR MEMBER-FRIENDLY?
    @commands.bot_has_permissions(view_audit_log = True)
    #@commands.has_permissions(moderate_members = True)
    @commands.guild_only()
    async def timed_out(self, ctx: commands.Context) -> Optional[discord.Embed]:
        async with ctx.typing(ephemeral=True):

            timed_out_list = []
            reason_list = []

            member_updates = {}

            async for entry in ctx.guild.audit_logs(action=discord.AuditLogAction.member_update):
                if entry.target in ctx.guild.members:
                    member_updates[entry.target.id] = entry

            print(member_updates)

            for member in ctx.guild.members:
                if member.is_timed_out():
                    entry = member_updates.get(member.id)
                    if entry:
                        if not entry.reason:
                            reason = "Not specified"
                        else:
                            reason = entry.reason

                        reason_list.append(str(reason))
                    timed_out_list.append(member)

            embed = discord.Embed(title = "Timed out list", color = tv.color)

            if len(timed_out_list) == 0:
                embed.add_field(name = "\u2800", value = "`Nobody is timed out.`")

            else:
                num = 0
                for i in timed_out_list:
                    if num > 4:
                        embed.add_field(name = "\u2800", value = f"There are/is **{int(len(timed_out_list)) - 5}** more muted members out there.", inline = False)
                        break

                    embed.add_field(name = f"{i.name}", value = f"*ID: {i.id}*\nReason: `{reason_list[num]}`", inline = False) #*#{i.discriminator}*
                    num += 1
            
            return await ctx.reply(embed=embed, ephemeral = True, mention_author = False)