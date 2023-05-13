from dotenv import load_dotenv
load_dotenv()

import aiohttp
import asyncpg
import asyncio

import logging

from utils.context import DwelloContext
from utils.bases.bot_base import DwelloBase, get_or_fail

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] - %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S %Z%z',  # CET timezone format
)

class Dwello(DwelloBase):
    """Bot definition class."""

if __name__ == "__main__":

    credentials = {
        "user": get_or_fail('pg_username'),
        "password": get_or_fail('pg_password'),
        "database": get_or_fail('pg_name'),
        "host": get_or_fail('pg_host'),
        "port": get_or_fail('pg_port'),
    }

    async def main(): # ADD SSH KEY CONNECTION
        async with asyncpg.create_pool(**credentials) as pool, aiohttp.ClientSession() as session, Dwello(pool, session) as bot:

            token = get_or_fail('token')
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
# custom guild module: https://github.com/irregularunit/bot
#
# guild:= discord.get(guild) | non-existend example
# TYPE_CHECKING where modules used for type-checking
# from typing_extensions import Self
