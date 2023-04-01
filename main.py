from dotenv import load_dotenv
load_dotenv()

import sys, typing, os
import asyncio, discord, logging, matplotlib, requests, colorthief, aiohttp, asyncpg, setuptools, re
from utils import add_requirements
from text_variables import bot_reply_list
from discord.ext import commands
from utils.db_operations import DB_Operations
from utils.levelling import LevellingUtils

intents = discord.Intents.all() # Creating a client and setting up its parameters
bot = commands.Bot(command_prefix = '$', chunk_guilds_at_startup = False, activity = discord.Activity(type = discord.ActivityType.playing , name = 'Visual Studio Code') , intents = intents, help=False, status = discord.Status.do_not_disturb)
bot.remove_command("help")

cogs = {
    "cogs.entertainment",
    "cogs.information",
    "cogs.moderation", 
    "cogs.guild", 
    "cogs.other",
    "utils.debugging.error_handler",
    "jishaku"
}

# features.economy.utils.economy_loop

@bot.event
async def on_ready():

    bot_reply_list.append(f"**Stop it!** - asked {bot.user.name} calmly.",)
    await bot.tree.sync(guild=discord.Object(690995360411156531))
    
    bot.jobs_data = await bot.db.fetch_job_data()

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
    package_list = [asyncio, 
                    discord,
                    matplotlib, 
                    requests, 
                    colorthief, 
                    aiohttp,
                    asyncpg, 
                    setuptools,
                    re
                    ]
    add_requirements(*package_list)

    bot.db = DB_Operations(bot)
    bot.pool = await DB_Operations(bot).create_pool()

    #bot.lvl = LevellingUtils(bot)
    await LevellingUtils(bot).create_tables()

    async with bot:
        #for category, cogs_ in cogs.items():
        for cog in cogs:
            await bot.load_extension(cog)

        logging.basicConfig(level=logging.INFO)

        token = os.getenv('token')
        await bot.start(token) #log_handler=None
asyncio.run(main())

# EMPTY SPACE: \u2800
# This command doesn't exist: function (error handler)
# Make an info(help) command
# REDO Economy
# Conversational AI ("I don't want to understand you") (wtf?)
# Bot`s irritations
# Global bot.check (error handler)
# welcome/leave channel disable/remove
# bot_eco & server_eco balance
# twitch/tiktok notifs
# global trading
# global/local leaderboards
# make cooldowns
# PUT ALL ERROR HANDLER IN ONE FILE | fucking organize it already
# do subclassing (subcogging)
# from easypil to PIL
# cannot install easypil
