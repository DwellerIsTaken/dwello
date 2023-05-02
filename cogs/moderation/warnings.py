from __future__ import annotations

from discord.ui import View, Button, button
from discord.app_commands import Choice
from discord.ext import commands
import text_variables as tv
import datetime, discord
import asyncpg

from .timeout import tempmute

from typing import Optional, List, Any

from bot import Dwello, DwelloContext
from utils import (BaseCog, 
                   apostrophize,
                   member_check, 
                   interaction_check)

class TimeoutSuggestion(View):

    def __init__(self, bot: Dwello, ctx: DwelloContext, member: discord.Member, reason: str ,timeout: int = None):
        super().__init__(timeout = timeout)
        self.bot = bot
        self.ctx = ctx
        self.member = member
        self.reason = reason

    @button(label = 'Yes', style = discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: Button):
        await interaction_check(interaction, self.ctx.author)

        #await self.ctx.interaction.response.defer()
        await tempmute(self.bot, self.ctx, self.member, 12, None, self.reason)

        await interaction.message.edit(view = None)
        return await interaction.message.delete()

    @button(label = 'No', style = discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: Button):
        await interaction_check(interaction, self.ctx.author)
        
        await interaction.message.edit(view = None)
        return await interaction.message.delete()

class Warnings(BaseCog):

    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)

    @commands.hybrid_group(invoke_without_command=True, with_app_command=True)
    async def warning(self, ctx: DwelloContext):

        embed = discord.Embed(description=f"```{ctx.clean_prefix}warning [command_name]```", color = tv.warn_color)
        return await ctx.reply(embed=embed)

    @warning.command(name='warn', help="Gives member a warning.", with_app_command = True)
    @commands.bot_has_permissions(moderate_members = True)
    @commands.has_permissions(moderate_members = True)
    @commands.guild_only()
    async def warn(self, ctx: DwelloContext, member: discord.Member, reason: Optional[str] = None) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            async with self.bot.pool.acquire() as conn:
                conn: asyncpg.Connection
                async with conn.transaction():

                    if not await member_check(ctx, member, self.bot):
                        return

                    if not reason:
                        reason = "Not specified"

                    await self.bot.lvl.create_user(member.id, ctx.guild.id)

                    await conn.execute("INSERT INTO warnings(guild_id, user_id, warn_text, created_at, warned_by) VALUES($1,$2,$3,$4,$5)", ctx.guild.id, member.id, reason, discord.utils.utcnow(), ctx.author.id)
                    results = await conn.fetch("SELECT * FROM warnings WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)

                    warns = 0
                    for result in results:
                        if result['warn_text']:
                            warns += 1

                    public_embed = discord.Embed(title="User is warned!", description=f"*Warned by:* {ctx.author.mention} \n "
                                                f"\n**{member}** has been successfully warned! \nReason: `{reason}`", color=tv.warn_color, timestamp=discord.utils.utcnow())
                    public_embed.set_footer(text = f"Amount of warnings: {warns}")

                    ban_embed=discord.Embed(title="Warned", description=f"Goede morgen! \nYou have been warned. Try to avoid being warned next time or it might get bad..."
                                            f" \n\nReason: **{reason}**\n\nYour amount of warnings: `{warns}`", color=tv.warn_color, timestamp=discord.utils.utcnow())
                    ban_embed.set_image(url = "https://c.tenor.com/GDm0wZykMA4AAAAd/thanos-vs-vision-thanos.gif")
                    ban_embed.set_footer(text= tv.footer) #  • 

                    try:
                        await member.send(embed=ban_embed)

                    except discord.HTTPException as e:
                        print(e)

            return await ctx.send(embed=public_embed)

    @warning.command(name='warnings', help="Shows member's warnings.", with_app_command = True)
    @commands.bot_has_permissions(moderate_members = True)
    @commands.guild_only()
    async def warnings(self, ctx: DwelloContext, member: discord.Member = None) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            async with self.bot.pool.acquire() as conn:
                conn: asyncpg.Connection
                async with conn.transaction():

                    if not member:
                        member = ctx.author

                    if member == ctx.author:
                        string = "You have"
                        suggest = False
                    
                    else:
                        suggest = True
                        string = "This user has"

                    results = await conn.fetch("SELECT * FROM warnings WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)

                    reason_list = []
                    date_list = []

                    #public_embed = discord.Embed(title=f"{member.name}{apostrophe} warnings",color=discord.Colour.red())
                    public_embed = discord.Embed(color=tv.warn_color, timestamp=discord.utils.utcnow())
                    public_embed.set_thumbnail(url=f"{member.display_avatar}")
                    public_embed.set_author(name=f"{apostrophize(member.name)} warnings", icon_url=str(member.display_avatar))
                    public_embed.set_footer(text = tv.footer)

                    warns = 0
                    for result in results:
                        reason = result['warn_text']
                        date = result['created_at']

                        if reason:
                            reason_list.append(str(reason))
                            date_list.append(date)
                            warns += 1

                    if warns == 0:
                        return await ctx.reply(embed=discord.Embed(description=f"{string} no warnings yet.", color=tv.color), mention_author = True, ephemeral=True) # kind of success, so embed can be used

                    warns_1 = 0
                    for result in range(warns):

                        if warns_1 > 4:
                            public_embed.add_field(name = "\u2800", value = f"This member has **{warns - warns_1}** more warnings.")
                            break

                        date = datetime.datetime.strptime(str(date_list[int(warns_1)]),"%Y-%m-%d %H:%M:%S.%f%z") #2022-09-25 18:26:08.602989+00:00
                        date = discord.utils.format_dt(date)

                        public_embed.add_field(name = f"Warning:   {int(warns_1) + 1}", value = f"Reason: `{reason_list[int(warns_1)]}`\nDate: *{date}*", inline = False) # -1
                        warns_1 += 1

                    await ctx.defer() # because view can be called (?)
                    await ctx.reply(embed = public_embed, mention_author=False)

            if suggest:
                suggestion_embed = discord.Embed(title = "A lot of warnings", description = f"Would you like to time **{member}** out for 12 hours?", color = tv.warn_color)

            if warns > 3:
                if ctx.author.guild_permissions.moderate_members: # == True ?
                    return await ctx.send(embed = suggestion_embed, view = TimeoutSuggestion(self.bot, ctx, member, "Too many warnings!"))

    @warning.command(name='remove', help="Removes selected warnings.", with_app_command = True)
    @commands.bot_has_permissions(moderate_members = True)
    @commands.has_permissions(moderate_members = True)
    @commands.guild_only()
    async def remove_warn(self, ctx: DwelloContext, member: discord.Member, warning: str) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            async with self.bot.pool.acquire() as conn:
                conn: asyncpg.Connection
                async with conn.transaction():

                    if member == ctx.author:
                        return await ctx.reply(embed= discord.Embed(title="Permission Denied.", description= "**Do. Not. Attempt.**", color=tv.warn_color), mention_author = True, ephemeral=True)

                    if not await member_check(ctx, member, self.bot):
                        return
                    
                    #records = await conn.fetch("SELECT * FROM warnings WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)

                    #warnings = await conn.fetch("SELECT COUNT(*) FROM warnings WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)
                    '''warns = 0
                    for result in records:
                        if result["warn_text"]:
                            warns += 1

                    if warning == "all":
                        warnings = await conn.fetch("SELECT COUNT(*) FROM warnings WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)
                        await conn.execute("DELETE FROM warnings WHERE warn_text IS NOT NULL AND guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)

                    else:
                        await conn.execute("DELETE FROM warnings WHERE warn_text = $1 AND guild_id = $2 AND user_id = $3", warning, ctx.guild.id, member.id)
                        warnings += 1'''
                    
                    if warning == "all":
                        warnings = await conn.fetchval("DELETE FROM warnings WHERE warn_text IS NOT NULL AND guild_id = $1 AND user_id = $2 RETURNING COUNT(*)", ctx.guild.id, member.id)

                    else:
                        await conn.execute("DELETE FROM warnings WHERE warn_text = $1 AND guild_id = $2 AND user_id = $3", warning, ctx.guild.id, member.id)
                        warnings = 1

                    embed = discord.Embed(title="Removed", 
                                                 description=f'*Removed by:* {ctx.author.mention} \n \nSuccessfully removed *{warnings}* warning(s) from {member}.',
                                                 color=tv.color, 
                                                 timestamp=discord.utils.utcnow())
                    
                    #embed.set_footer(text = f"Warnings left: {warns - warnings}") why tho

            return await ctx.reply(embed = embed, mention_author=False, ephemeral=True)

    @remove_warn.autocomplete('warning')
    async def autocomplete_callback(self, interaction: discord.Interaction, current: str) -> List[Choice]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction(): # REDO: DONT FETCH ON AUTOCOMPLETE

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