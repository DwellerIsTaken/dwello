from dotenv import load_dotenv
load_dotenv()

import aiohttp
import asyncpg
import sys, typing, os
import asyncio, discord, logging
from discord.ext import commands

from utils.context import DwelloContext
from utils.bases.bot_base import DwelloBase

cogs = {
    "cogs.economy",
    "cogs.information",
    "cogs.moderation", 
    "cogs.guild", 
    "cogs.other",
    "utils.debugging.error_handler",
    "jishaku"
}

class Dwello(DwelloBase):
    """Bot definition class."""

if __name__ == "__main__":

    credentials = {
        "user": f"{os.getenv('pg_username')}",
        "password": f"{os.getenv('pg_password')}",
        "database": f"{os.getenv('pg_name')}",
        "host": f"{os.getenv('pg_host')}",
        "port": f"{os.getenv('pg_port')}",
    }

    async def main(): # ADD SSH KEY CONNECTION
        async with asyncpg.create_pool(**credentials) as pool, aiohttp.ClientSession() as session, Dwello(pool, session) as bot:

            for cog in cogs:
                await bot.load_extension(cog)

            logging.basicConfig(level=logging.INFO)

            token = os.getenv('token')
            await bot.start(token)

    asyncio.run(main())

"""async def main():
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

    async with bot:
        for cog in cogs:
            await bot.load_extension(cog)

        logging.basicConfig(level=logging.INFO)

        token = os.getenv('token')
        await bot.start(token) #log_handler=None
asyncio.run(main())"""

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
# from easypil to PIL
#
