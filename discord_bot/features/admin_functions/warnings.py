from features.admin_functions.utils.member_check import member_check
from proper_debugging.interaction_check import interaction_check
import features.admin_functions.utils.moder_funcs as funcs
import features.levelling.utils.levelling as levelling
from discord.app_commands import Choice
from discord.ext import commands
import text_variables as tv
import datetime
import discord
import asqlite

class TimeoutSuggestion(discord.ui.View):

    def __init__(self, bot: discord.Client, ctx: commands.Context, member: discord.Member, reason: str ,timeout: int = None):
        super().__init__(timeout = timeout)
        self.bot = bot
        self.ctx = ctx
        self.member = member
        self.reason = reason

    @discord.ui.button(label = 'Yes', style = discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(interaction, self.ctx.author)

        #await self.ctx.interaction.response.defer()
        await funcs.timeout(self.bot, self.ctx, self.member, 12, None, self.reason)

        await interaction.message.edit(view = None)
        return await interaction.message.delete()

    @discord.ui.button(label = 'No', style = discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(interaction, self.ctx.author)
        
        await interaction.message.edit(view = None)
        return await interaction.message.delete()

class Warnings(commands.Cog, name = "warnings"):

    def __init__(self, bot):
        super().__init__
        self.bot = bot

    @commands.hybrid_group(invoke_without_command=True,with_app_command=True)
    async def warning(self,ctx):

        embed = discord.Embed(title="Denied", description="Use `$warning [command_name]` instead.",color=tv.color)

        return await ctx.reply(embed=embed)

    #-------------WARN-COMMAND-------------# {Gives user a warning. Permissions: [moderate_members=True]}

    @warning.command(name='warn', help="Gives member a warning. Only for admins!", with_app_command = True)
    @commands.has_permissions(moderate_members = True)
    async def warn(self, ctx, member: discord.Member, reason = None):
        async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:
                #async with ctx.typing():

                    if ctx.interaction is not None:          
                        await ctx.interaction.response.defer(ephemeral = True)

                    if await member_check(ctx, member, self.bot) != True:
                        return

                    if reason is None:
                        reason = "Not specified"

                    await levelling.create_user(member.id, ctx.guild.id)

                    await cursor.execute("INSERT INTO warnings(guild_id, user_id, warn_text, created_at, warned_by) VALUES(?,?,?,?,?)", ctx.guild.id, member.id, reason, discord.utils.utcnow(), ctx.author.id)
                    await connector.commit()

                    await cursor.execute(f"SELECT * FROM warnings WHERE guild_id = {ctx.guild.id} AND user_id = {member.id}")
                    results = await cursor.fetchall()

                    warns = 0
                    for result in results:
                        if result["warn_text"] is not None:
                            warns += 1

                    public_embed = discord.Embed(title="User is warned!", description=f'*Warned by:* {ctx.author.mention} \n \n**{member}** has been successfully warned! \nReason: `{reason}`',color=tv.warn_color)
                    public_embed.set_footer(text = f"Amount of warnings: {warns}")
                    public_embed.timestamp = discord.utils.utcnow()

                    ban_embed=discord.Embed(title="Warned", description=f"Goede morgen! \nYou have been warned. Try to avoid being warned next time or it might get bad... \n\nReason: **{reason}**\n\nYour amount of warnings: `{warns}`", color=tv.warn_color)
                    ban_embed.set_image(url = "https://c.tenor.com/GDm0wZykMA4AAAAd/thanos-vs-vision-thanos.gif")
                    ban_embed.set_footer(text= tv.footer) #  • 
                    ban_embed.timestamp = discord.utils.utcnow()

                    await cursor.close()
                    await connector.close()

                    try:
                        await member.send(embed=ban_embed)

                    except discord.HTTPException:
                        pass

                    if ctx.interaction is None:
                        return await ctx.reply(embed = public_embed, mention_author=False)
                    
                    else:
                        await ctx.channel.send(embed=public_embed)
                        return await ctx.interaction.followup.send("Successfully warned!")

    #-------------WARNINGS-COMMAND-------------# {Shows user's warnings. Permissions: []}

    @warning.command(name='warnings', help="Shows the member`s warnings.", with_app_command = True)
    @commands.has_permissions()
    async def warnings(self, ctx, member: discord.Member = None):
        async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:

                suggest = True
                string = "This user has"

                if not member:
                    member = ctx.author

                if member.id == ctx.author.id:
                    string = "You have"
                    suggest = False

                await cursor.execute(f"SELECT * FROM warnings WHERE guild_id = {ctx.guild.id} AND user_id = {member.id}")
                results = await cursor.fetchall()

                member_s_check = str(member.name)[-1]
                reason_list = []
                date_list = []

                if member_s_check == "s":
                    apostrophe = "`"

                else:
                    apostrophe = "`s"

                #public_embed = discord.Embed(title=f"{member.name}{apostrophe} warnings",color=discord.Colour.red())
                public_embed = discord.Embed(color=tv.warn_color)
                public_embed.set_thumbnail(url=f"{member.display_avatar}")
                public_embed.set_author(name=f"{member.name}{apostrophe} warnings", icon_url=f"{member.display_avatar}")
                public_embed.set_footer(text = tv.footer)
                public_embed.timestamp = discord.utils.utcnow()

                warns = 0
                for result in results:
                    reason = result["warn_text"]
                    date = result["created_at"]
                    if reason is not None:
                        reason_list.append(str(reason))
                        date_list.append(date)
                        warns += 1

                if warns == 0:
                    if ctx.interaction is None:
                        return await ctx.reply(f"{string} no warnings yet.", mention_author = True)
                
                    else:
                        await ctx.interaction.response.defer(ephemeral = True)
                        return await ctx.interaction.followup.send(f"{string} no warnings yet.")

                warns_1 = 0
                for result in range(warns):

                    if warns_1 > 4:
                        public_embed.add_field(name = "\u2800", value = f"This member has **{warns - warns_1}** more warnings.")
                        break

                    date = datetime.datetime.strptime(str(date_list[int(warns_1)]),"%Y-%m-%d %H:%M:%S.%f%z") #2022-09-25 18:26:08.602989+00:00
                    date = discord.utils.format_dt(date)

                    public_embed.add_field(name = f"Warning:   {int(warns_1) + 1}", value = f"Reason: `{reason_list[int(warns_1)]}`\nDate: *{date}*", inline = False) # -1
                    warns_1 += 1

                if ctx.interaction is None:
                    await ctx.reply(embed = public_embed, mention_author = False)

                else:
                    await ctx.interaction.response.defer(ephemeral = True)
                    await ctx.interaction.followup.send(embed = public_embed)

                if suggest != False:
                    suggestion_embed = discord.Embed(title = "A lot of warnings", description = f"Would you like to time **{member}** out for 12 hours?", color = tv.warn_color)

                if warns > 3:
                    if ctx.author.guild_permissions.moderate_members == True:
                        return await ctx.channel.send(embed = suggestion_embed, view = TimeoutSuggestion(self.bot, ctx, member, "Too many warnings!"))

    #-------------REMOVE-WARN-COMMAND-------------# {Removes user's warning(s). Permissions: [moderate_members=True]}

    @warning.command(name='remove', help="Removes selected warnings. Only for admins!", with_app_command = True)
    @commands.has_permissions(moderate_members = True)
    async def remove_warn(self, ctx, member: discord.Member, warning: str):
        async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:

                if ctx.interaction is not None:          
                    await ctx.interaction.response.defer(ephemeral = True)

                if member == ctx.author:
                    return await ctx.reply(embed= discord.Embed(title="Permission Denied.", description= "**Do. Not. Attempt.**", color=tv.warn_color), mention_author = True)

                elif await member_check(ctx, member, self.bot) != True:
                    return
                
                await cursor.execute(f"SELECT * FROM warnings WHERE guild_id = {ctx.guild.id} AND user_id = {member.id}")
                records = await cursor.fetchall()

                warnings = 0
                warns = 0
                for result in records:
                    if result["warn_text"] is not None:
                        warns += 1

                if warning == "all":
                    for result in records:
                        if result["warn_text"] is not None:
                            warnings += 1

                    await cursor.execute("DELETE FROM warnings WHERE warn_text IS NOT NULL AND guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))

                else:
                    await cursor.execute("DELETE FROM warnings WHERE warn_text = ? AND guild_id = ? AND user_id = ?", (warning, ctx.guild.id, member.id))
                    warnings += 1

                embed = discord.Embed(title="Removed",description=f"Successfully removed *{warnings}* warning(s).",color=tv.color)

                public_embed = discord.Embed(title="Removed!", description=f'*Removed by:* {ctx.author.mention} \n \nSuccessfully removed *{warnings}* warning(s).',color=tv.color)
                public_embed.set_footer(text = f"Warnings left: {warns - warnings}")
                public_embed.timestamp = discord.utils.utcnow()

                if ctx.interaction is None:
                    await ctx.reply(embed = public_embed, mention_author=False)
                    
                else:
                    await ctx.channel.send(embed=public_embed)
                    await ctx.interaction.followup.send(embed=embed)

                await connector.commit()
                await cursor.close()
                return await connector.close()

    @remove_warn.autocomplete('warning')
    async def autocomplete_callback(self, interaction: discord.Interaction, current: str):
         async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:

                member = interaction.namespace["member"]
                #member = interaction.guild.get_member(int(member.id))

                member = discord.Object(member.id)

                await cursor.execute(f"SELECT * FROM warnings WHERE guild_id = {interaction.guild.id} AND user_id = {member.id}")
                results = await cursor.fetchall()

                item = len(current)
                choices = []

                choices.append(Choice(name = "all", value = "all"))

                for result in results:

                    text = result["warn_text"]
                    date = result["created_at"]

                    if text is None:
                        if date is None:
                            continue

                    name = str(text) # {str(date)[:10]}

                    #if len(str(text)) > 15:
                        #name = f"{str(text)[:15]}...\u2800{str(date)[:10]}"

                    if current:
                        pass

                    if current.startswith(str(text).lower()[:int(item)]):
                        choices.append(Choice(name = name, value = name))
                        pass
                        
                    elif current.startswith(str(date)[:int(item)]):
                        choices.append(Choice(name = name, value = name))
                        pass

                if len(choices) > 5:
                    return choices[:5]

                return choices

async def setup(bot):
  await bot.add_cog(Warnings(bot))