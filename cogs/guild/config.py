from __future__ import annotations

from discord.app_commands import Choice
from discord.ext import commands
from string import Template
import text_variables as tv
import discord, os

from typing import Optional, Literal, Any
from utils import Twitch, BaseCog, AutoComplete

class ConfigFunctions():

    def __init__(self, bot):
        self.bot = bot

    async def add_message(self, ctx: commands.Context, name: str, text: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                record = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)

                if (record[0] if record else None) is None:
                    return await ctx.reply(f"Please use `${name} channel` first.", ephemeral=True, mention_author=True) # adjust based on group/subgroup

                if not text: # check will only work in ctx.prefix case
                    return await ctx.reply(f"Please enter the {name} message, if you want to be able to use this command properly.", ephemeral=True, mention_author=True)

                result = await conn.fetchrow("SELECT message_text FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)

                await conn.execute("UPDATE server_data SET message_text = $1, event_type = COALESCE(event_type, $2) WHERE guild_id = $3 AND COALESCE(event_type, $2) = $2", text, name, ctx.guild.id)
                string = f"{name.capitalize()} message has been {'set' if not result[0] else 'updated'} to: ```{text}```"

        return await ctx.reply(embed = discord.Embed(description=string, color = tv.color), mention_author = False, ephemeral=True)
    
    async def add_channel(self, ctx: commands.Context, name: str, channel: Optional[discord.TextChannel] = commands.CurrentChannel) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                result = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)

                string = f"The channel has been {'set' if not (result[0] if result else None) else 'updated'} to {channel.mention}"

                if (result[0] if result else None) == channel.id:
                    return await ctx.reply(f"{name.capitalize()} channel has already been set to this channel!", mention_author = True, ephemeral = True)

                #await conn.execute("UPDATE server_data SET channel_id = $1, event_type = COALESCE(event_type, $2) WHERE guild_id = $3 AND COALESCE(event_type, $2) = $2", channel.id, name, ctx.guild.id)

                await conn.execute("UPDATE server_data SET channel_id = $1 WHERE guild_id = $2 AND event_type = $3", channel.id, ctx.guild.id, name) # DB DOESNT WORK ?

        await channel.send(embed = discord.Embed(description=f"This channel has been set as a *{name}* channel.", color = tv.color))
        return await ctx.reply(embed = discord.Embed(description=string, color = tv.color), mention_author = False, ephemeral=True)

    async def message_display(self, ctx: commands.Context, name: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                result = await conn.fetchrow("SELECT message_text FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)

                if not (result[0] if result else None):
                    return await ctx.reply(f"{name.capitalize()} message isn't yet set. \n```/{name} message set```", ephemeral=True, mention_author=True)

        return await ctx.reply(embed = discord.Embed(title = f"{name.capitalize()} channel message", description=f"```{result[0]}```", color=tv.color), mention_author=False, ephemeral=True)

    async def channel_display(self, ctx: commands.Context, name: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                result = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)

                if (result[0] if result else None) is None:
                    return await ctx.reply(f"{name.capitalize()} channel isn't yet set. \n```/{name} channel set```", mention_author=True, ephemeral=True)

                #channel = discord.Object(int(result[0]))
                channel = ctx.guild.get_channel(result[0])

        return await ctx.reply(embed = discord.Embed(description=f"{name.capitalize()} channel is currently set to {channel.mention}", color=tv.color), mention_author=False, ephemeral=True)

    async def remove(self, ctx: commands.Context, name: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                result = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)

                if (result[0] if result else None) is None:
                    return await ctx.reply(f"{name.capitalize()} channel isn't yet set. \n```/{name} channel set```", mention_author=True, ephemeral=True)

                await conn.execute("UPDATE server_data SET channel_id = NULL WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)
        return await ctx.reply(embed=discord.Embed(description=f"{name.capitalize()} channel has been removed.", color=tv.color), mention_author=False, ephemeral=True)

class Config(BaseCog):

    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        self.config = ConfigFunctions(self.bot)
        self.twitchutils = Twitch(self.bot) 
        self.ac = AutoComplete(self.bot)

    @commands.hybrid_group(invoke_without_command=True,with_app_command=True)
    @commands.bot_has_permissions(manage_channels=True,manage_messages=True)
    @commands.has_permissions(manage_channels=True,manage_messages=True)
    @commands.guild_only()
    async def welcome(self, ctx: commands.Context) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            
            #welcome_help_embed = discord.Embed(title="✨ WELCOME HELP ✨", description = tv.on_member_join_help_welcome_embed_description, color = tv.color)
            #welcome_help_embed.set_footer(text=tv.footer) # help comm comprehensive group desc

            embed = discord.Embed(description="```$welcome [command name]```", color=tv.warn_color)
            return await ctx.reply(embed=embed, ephemeral=True, mention_author=True)
        
    @welcome.group(invoke_without_command=True,with_app_command=True, name="message")
    async def w_message(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            embed = discord.Embed(description="```$welcome message [command name]```", color=tv.warn_color)
            return await ctx.reply(embed=embed, ephemeral=True, mention_author=True)

    @welcome.group(invoke_without_command=True,with_app_command=True, name="channel")
    async def w_channel(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            embed = discord.Embed(description="```$welcome channel [command name]```", color=tv.warn_color)
            return await ctx.reply(embed=embed, ephemeral=True, mention_author=True)

    @w_channel.command(name="set", description = "Sets chosen channel as a welcome channel.")
    async def welcome_channel_set(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = commands.CurrentChannel):
        async with ctx.typing(ephemeral=True):

            return await self.config.add_channel(ctx, "welcome", channel)

    @w_message.command(name="set", description = "You can use this command to set a welcome message.")
    async def welcome_message_set(self, ctx: commands.Context, *, text: str): # ,* (?)
        async with ctx.typing(ephemeral=True):

            return await self.config.add_message(ctx, "welcome", text)

    @w_message.command(name="display", description = "Displays the current welcome message if there is one.")
    async def welcome_message_display(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            return await self.config.message_display(ctx, "welcome")

    @w_channel.command(name="display", description = "Displays the current welcome channel if there is one.")
    async def welcome_channel_display(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            return await self.config.channel_display(ctx, "welcome")

    @w_channel.command(name="remove", description = "Removes the welcome channel.")
    async def welcome_channel_remove(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            return await self.config.remove(ctx, "welcome")

    @welcome.command(name="help", description = "Welcome help.")
    async def help(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            help_welcome_help_embed = discord.Embed(title="✨ COMPREHENSIVE WELCOME/LEAVE HELP ✨", description = tv.on_member_join_help_welcome_help_embed_description, color = tv.color)
            help_welcome_help_embed.set_image(url = '\n https://cdn.discordapp.com/attachments/811285768549957662/989299841895108668/ggggg.png')
            help_welcome_help_embed.set_footer(text=tv.footer)

            return await ctx.reply(embed=help_welcome_help_embed)

    @commands.hybrid_group(invoke_without_command=True,with_app_command=True)
    @commands.bot_has_permissions(manage_channels=True,manage_messages=True)
    @commands.has_permissions(manage_channels=True,manage_messages=True) # REDO PERMS
    @commands.guild_only()
    async def leave(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            #leave_help_embed = discord.Embed(title="✨ LEAVE HELP ✨", description = tv.on_member_leave_help_welcome_embed_description, color = tv.color)
            #leave_help_embed.set_footer(text=tv.footer) #help comm group descript

            embed = discord.Embed(description="```$leave [command name]```", color=tv.warn_color)
            return await ctx.reply(embed=embed, ephemeral=True, mention_author=True)

    @leave.group(invoke_without_command=True,with_app_command=True, name="message")
    async def l_message(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            embed = discord.Embed(description="```$leave message [command name]```", color=tv.warn_color)
            return await ctx.reply(embed=embed, ephemeral=True, mention_author=True)

    @leave.group(invoke_without_command=True,with_app_command=True, name="channel")
    async def l_channel(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            embed = discord.Embed(description="```$leave channel [command name]```", color=tv.warn_color)
            return await ctx.reply(embed=embed, ephemeral=True, mention_author=True)

    @l_channel.command(name="set", description = "Sets chosen channel as a leave channel.")
    async def leave_channel_set(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = commands.CurrentChannel):
        async with ctx.typing(ephemeral=True):
        
            return await self.config.add_channel(ctx, "leave", channel)

    @l_message.command(name="set", description = "You can use this command to set a leave message.")
    async def leave_message_set(self, ctx: commands.Context, *, text: str):
        async with ctx.typing(ephemeral=True):

            return await self.config.add_message(ctx, "leave", text)

    @l_message.command(name="display", description = "Displays the current leave message if there is one.")
    async def leave_message_display(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            return await self.config.message_display(ctx, "leave")

    @l_channel.command(name="display", description = "Displays the current leave channel if there is one.")
    async def leave_channel_display(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            return await self.config.channel_display(ctx, "leave")

    @l_channel.command(name="remove", description = "Removes the leave channel.")
    async def leave_channel_remove(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            return await self.config.remove(ctx, "leave")

    @leave.command(name="help", description = "Leave help.")
    async def l_help(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            help_leave_help_embed = discord.Embed(title="✨ COMPREHENSIVE WELCOME/LEAVE HELP ✨", description = tv.on_member_join_help_welcome_help_embed_description, color = tv.color)
            help_leave_help_embed.set_image(url = '\n https://cdn.discordapp.com/attachments/811285768549957662/989299841895108668/ggggg.png')
            help_leave_help_embed.set_footer(text=tv.footer)

            return await ctx.reply(embed=help_leave_help_embed)
    
    @commands.hybrid_group(invoke_without_command=True, with_app_command=True)
    @commands.bot_has_permissions(manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True, manage_messages=True)
    @commands.guild_only()
    async def twitch(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            embed = discord.Embed(description="```$twitch [command name]```", color=tv.warn_color)
            return await ctx.reply(embed=embed, ephemeral=True, mention_author=True)
    
    @twitch.group(invoke_without_command=True, with_app_command=True, name="message")
    async def t_message(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            embed = discord.Embed(description="```$twitch message [command_name]```", color=tv.warn_color)
            return await ctx.reply(embed=embed, ephemeral=True, mention_author=True)

            #return await ConfigFunctions.add_message(ctx, "twitch", text)

    @twitch.group(invoke_without_command=True,with_app_command=True, name="channel")
    async def t_channel(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):

            embed = discord.Embed(description="```$twitch channel [command_name]```", color=tv.warn_color)
            return await ctx.reply(embed=embed, ephemeral=True, mention_author=True)

            #return await ConfigFunctions.add_channel(ctx, "twitch", channel) # SET CHANNEL WHEN ON invoke_without_command
    
    @t_channel.command(name="set",help="Sets a channel where your twitch notifications will be posted.")
    async def twitch_channel_set(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = commands.CurrentChannel):

        return await self.config.add_channel(ctx, "twitch", channel)

    @t_message.command(name="set", help="Sets a notification message.")
    async def twitch_message_set(self, ctx: commands.Context, *, text: str):

        return await self.config.add_message(ctx, "twitch", text)
    
    @t_message.command(name="display", description = "Displays the current twitch message if there is one.")
    async def twitch_message_display(self, ctx: commands.Context):
        async with ctx.typing():
            return await self.config.message_display(ctx, "twitch")

    @t_channel.command(name="display", description = "Displays the current twitch channel if there is one.")
    async def twitch_channel_display(self, ctx: commands.Context):
        async with ctx.typing():
            return await self.config.channel_display(ctx, "twitch")
    
    @t_channel.command(name="remove", description = "Removes the twitch channel.")
    async def twitch_channel_remove(self, ctx: commands.Context):

        return await self.config.remove(ctx, "twitch") # MAYBE REMOVE CHANNEL_REMOVE COMMS

    @twitch.command(name="add", help="Sets a twitch streamer. The notification shall be posted when the streamer goes online.")
    async def add_twitch_streamer(self, ctx: commands.Context, twitch_streamer_name: str):

        return await self.twitchutils.event_subscription(ctx, "stream.online", twitch_streamer_name)
    
    @twitch.command(name="list", help="Shows the list of streamers guild is subscribed to.")
    async def twitch_streamer_list(self, ctx: commands.Context):

        return await self.twitchutils.guild_twitch_subscriptions(ctx)
    
    @twitch.command(name="remove", help="Removes a twitch subscription.")
    async def twitch_streamer_remove(self, ctx: commands.Context, username: str): # add choice to delete all

        return await self.twitchutils.twitch_unsubscribe_from_streamer(ctx, username)
    
    @twitch_streamer_remove.autocomplete('username')
    async def autocomplete_callback_(self, interaction: discord.Interaction, current: str): # MAKE IT A GLOBAL FUNC
        
        return await self.ac.choice_autocomplete(interaction, current, "twitch_users", "username", "user_id", True)

# RESTRUCTURE GROUP-SUBGROUP CONNECTIONS LIKE: welcome set channel/message | welcome display channel/message (?)
# GLOBAL CHANNEL/MESSAGE DISPLAY THAT WILL SHOW MESSAGE/CHANNEL FOR EACH EVENT_TYPE (?)
# CHANNEL/MESSAGE DISPLAY FOR ALL
# TWITCH (DB) SUBSCRIPTION TO USERS (USER LIST THAT GUILD IS SUBSCRIBED TO) DISPLAY
# twitch.py IN UTILS
# MAYBE A LIST OF EVENTSUBS PER TWITCH USER (LET PEOPLE SUBSCRIBE TO OTHER EVENTS INSTEAD OF JUST SUBSCRIBING TO ON_STREAM)