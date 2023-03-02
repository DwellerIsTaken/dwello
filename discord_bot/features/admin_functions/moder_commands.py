from features.admin_functions.utils.member_check import member_check
from features.admin_functions.utils.moder_funcs import timeout
from discord.app_commands import Choice
from discord.ext import commands
import text_variables as tv
import discord

class moder_funcs(commands.Cog, name = "bans"):

    def __init__(self, bot):
        super().__init__
        self.bot = bot

    #-------------BAN-COMMAND-------------# {Bans users. Permissions: [kick_members=True, ban_members=True]}

    @commands.hybrid_command(name='ban', help="Bans users with bad behaviour. Only for admins!", with_app_command = True)
    @commands.has_permissions(kick_members=True, ban_members=True)
    async def ban(self,ctx, member: discord.Member, *, reason=None):
        #async with ctx.typing():

            if await member_check(ctx, member, self.bot) != True:
                return

            if reason is None:
                reason = "Not specified"

            ban_embed=discord.Embed(title="Permanently banned", description=f"Greetings! \nYou have been banned from **{ctx.channel.guild.name}**. You must have done something wrong or it's just an administrator whom is playing with his toys. In any way, it's an embezzlement kerfuffle out here.\n \n Reason: **{reason}**", color=tv.color)
            ban_embed.set_image(url = "https://media1.tenor.com/images/05186cf068c1d8e4b6e6d81025602215/tenor.gif?itemid=14108167")
            ban_embed.set_footer(text=tv.footer)
            ban_embed.timestamp = discord.utils.utcnow()
            await member.send(embed=ban_embed)

            embed = discord.Embed(title="User banned!", description=f'*Banned by:* {ctx.author.mention} \n \n**{member}** has been succesfully banned from this server! \nReason: `{reason}`',color=tv.warn_color)

            if ctx.interaction is None:
                await ctx.channel.send(embed=embed)

            else:
                await ctx.interaction.response.send_message(embed=embed)

            await member.ban(reason=reason)

    #-------------UNBAN-COMMAND-------------# {Unbans users. Permissions: [view_audit_log=True,ban_members=True]}

    @commands.hybrid_command(name='unban', help="Unbans users for good behaviour. Only for admins!", with_app_command = True)
    @commands.has_permissions(view_audit_log=True,ban_members=True)
    async def unban(self,ctx, member_object: str):
        #async with ctx.typing():

            member = discord.Object(id=member_object)

            try:
                await ctx.guild.unban(member)
                await ctx.interaction.response.send_message("The provided member is un-banned.", ephemeral = True)

            except discord.NotFound:
                return await ctx.interaction.response.send_message("The provided member doesn't exist or isn't banned.", ephemeral = True)

    @unban.autocomplete('member_object')
    async def autocomplete_callback(self, interaction: discord.Interaction, current: str):

        item = len(current)
        choices = []

        async for entry in interaction.guild.bans(limit=None):
            if current:
                pass

            if current.startswith(str(entry.user.name).lower()[:int(item)]):
                choices.append(Choice(name = str(entry.user.name), value = str(entry.user.id)))
                pass
                
            elif current.startswith(str(entry.user.id)[:int(item)]):
                choices.append(Choice(name = str(entry.user.name), value = str(entry.user.id)))
                pass

        if len(choices) > 5:
            return choices[:5]

        return choices

    #-------------KICK-COMMAND-------------# {Kicks users. Permissions: [kick_members=True]}

    @commands.hybrid_command(name='kick', help="Kick a member for bad behaviour. Only for admins!", with_app_command = True)
    @commands.has_permissions(kick_members=True)
    async def kick(self,ctx, member: discord.Member, *, reason=None):

        if await member_check(ctx, member, self.bot) != True:
            return

        if reason is None:
            reason = "Not specified"

        embed = discord.Embed(title="User kicked!", description=f'*Kicked by:* {ctx.author.mention} \n \n**{member}** has been succesfully kicked from this server! \nReason: `{reason}`',color=tv.warn_color)

        if ctx.interaction is None:
            await ctx.channel.send(embed=embed)

        else:
            await ctx.interaction.response.send_message(embed=embed)

        await member.kick(reason=reason)

    #-------------MUTE-COMMAND-------------# {Timeouts users. Permissions: [moderate_members = True]}

    @commands.hybrid_command(name='mute', help="Mutes users whom are being dissidents. Only for admins!", with_app_command = True)
    @discord.app_commands.choices(period = [Choice(name="Seconds", value="seconds"), Choice(name="Minutes", value="minutes"), Choice(name="Hours", value="hours"),Choice(name="Days", value="days"),Choice(name="Weeks", value="weeks")])
    @commands.has_permissions(moderate_members = True)
    async def mute(self, ctx, member: discord.Member, duration: int, period: Choice[str] = None, *, reason=None):
        #async with ctx.typing():

        try:
            await ctx.interaction.response.defer(ephemeral = True)

        except:
            pass

        return await timeout(self.bot, ctx, member, duration, period, reason)

    @mute.error
    async def mute_error(self,ctx, error):
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

    #-------------UNMUTE-COMMAND-------------# {Un-timeouts users. Permissions: [moderate_members = True]}

    @commands.hybrid_command(name='unmute', help="Unmutes users for good behaviour. Only for admins!", with_app_command = True)
    @commands.has_permissions(moderate_members = True)
    async def unmute(self,ctx, member: discord.Member):
        #async with ctx.typing():

            if member.id == self.bot.user.id:

                if ctx.interaction is None:
                    return await ctx.reply(embed= discord.Embed(title="Permission Denied.", description="**I'm no hannibal Lector though, no need to unmute.**", color=tv.color), mention_author = True)

                else:
                    return await ctx.interaction.response.send_message(embed= discord.Embed(title="Permission Denied.", description = "**Turn your sound up - I ain't muted.**", color=tv.color), ephemeral = True)
            
            if member.is_timed_out() is False:
                if ctx.interaction is None:
                    return await ctx.reply("The provided member isn't timed out.", mention_author = True)
                
                else:
                    return await ctx.interaction.response.send_message("The provided member isn't timed out.", ephemeral = True)

            try:
                if ctx.interaction.user == member:
                    return await ctx.interaction.response.send_message(embed = discord.Embed(title="Permission Denied.", description=f"Don't try to unmute yourself if you aren't muted.", color=tv.color), ephemeral = True)

            except:
                if ctx.message.author == member:
                    return await ctx.reply(embed = discord.Embed(title="Permission Denied.", description=f"Don't try to unmute yourself if you aren't muted.", color=tv.color), mention_author = True)

            if ctx.interaction is None:
                await ctx.reply(embed= discord.Embed(title="Unmuted", description=f"{member} is unmuted.", color=tv.color), mention_author = False)

            else:
                await ctx.interaction.response.send_message(embed= discord.Embed(title="Unmuted", description=f"{member} is unmuted.", color=tv.color), ephemeral = True)

            return await member.timeout(None, reason = "Un-timed out")

    #-------------TIMED-OUT-COMMAND-------------# {Timed out list. Permissions: [moderate_members = True,view_audit_log = True]}

    @commands.hybrid_command(name='timed_out', help="Shows everyone whom is timed out. Only for admins!", with_app_command = True)
    @commands.has_permissions(moderate_members = True, view_audit_log = True)
    async def timed_out(self, ctx):
        #async with ctx.typing():

            timed_out_list = []
            reason_list = []

            for member in ctx.guild.members:
                if member.is_timed_out():
                    timed_out_list.append(member)

                    async for entry in ctx.guild.audit_logs(action = discord.AuditLogAction.member_update):

                        if member == entry.target:
                            if str(entry.reason) == "None":
                                reason = "Not specified"

                            else:
                                reason = entry.reason

                            reason_list.append(str(reason))
                            break

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

            if ctx.interaction is None:
                await ctx.reply(embed = embed, mention_author = False)

            else:
                await ctx.interaction.response.defer(ephemeral = True)
                return await ctx.interaction.followup.send(embed = embed)

async def setup(bot):
  await bot.add_cog(moder_funcs(bot))