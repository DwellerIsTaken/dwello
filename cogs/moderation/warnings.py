#import features.levelling.utils.levelling as levelling
from discord.app_commands import Choice
from discord.ext import commands
import text_variables as tv
import datetime, discord, asyncpg, os
from contextlib import suppress

from utils import member_check, interaction_check
from .timeout import Timeout
from typing import Optional, List

class TimeoutSuggestion(discord.ui.View):

    def __init__(self, bot: commands.Bot, ctx: commands.Context, member: discord.Member, reason: str ,timeout: int = None):
        super().__init__(timeout = timeout)
        self.bot = bot
        self.ctx = ctx
        self.member = member
        self.reason = reason

    @discord.ui.button(label = 'Yes', style = discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(interaction, self.ctx.author)

        #await self.ctx.interaction.response.defer()
        await Timeout.tempmute(self.bot, self.ctx, self.member, 12, None, self.reason)

        await interaction.message.edit(view = None)
        return await interaction.message.delete()

    @discord.ui.button(label = 'No', style = discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(interaction, self.ctx.author)
        
        await interaction.message.edit(view = None)
        return await interaction.message.delete()

class Warnings(commands.Cog):

    def __init__(self, bot: commands.Bot):
        super().__init__
        self.bot = bot

    @commands.hybrid_group(invoke_without_command=True, with_app_command=True)
    async def warning(self, ctx: commands.Context):

        embed = discord.Embed(title="Denied", description="Use `$warning [command_name]` instead.", color = tv.color)
        return await ctx.reply(embed=embed)

    @warning.command(name='warn', help="Gives member a warning. | Moderation", with_app_command = True)
    @commands.bot_has_permissions(moderate_members = True)
    @commands.has_permissions(moderate_members = True)
    @commands.guild_only()
    async def warn(self, ctx: commands.Context, member: discord.Member, reason: Optional[str] = None) -> Optional[discord.Message]:
        async with ctx.typing():
            async with self.bot.pool.acquire() as conn:
                async with conn.transaction():

                    if ctx.interaction is not None:          
                        await ctx.interaction.response.defer(ephemeral = True)

                    if await member_check(ctx, member, self.bot) != True:
                        return

                    if reason is None:
                        reason = "Not specified"

                    await self.bot.lvl.create_user(member.id, ctx.guild.id)

                    await conn.execute("INSERT INTO warnings(guild_id, user_id, warn_text, created_at, warned_by) VALUES($1,$2,$3,$4,$5)", ctx.guild.id, member.id, reason, discord.utils.utcnow(), ctx.author.id)
                    results = await conn.fetch("SELECT * FROM warnings WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)

                    warns = 0
                    for result in results:
                        if result["warn_text"] is not None:
                            warns += 1

                    public_embed = discord.Embed(title="User is warned!", description=f'*Warned by:* {ctx.author.mention} \n \n**{member}** has been successfully warned! \nReason: `{reason}`', color=tv.warn_color, timestamp=discord.utils.utcnow())
                    public_embed.set_footer(text = f"Amount of warnings: {warns}")

                    ban_embed=discord.Embed(title="Warned", description=f"Goede morgen! \nYou have been warned. Try to avoid being warned next time or it might get bad... \n\nReason: **{reason}**\n\nYour amount of warnings: `{warns}`", color=tv.warn_color, timestamp=discord.utils.utcnow())
                    ban_embed.set_image(url = "https://c.tenor.com/GDm0wZykMA4AAAAd/thanos-vs-vision-thanos.gif")
                    ban_embed.set_footer(text= tv.footer) #  • 

                    async with suppress(discord.HTTPException): await member.send(embed=ban_embed)

            return await ctx.send(embed=public_embed)

    @warning.command(name='warnings', help="Shows member`s warnings.", with_app_command = True)
    @commands.bot_has_permissions(moderate_members = True)
    @commands.guild_only()
    async def warnings(self, ctx: commands.Context, member: discord.Member = None) -> Optional[discord.Message]:
        async with ctx.typing():
            async with self.bot.pool.acquire() as conn:
                async with conn.transaction():

                    suggest = True
                    string = "This user has"

                    if not member:
                        member = ctx.author

                    if member.id == ctx.author.id:
                        string = "You have"
                        suggest = False

                    results = await conn.fetch("SELECT * FROM warnings WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)

                    member_s_check = str(member.name)[-1]
                    reason_list = []
                    date_list = []

                    if member_s_check == "s":
                        apostrophe = "`"

                    else:
                        apostrophe = "`s"

                    #public_embed = discord.Embed(title=f"{member.name}{apostrophe} warnings",color=discord.Colour.red())
                    public_embed = discord.Embed(color=tv.warn_color, timestamp=discord.utils.utcnow())
                    public_embed.set_thumbnail(url=f"{member.display_avatar}")
                    public_embed.set_author(name=f"{member.name}{apostrophe} warnings", icon_url=f"{member.display_avatar}")
                    public_embed.set_footer(text = tv.footer)

                    warns = 0
                    for result in results:
                        reason = result["warn_text"]
                        date = result["created_at"]
                        if reason is not None:
                            reason_list.append(str(reason))
                            date_list.append(date)
                            warns += 1

                    if warns == 0:
                        return await ctx.reply(f"{string} no warnings yet.", mention_author = True, ephemeral=True)

                    warns_1 = 0
                    for result in range(warns):

                        if warns_1 > 4:
                            public_embed.add_field(name = "\u2800", value = f"This member has **{warns - warns_1}** more warnings.")
                            break

                        date = datetime.datetime.strptime(str(date_list[int(warns_1)]),"%Y-%m-%d %H:%M:%S.%f%z") #2022-09-25 18:26:08.602989+00:00
                        date = discord.utils.format_dt(date)

                        public_embed.add_field(name = f"Warning:   {int(warns_1) + 1}", value = f"Reason: `{reason_list[int(warns_1)]}`\nDate: *{date}*", inline = False) # -1
                        warns_1 += 1

                    await ctx.defer()
                    await ctx.reply(embed = public_embed, mention_author=True)

            if suggest != False:
                suggestion_embed = discord.Embed(title = "A lot of warnings", description = f"Would you like to time **{member}** out for 12 hours?", color = tv.warn_color)

            if warns > 3:
                if ctx.author.guild_permissions.moderate_members == True:
                    return await ctx.send(embed = suggestion_embed, view = TimeoutSuggestion(self.bot, ctx, member, "Too many warnings!"))

    @warning.command(name='remove', help="Removes selected warnings. | Moderation", with_app_command = True)
    @commands.bot_has_permissions(moderate_members = True)
    @commands.has_permissions(moderate_members = True)
    @commands.guild_only()
    async def remove_warn(self, ctx: commands.Context, member: discord.Member, warning: str) -> Optional[discord.Message]:
        async with ctx.typing():
            async with self.bot.pool.acquire() as conn:
                async with conn.transaction():

                    await ctx.defer()

                    if member == ctx.author:
                        return await ctx.reply(embed= discord.Embed(title="Permission Denied.", description= "**Do. Not. Attempt.**", color=tv.warn_color), mention_author = True)

                    elif await member_check(ctx, member, self.bot) != True:
                        return
                    
                    records = await conn.fetch("SELECT * FROM warnings WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)

                    warnings = 0
                    warns = 0
                    for result in records:
                        if result["warn_text"] is not None:
                            warns += 1

                    if warning == "all":
                        for result in records:
                            if result["warn_text"] is not None:
                                warnings += 1

                        await conn.execute("DELETE FROM warnings WHERE warn_text IS NOT NULL AND guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)

                    else:
                        await conn.execute("DELETE FROM warnings WHERE warn_text = $1 AND guild_id = $2 AND user_id = $3", warning, ctx.guild.id, member.id)
                        warnings += 1

                    #embed = discord.Embed(title="Removed",description=f"Successfully removed *{warnings}* warning(s).",color=tv.color)

                    public_embed = discord.Embed(title="Removed!", description=f'*Removed by:* {ctx.author.mention} \n \nSuccessfully removed *{warnings}* warning(s) from {member}.',color=tv.color, timestamp=discord.utils.utcnow())
                    public_embed.set_footer(text = f"Warnings left: {warns - warnings}")

            return await ctx.reply(embed = public_embed, mention_author=False)

    @remove_warn.autocomplete('warning')
    async def autocomplete_callback(self, interaction: discord.Interaction, current: str) -> List[Choice]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                member = interaction.namespace["member"]
                #member = interaction.guild.get_member(int(member.id))

                member = discord.Object(member.id)

                # temporary
                results = await conn.fetch("SELECT * FROM warnings WHERE guild_id = $1 AND user_id = $2", interaction.guild.id, member.id)

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