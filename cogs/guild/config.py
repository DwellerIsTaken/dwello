#from features.required_permissions.utils.join_leave_func import *
from discord.ext import commands
from contextlib import suppress
from string import Template
import text_variables as tv
import discord, os

from typing import Optional, Literal
from utils import event_subscription

class ConfigFunctions():

    def __init__(self, bot):
        self.bot = bot

    async def add_message(self, ctx: commands.Context, name: str, text: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                record = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)

                if (record[0] if record else None) is None:
                    return await ctx.reply(f"Please use `${name} channel` first.") # adjust based on group/subgroup

                if not text:
                    return await ctx.reply(f"Please enter the {name} message, if you want to be able to use this command properly!")

                result = await conn.fetchrow("SELECT message_text FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)

                '''if result:
                    await conn.execute("UPDATE server_data SET message_text = $1 WHERE guild_id = $2 AND event_type = $3", text, ctx.guild.id, name)
                    w = 'updated'

                else:
                    await conn.execute("INSERT INTO server_data (guild_id, message_text, event_type) VALUES($1,$2,$3)", ctx.guild.id, text, name)
                    w = 'set' # create all the event_types when bot enters the guild'''

                await conn.execute("UPDATE server_data SET message_text = $1, event_type = COALESCE(event_type, $2) WHERE guild_id = $3 AND COALESCE(event_type, $2) = $2", text, name, ctx.guild.id)
                string = f"The {name} message has been {'set' if not result[0] else 'updated'} to: ```{text}```"

        return await ctx.reply(embed = discord.Embed(description=string, color = tv.color), mention_author = False, ephemeral=True)

    '''async def chnl(self, ctx: commands.Context, name: Optional[str], channel: Optional[discord.TextChannel] = commands.CurrentChannel) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                result = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)
                
                w = '*'

                if result:
                    if str(result[0]) == str(channel.id): # ?
                        return await ctx.reply(f"The leave channel has already been set to this channel!")
                    
                    else:
                        await conn.execute("UPDATE server_data SET channel_id = $1 WHERE guild_id = $2 AND event_type = $3", channel.id, ctx.guild.id, name)
                        w = 'updated'
                    
                else: # probably remove
                    await conn.execute("INSERT INTO server_data (guild_id, channel_id, event_type) VALUES($1,$2,$3)", ctx.guild.id, channel.id, name)
                    w = 'set'
        
        return await ctx.reply(f"The {name} channel has been {w} to {channel.mention}.", mention_author=False, ephemeral=True)'''
    
    async def add_channel(self, ctx: commands.Context, name: str, channel: Optional[discord.TextChannel] = commands.CurrentChannel) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                result = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)

                string = f"The channel has been {'set' if not result[0] else 'updated'} to {channel.mention}"

                if (result[0] if result else None) == channel.id:
                    return await ctx.reply("The twitch channel has already been set to this channel!", mention_author = True, ephemeral = True)

                await conn.execute("UPDATE server_data SET channel_id = $1, event_type = COALESCE(event_type, $2) WHERE guild_id = $3 AND COALESCE(event_type, $2) = $2", channel.id, name, ctx.guild.id)

        return await ctx.reply(embed = discord.Embed(description=string, color = tv.color), mention_author = False, ephemeral=True)

    async def message_display(self, ctx: commands.Context, name: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                if name != "welcome" and name != "leave": # ?
                    raise TypeError

                result = await conn.fetchrow("SELECT message_text FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)

                if (result[0] if result else None) is None:
                    return await ctx.reply(f"The {name} message isn't yet set. Consider using `${name} message`.")

        return await ctx.reply(f"The {name} message is:```{result[0]}```", mention_author=False, ephemeral=True)

    async def channel_display(self, ctx: commands.Context, name: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                result = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)

                if (result[0] if result else None) is None:
                    return await ctx.reply(f"The {name} channel isn't yet set. Consider using `${name} channel`.")

                #channel = discord.Object(int(result[0]))
                channel = ctx.guild.get_channel(result[0])

        return await ctx.reply(f"The {name} channel is currently set to {channel.mention}", mention_author=False, ephemeral=True)

    async def remove(self, ctx: commands.Context, name: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                await conn.execute("UPDATE server_data SET channel_id = NULL WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, name)
        return await ctx.reply(f"The {name} channel has been removed.", mention_author=False, ephemeral=True)

class Config(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = ConfigFunctions(bot)

    @commands.hybrid_group(invoke_without_command=True,with_app_command=True)
    @commands.bot_has_permissions(manage_channels=True,manage_messages=True)
    @commands.has_permissions(manage_channels=True,manage_messages=True)
    @commands.guild_only()
    async def welcome(self, ctx: commands.Context) -> Optional[discord.Message]:

        welcome_help_embed = discord.Embed(title="✨ WELCOME HELP ✨", description = tv.on_member_join_help_welcome_embed_description, color = tv.color)
        welcome_help_embed.set_footer(text=tv.footer)

        return await ctx.reply(embed=welcome_help_embed)

    @welcome.group(invoke_without_command=True,with_app_command=True, name="message")
    async def w_message(self, ctx: commands.Context):
        embed = discord.Embed(title="Denied", description="Use `$welcome message [command_name]` instead.",color=tv.color)

        return await ctx.reply(embed=embed)

    @welcome.group(invoke_without_command=True,with_app_command=True, name="channel")
    async def w_channel(self, ctx: commands.Context):
        embed = discord.Embed(title="Denied", description="Use `$welcome channel [command_name]` instead.",color=tv.color)

        return await ctx.reply(embed=embed)

    @w_channel.command(name="set", description = "Sets chosen channel as a welcome channel.")
    async def welcome_channel_set(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = commands.CurrentChannel):

        return await self.config.add_channel(ctx, "welcome", channel)

    @w_message.command(name="set", description = "You can use this command to set a welcome message.")
    async def welcome_message_set(self, ctx: commands.Context, *, text: str): # ,* (?)

        return await self.config.add_message(ctx, "welcome", text)

    @w_message.command(name="display", description = "Displays the current welcome message if there is one.")
    async def welcome_message_display(self, ctx: commands.Context):
        async with ctx.typing():
            return await self.config.message_display(ctx, "welcome")

    @w_channel.command(name="display", description = "Displays the current welcome channel if there is one.")
    async def welcome_channel_display(self, ctx: commands.Context):
        async with ctx.typing():
            return await self.config.channel_display(ctx, "welcome")

    @w_channel.command(name="remove", description = "Removes the welcome channel.")
    async def welcome_channel_remove(self, ctx: commands.Context):

        return await self.config.remove(ctx, "welcome")

    @welcome.command(name="help", description = "Welcome help.")
    async def help(self, ctx: commands.Context):

        help_welcome_help_embed = discord.Embed(title="✨ COMPREHENSIVE WELCOME/LEAVE HELP ✨", description = tv.on_member_join_help_welcome_help_embed_description, color = tv.color)
        help_welcome_help_embed.set_image(url = '\n https://cdn.discordapp.com/attachments/811285768549957662/989299841895108668/ggggg.png')
        help_welcome_help_embed.set_footer(text=tv.footer)

        return await ctx.reply(embed=help_welcome_help_embed)

    @commands.hybrid_group(invoke_without_command=True,with_app_command=True)
    @commands.bot_has_permissions(manage_channels=True,manage_messages=True)
    @commands.has_permissions(manage_channels=True,manage_messages=True) # REDO PERMS
    @commands.guild_only()
    async def leave(self, ctx: commands.Context):

        leave_help_embed = discord.Embed(title="✨ LEAVE HELP ✨", description = tv.on_member_leave_help_welcome_embed_description, color = tv.color)
        leave_help_embed.set_footer(text=tv.footer)

        return await ctx.reply(embed=leave_help_embed)

    @leave.group(invoke_without_command=True,with_app_command=True, name="message")
    async def l_message(self, ctx: commands.Context):
        embed = discord.Embed(title="Denied", description="Use `$leave message [command_name]` instead.",color=tv.color)

        return await ctx.reply(embed=embed)

    @leave.group(invoke_without_command=True,with_app_command=True, name="channel")
    async def l_channel(self, ctx: commands.Context):
        embed = discord.Embed(title="Denied", description="Use `$leave channel [command_name]` instead.",color=tv.color)

        return await ctx.reply(embed=embed)

    @l_channel.command(name="set", description = "Sets chosen channel as a leave channel.")
    async def leave_channel_set(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = commands.CurrentChannel):
        
        return await self.config.add_channel(ctx, "leave", channel)

    @l_message.command(name="set", description = "You can use this command to set a leave message.")
    async def leave_message_set(self, ctx: commands.Context, *, text: str):

        return await self.config.add_message(ctx, "leave", text)

    @l_message.command(name="display", description = "Displays the current leave message if there is one.")
    async def leave_message_display(self, ctx: commands.Context):
        async with ctx.typing():
            return await self.config.message_display(ctx, "leave")

    @l_channel.command(name="display", description = "Displays the current leave channel if there is one.")
    async def leave_channel_display(self, ctx: commands.Context):
        async with ctx.typing():
            return await self.config.channel_display(ctx, "leave")

    @l_channel.command(name="remove", description = "Removes the leave channel.")
    async def leave_channel_remove(self, ctx: commands.Context):

        return await self.config.remove(ctx, "leave")

    @leave.command(name="help", description = "Leave help.")
    async def l_help(self, ctx: commands.Context):

        help_leave_help_embed = discord.Embed(title="✨ COMPREHENSIVE WELCOME/LEAVE HELP ✨", description = tv.on_member_join_help_welcome_help_embed_description, color = tv.color)
        help_leave_help_embed.set_image(url = '\n https://cdn.discordapp.com/attachments/811285768549957662/989299841895108668/ggggg.png')
        help_leave_help_embed.set_footer(text=tv.footer)

        return await ctx.reply(embed=help_leave_help_embed)
    
    @commands.hybrid_group(invoke_without_command=True, with_app_command=True)
    @commands.bot_has_permissions(manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True, manage_messages=True)
    @commands.guild_only()
    async def twitch(self, ctx: commands.Context):

        return await ctx.reply("Please provide an argument! ```$add twitch [command name]```")
    
    @twitch.group(invoke_without_command=True,with_app_command=True, name="message")
    async def t_message(self, ctx: commands.Context):

        embed = discord.Embed(title="Denied", description="Use `$leave message [command_name]` instead.",color=tv.color)
        return await ctx.reply(embed=embed)

        #return await ConfigFunctions.add_message(ctx, "twitch", text)

    @twitch.group(invoke_without_command=True,with_app_command=True, name="channel")
    async def t_channel(self, ctx: commands.Context):

        embed = discord.Embed(title="Denied", description="Use `$leave channel [command_name]` instead.",color=tv.color)
        return await ctx.reply(embed=embed)

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

        return await event_subscription(ctx, "stream.online", twitch_streamer_name)

# RESTRUCTURE GROUP-SUBGROUP CONNECTIONS LIKE: welcome set channel/message | welcome display channel/message (?)
# GLOBAL CHANNEL/MESSAGE DISPLAY THAT WILL SHOW MESSAGE/CHANNEL FOR EACH EVENT_TYPE (?)
# CHANNEL/MESSAGE DISPLAY FOR ALL
# TWITCH (DB) SUBSCRIPTION TO USERS (USER LIST THAT GUILD IS SUBSCRIBED TO) DISPLAY
# twitch.py IN UTILS
# MAYBE A LIST OF EVENTSUBS PER TWITCH USER (LET PEOPLE SUBSCRIBE TO OTHER EVENTS INSTEAD OF JUST SUBSCRIBING TO ON_STREAM)