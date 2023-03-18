import asyncio, discord, sys, typing, logging, os
from features.levelling.utils import levelling
from text_variables import bot_reply_list
from discord.ext import commands
from utils.fetch_from_db import *
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all() # Creating a client and setting up its parameters
bot = commands.Bot(command_prefix = '$', chunk_guilds_at_startup = False ,activity = discord.Activity(type = discord.ActivityType.playing , name = 'Visual Studio Code') , intents = intents, help=False)
bot.remove_command("help")

cogs = {
    'Required Permissions': ['features.required_permissions.add_comms', 'features.required_permissions.clear_command', 'features.required_permissions.join_leave_comms'],
    'Server Statistics': ['features.required_permissions.utils.server_statistics_loop'],
    'Entertainment': ['features.entertainment.weather'],
    'Moderation': ['features.admin_functions.moder_commands', 'features.admin_functions.warnings'],
    'Debugging': ['proper_debugging.error_handler', 'proper_debugging.on_command_error_event'],
    'Levelling': ['features.levelling.levelling_system'],
    'Economy': ['features.economy.server_eco_comms', 'features.economy.bot_eco_comms'],
    'Events': ['features.bot_events.events'],
    'Other': ['jishaku']
}

# features.economy.utils.economy_loop

@bot.event
async def on_ready():

    bot_reply_list.append(f"**Stop it!** - asked {bot.user.name} calmly.",)
    await bot.tree.sync(guild=discord.Object(690995360411156531))

    bot.jobs_data = await fetch_job_data()

    print('Python version:', sys.version)
    print('{0} is online'.format(bot.user.name))
    print('Version:', discord.__version__)

@bot.command()
@commands.is_owner()
@commands.guild_only()
async def sync(
  ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: typing.Optional[typing.Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

async def main():
    await levelling.create_tables()

    async with bot:
        for category, cogs_ in cogs.items():
            for cog in cogs_:
                await bot.load_extension(cog)

        logging.basicConfig(level=logging.INFO)

        token = os.getenv('token')
        await bot.start(token) #log_handler=None
asyncio.run(main())

# EMPTY SPACE: \u2800
# This command doesn't exist: function (error handler)
# temp_track = (i.split("/")[-1]).split('.')[0]
# Make an info(help) command
# Economy
# Conversational AI ("I don't want to understand you")
# Thanos` irritations
# Global bot.check (error handler)
# await self.bot.get_cog("Economy").start(ctx, member)
# welcome/leave channel disable/remove
# bot_eco & server_eco balance
# twitch/tiktok notifs
# global trading
# global/local leaderboards

'''
bot.global_cd = commands.CooldownMapping.from_cooldown(2, 5, commands.BucketType.member)

@bot.check
async def cooldown_check(ctx):
    
    if str(ctx.invoked_with).lower() == "help":
        return True
    bucket = ctx.bot.global_cd.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()
    if retry_after:
        raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.member)
    return True
    '''