from dotenv import load_dotenv
load_dotenv()

import sys, typing, os
import asyncio, discord, logging
from utils import add_requirements, create_pool, AiohttpWeb, LevellingUtils, Twitch
from text_variables import bot_reply_list
from discord.ext import commands

intents = discord.Intents.all() # Creating a client and setting up its parameters
bot = commands.Bot(command_prefix = '$', chunk_guilds_at_startup = False, activity = discord.Streaming(name = 'Visual Studio Code', url="https://youtu.be/dQw4w9WgXcQ") , intents = intents, help=False, status = discord.Status.do_not_disturb, allowed_mentions=discord.AllowedMentions.none()) #Activity
#bot.remove_command("help")

cogs = {
    "cogs.economy",
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
    
    bot.jobs_data = await bot.db.fetch_job_data() # check it | probably remove

    print('Python version:', sys.version)
    print('{0} is online'.format(bot.user.name))
    print('Version:', discord.__version__)

@bot.command()
@commands.is_owner()
async def list_eventsubs(ctx: commands.Context):

    return bot.tw.event_subscription_list()

@bot.command()
@commands.is_owner()
async def wipe_all_eventsubs(ctx: commands.Context):

    return bot.tw.unsubscribe_from_all_eventsubs()

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
    '''package_list = [asyncio, 
                    discord,
                    matplotlib, 
                    requests, 
                    colorthief, 
                    aiohttp,
                    asyncpg, 
                    setuptools
                    ]
    add_requirements(*package_list)'''

    bot.pool = await create_pool()

    from utils import DB_Operations
    bot.db = DB_Operations(bot)

    await bot.db.create_tables()
    bot.db_data = await bot.db.fetch_data()

    web = AiohttpWeb(bot)
    asyncio.create_task(web.run(port=8081))

    bot.tw = Twitch(bot)

    async with bot:
        for cog in cogs:
            await bot.load_extension(cog)

        logging.basicConfig(level=logging.INFO)

        token = os.getenv('token')
        await bot.start(token) #log_handler=None
asyncio.run(main())

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
#
