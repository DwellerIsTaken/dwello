from features.required_permissions.utils.join_leave_func import *
from discord.ext import commands
import text_variables as tv
import discord

class Welcome(commands.Cog, name="welcome"):

    def __init__(self,bot):
        self.bot = bot

    '''@commands.Cog.listener()
    async def on_member_join(self, member):
        await join_leave_event(self.bot, member, "welcome")'''

    @commands.hybrid_group(invoke_without_command=True,with_app_command=True)
    async def welcome(self,ctx):

        welcome_help_embed = discord.Embed(title="✨ WELCOME HELP ✨", description = tv.on_member_join_help_welcome_embed_description, color = tv.color)
        welcome_help_embed.set_footer(text=tv.footer)

        return await ctx.reply(embed=welcome_help_embed)

    @welcome.group(invoke_without_command=True,with_app_command=True)
    async def message(self,ctx):
        embed = discord.Embed(title="Denied", description="Use `$welcome message [command_name]` instead.",color=tv.color)

        return await ctx.reply(embed=embed)

    @welcome.group(invoke_without_command=True,with_app_command=True)
    async def channel(self,ctx):
        embed = discord.Embed(title="Denied", description="Use `$welcome channel [command_name]` instead.",color=tv.color)

        return await ctx.reply(embed=embed)

    @channel.command(name="set", description = "Sets chosen channel as a welcome channel.")
    @commands.has_permissions(manage_channels=True)
    async def channel_set(self, ctx, channel: discord.TextChannel = None):

        await chnl(ctx, "welcome", channel)

    @message.command(name="set", description = "You can use this command to set a welcome message.")
    @commands.has_permissions(manage_channels=True, manage_messages=True)
    async def message_set(self, ctx, *, text: str):

        await msg(ctx, "welcome", text)

    @message.command(name="display", description = "Displays the current welcome message if there is one.")
    @commands.has_permissions(manage_channels=True,manage_messages=True)
    async def welcome_message_display(self, ctx):

        await displ(ctx, "welcome")

    @channel.command(name="display", description = "Displays the current welcome channel if there is one.")
    @commands.has_permissions(manage_channels=True,manage_messages=True)
    async def welcome_channel_display(self, ctx):

        await chnl_displ(ctx, "welcome")

    @channel.command(name="remove", description = "Removes the welcome channel.")
    @commands.has_permissions(manage_channels=True,manage_messages=True)
    async def welcome_channel_remove(self, ctx):

        await rmv(ctx, "welcome")

    @welcome.command(name="help", description = "Welcome help.")
    async def help(self, ctx):

        help_welcome_help_embed = discord.Embed(title="✨ COMPREHENSIVE WELCOME/LEAVE HELP ✨", description = tv.on_member_join_help_welcome_help_embed_description, color = tv.color)
        help_welcome_help_embed.set_image(url = '\n https://cdn.discordapp.com/attachments/811285768549957662/989299841895108668/ggggg.png')
        help_welcome_help_embed.set_footer(text=tv.footer)

        return await ctx.reply(embed=help_welcome_help_embed)

class Leave(commands.Cog, name="Leave"):

    def __init__(self,bot):
        self.bot = bot

    '''@commands.Cog.listener()
    async def on_member_remove(self, member):
        await join_leave_event(self.bot, member, "leave")'''

    @commands.hybrid_group(invoke_without_command=True,with_app_command=True)
    async def leave(self,ctx):

        leave_help_embed = discord.Embed(title="✨ LEAVE HELP ✨", description = tv.on_member_leave_help_welcome_embed_description, color = tv.color)
        leave_help_embed.set_footer(text=tv.footer)

        return await ctx.reply(embed=leave_help_embed)

    @leave.group(invoke_without_command=True,with_app_command=True)
    async def message(self,ctx):
        embed = discord.Embed(title="Denied", description="Use `$leave message [command_name]` instead.",color=tv.color)

        return await ctx.reply(embed=embed)

    @leave.group(invoke_without_command=True,with_app_command=True)
    async def channel(self,ctx):
        embed = discord.Embed(title="Denied", description="Use `$leave channel [command_name]` instead.",color=tv.color)

        return await ctx.reply(embed=embed)

    @channel.command(name="set", description = "Sets chosen channel as a leave channel.")
    @commands.has_permissions(manage_channels=True)
    async def channel_set(self, ctx, channel: discord.TextChannel = None):
        
        await chnl(ctx, "leave", channel)

    @message.command(name="set", description = "You can use this command to set a leave message.")
    @commands.has_permissions(manage_channels=True,manage_messages=True)
    async def message_set(self, ctx, *, text: str):

        await msg(ctx, "leave", text)

    @message.command(name="display", description = "Displays the current leave message if there is one.")
    @commands.has_permissions(manage_channels=True,manage_messages=True)
    async def leave_message_display(self, ctx):

        await displ(ctx, "leave")

    @channel.command(name="display", description = "Displays the current leave channel if there is one.")
    @commands.has_permissions(manage_channels=True,manage_messages=True)
    async def leave_channel_display(self, ctx):

        await chnl_displ(ctx, "leave")

    @channel.command(name="remove", description = "Removes the leave channel.")
    @commands.has_permissions(manage_channels=True,manage_messages=True)
    async def leave_channel_remove(self, ctx):

        await rmv(ctx, "leave")

    @leave.command(name="help", description = "Leave help.")
    async def help(self, ctx):

        help_leave_help_embed = discord.Embed(title="✨ COMPREHENSIVE WELCOME/LEAVE HELP ✨", description = tv.on_member_join_help_welcome_help_embed_description, color = tv.color)
        help_leave_help_embed.set_image(url = '\n https://cdn.discordapp.com/attachments/811285768549957662/989299841895108668/ggggg.png')
        help_leave_help_embed.set_footer(text=tv.footer)

        return await ctx.reply(embed=help_leave_help_embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
    await bot.add_cog(Leave(bot))
