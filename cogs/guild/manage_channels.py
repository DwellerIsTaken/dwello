from discord.ext import commands
import text_variables as tv
import discord, os

from discord.ui import button, View, Button
from typing import Optional, Union, Tuple, Literal, Any
from utils import HandleHTTPException, BaseCog

class ChannelsFunctions():

    def __init__(self, bot):
        self.bot = bot

    async def counter_func(self, ctx: Union[commands.Context, discord.interactions.Interaction], name: Literal["all_counter","member_counter","bot_counter","counter_category"]) -> Optional[Tuple[discord.Message, Union[discord.VoiceChannel, discord.CategoryChannel]]]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                count = ctx.guild.member_count

                bot_counter = 0
                for member in ctx.guild.members:

                    if member.bot:
                        bot_counter += 1

                member_counter = int(ctx.guild.member_count) - bot_counter

                query = "SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2"
                row = await conn.fetchrow(query, ctx.guild.id, "counter_category")
                counter_category = row[0] if row else None

                if name == "all_counter":
                    count = count
                    nickname = "All"

                if name == "member_counter":
                    count = member_counter
                    nickname = "Member"

                elif name == "bot_counter":
                    count = bot_counter
                    nickname = "Bot"

                elif name == "counter_category":
                    if counter_category:
                        return await ctx.reply("This category already exists.", ephemeral = True)
                    
                    else:
                        counter_channel = await ctx.guild.create_category("📊 Server Counters 📊", reason=None)
                        await conn.execute(f"UPDATE server_data SET channel_id = $1, event_type = $2 WHERE guild_id = $3", counter_channel.id, name, ctx.guild.id)

                query = "SELECT channel_id, deny_clicked FROM server_data WHERE guild_id = $1 AND event_type = $2"
                row = await conn.fetchrow(query, ctx.guild.id, name)
                channel_id, deny_result = (row[0], row[1]) if row else (None, None)

                # should be checked in a channel_delete event
                '''try:
                    counter_category = discord.utils.get(ctx.guild.categories, id = int(category_record))

                except TypeError:
                    counter_category = None'''
                
                if channel_id is not None:       
                    return await ctx.reply("This counter already exists! Please provide another type of counter if you need to, otherwise __**please don`t create a counter that already exists**__.", mention_author=True, ephemeral=True)

                if deny_result is None and counter_category is None:
                    return await ctx.reply(embed = discord.Embed(description="**Do you want to create a category for your counters?**", color = tv.color).set_footer(text=tv.footer), view = Stats_View(self.bot, ctx, name), ephemeral = True)


                #elif deny_result is None and counter_category is not None: # ?
                    #await conn.execute("UPDATE server_data SET deny_clicked = $1 WHERE guild_id = $2", 1, ctx.guild.id)

                if channel_id is None:
                    counter_channel = await ctx.guild.create_voice_channel(f"📊 {nickname} counter: {count}", reason=None, category=counter_category)
                    await conn.execute(f"UPDATE server_data SET channel_id = $1, event_type = $2 WHERE guild_id = $3", counter_channel.id, name, ctx.guild.id)
                
        return await ctx.reply(f"The **{counter_channel.name}** is successfully created!", mention_author=False), counter_channel

    async def move_channel(self, ctx: commands.Context, category: discord.CategoryChannel, *args: str) -> None:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                placeholders = ','.join(['${}'.format(i + 2) for i in range(len(args))])
                query = "SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type IN ({})".format(placeholders)

                rows = await conn.fetch(query, ctx.guild.id, *args)

                for row in rows:
                    channel = ctx.guild.get_channel(row[0])
                    async with HandleHTTPException(ctx, title=f'Failed to move {channel} into {category}'):
                        await channel.move(category=category, beginning=True)

class Stats_View(View):

    def __init__(self, bot: commands.Bot, ctx: commands.Context, name: str, *, timeout: int = None):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.ctx = ctx
        self.name = name
        self.cf_ = ChannelsFunctions(self.bot)
    
    async def interaction_check(self, interaction: discord.Interaction) -> Optional[discord.Message]:
        if interaction.user.id == self.ctx.author.id:
            return True

        else:
            missing_permissions_embed = discord.Embed(title = "Permission Denied.", description = f"You can't interact with someone else's buttons.", color = tv.color)
            missing_permissions_embed.set_footer(text=tv.footer)
            return await interaction.response.send_message(embed=missing_permissions_embed, ephemeral=True)
    
    @button(style = discord.ButtonStyle.green, label="Approve", disabled=False, custom_id="approve_button")
    async def approve(self, interaction: discord.interactions.Interaction, button: Button) -> Optional[discord.Message]:

        counter_category = await self.cf_.counter_func(self.ctx, "counter_category")
        await self.cf_.counter_func(self.ctx, self.name)
        #await move_channel(interaction, counter_category)
        #await interaction.message.edit(embed=again_embed,view = None)

        return await interaction.response.edit_message(content=f"The **{counter_category[1].name}** is successfully created by **{interaction.user}**!", view=None)

    @button(style = discord.ButtonStyle.red, label="Deny", disabled=False, custom_id="deny_button")
    async def deny(self, interaction: discord.interactions.Interaction, button: Button) -> None:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                await conn.execute("UPDATE deny_clicked FROM server_data WHERE guild_id = $1", interaction.guild.id)
                await self.cf_.counter_func(self.ctx, self.name)
                return await interaction.response.edit_message(content=None,view = None)

class Channels(BaseCog):

    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        self.cf = ChannelsFunctions(self.bot)

    @commands.hybrid_group(name="counter", description="Counter group.", invoke_without_command = True, with_app_command=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def counter(self, ctx: commands.Context):

        return await ctx.reply("Please provide an argument! ```$counter [counter type]```", ephemeral=True)

    @counter.command(name='all', help="Creates a [voice] channel with all-user (bots included) count on this server.")
    async def all(self, ctx: commands.Context):

        return await self.cf.counter_func(ctx, "all_counter")

    @counter.command(name='members', help="Creating a [voice] channel with all-member count on this specific server.")
    async def members(self, ctx: commands.Context):
        
        return await self.cf.counter_func(ctx, "member_counter")

    @counter.command(name='bots', help="Creating a [voice] channel with all-bot count on this specific server.")
    async def bots(self, ctx: commands.Context):
        
        return await self.cf.counter_func(ctx, "bot_counter")

    @counter.command(name='category', help="Creates a category where your counter(s) will be stored.")
    async def category(self, ctx: commands.Context):

        category = await self.cf.counter_func(ctx, "counter_category")
        return await self.cf.move_channel(ctx, category[1], "all_counter", "member_counter", "bot_counter")

    @counter.command(name='list', help="Shows a list of counters you can create.")
    async def list(self, ctx: commands.Context):

        help_embed = discord.Embed(title = ":bar_chart: AVAILABLE COUNTERS :bar_chart:", description =  tv.server_statistics_list_help_embed_description, color = tv.color).set_footer(text=tv.footer)

        return await ctx.reply(embed = help_embed, ephemeral = True)