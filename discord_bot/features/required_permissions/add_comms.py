from features.required_permissions.utils.add_funcs import *
from discord.ext import commands
import text_variables as tv
import discord 

class Server_Statistics(commands.Cog, name = "Server_Statistics"):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="add",description="A group that allows you to add some items to the server.",invoke_without_command = True,with_app_command=True)
    async def add(self,ctx):

        return await ctx.reply("Please provide an argument! ```$add [subgroup] [command]```") # content | server_stats_help_embed

    @add.group(invoke_without_command = True,with_app_command=True)
    async def counter(self, ctx):

        return await ctx.reply("Please provide an argument! ```$add counter [counter type]```")

    @add.group(invoke_without_command = True,with_app_command=True)
    async def twitch(self, ctx):

        return await ctx.reply("Please provide an argument! ```$add twitch [command name]```")

    @twitch.command(name="channel",help="Sets a channel where your twitch notifications will be posted.")
    @commands.has_permissions(administrator=True)
    async def twitch_channel(self, ctx, channel: discord.TextChannel = None):

        await add_twitch_chnl(ctx, channel)

    @twitch.command(name="streamer", help="Sets a twitch streamer. The notification shall be posted when the streamer goes online.")
    @commands.has_permissions(administrator=True)
    async def twitch_streamer(self, ctx, twitch_streamer_name: str):

        pass

    @counter.command(name='all', help="Creates a [voice] channel with all-user (bots included) count on this server.")
    @commands.has_permissions(manage_channels=True)
    async def all(self, ctx):

        await counter_func(ctx, "all_counter_channel_id")

    @counter.command(name='members', help="Creating a [voice] channel with all-member count on this specific server.")
    @commands.has_permissions(manage_channels=True)
    async def members(self,ctx):
        
        await counter_func(ctx, "members_counter_channel_id")

    @counter.command(name='bots', help="Creating a [voice] channel with all-bot count on this specific server.")
    @commands.has_permissions(manage_channels=True)
    async def bots(self,ctx):
        
        await counter_func(ctx, "bots_counter_channel_id")

    @counter.command(name='category', help="Creates a category where your counter(s) will be stored.")
    @commands.has_guild_permissions(manage_channels=True)
    async def category(self,ctx):

        category = await create_counter_category(ctx)
        await move_channel(ctx, category)

    @counter.command(name='list', help="Shows a list of counters you can create.")
    async def list(self,ctx):

        help_embed = discord.Embed(title = ":bar_chart: AVAILABLE COUNTERS :bar_chart:", description =  tv.server_statistics_list_help_embed_description, color = tv.color).set_footer(text=tv.footer)

        return await ctx.reply(embed = help_embed)

async def setup(bot):
  await bot.add_cog(Server_Statistics(bot))