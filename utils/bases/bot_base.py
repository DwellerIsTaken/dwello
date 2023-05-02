from discord.ext.commands import AutoShardedBot
from discord.ext import commands
import discord
import aiohttp
import asyncio
import asyncpg
import sys

from typing import Optional, Union, Literal

from utils.web import AiohttpWeb
from .autocomplete import AutoComplete
from utils.context import DwelloContext
from utils.db_operations import DB_Operations
from utils.listeners import ListenersFunctions
from utils.levelling import LevellingUtils
from utils.other import OtherUtils
from utils.twitch import Twitch

class DwelloBase(AutoShardedBot):

    def __init__(self, pool: asyncpg.Pool, session: aiohttp.ClientSession) -> None:
        intents = discord.Intents.all()
        intents.typing = False

        super().__init__(
            intents=intents,
            command_prefix='$',
            case_insensitive=True,
            activity=discord.Streaming(name="Visual Studio Code", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            allowed_mentions=discord.AllowedMentions.none(),
            strip_after_prefix=True,
            chunk_guilds_at_startup=False,
        )

        self.pool = pool
        self.session = session

        self.levelling: LevellingUtils = LevellingUtils(self)
        self.autocomplete: AutoComplete = AutoComplete(self)
        self.otherutils: OtherUtils = OtherUtils(self)
        self.db: DB_Operations = DB_Operations(self)
        self.listeners = ListenersFunctions(self)
        self.web: AiohttpWeb = AiohttpWeb(self)
        self.twitch: Twitch = Twitch(self)

        asyncio.create_task(self.web.run(port=8081))

    async def on_ready(self):

        await self.tree.sync(guild=discord.Object(690995360411156531))

        await self.db.create_tables()
        self.db_data = await self.db.fetch_data()
        
        #bot.jobs_data = await bot.db.fetch_job_data() # check it | probably remove

        print('Python version:', sys.version)
        print('{0} is online'.format(self.user.name))
        print('Version:', discord.__version__)

    async def get_context(self, message, *, cls = DwelloContext):
        return await super().get_context(message, cls=cls)