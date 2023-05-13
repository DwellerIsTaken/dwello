from discord.ext.commands import AutoShardedBot
from discord.ext import commands
import discord
import logging
import aiohttp
import asyncio
import asyncpg
import sys
import os
import re

from typing import ClassVar, Optional, Union, Literal, List, Dict, Any
from typing_extensions import Self, override

from utils.web import AiohttpWeb
from .autocomplete import AutoComplete
from utils.context import DwelloContext
from utils.db_operations import DB_Operations
from utils.listeners import ListenersFunctions
from utils.levelling import LevellingUtils
from utils.other import OtherUtils
from utils.twitch import Twitch

initial_extensions = ("jishaku",)

extensions = [
    "cogs.economy",
    "cogs.information",
    "cogs.moderation", 
    "cogs.guild", 
    "cogs.other",
    "utils.debugging.error_handler",
]

def col(color=None, /, *, fmt=0, bg=False):
    base = "\u001b["
    if fmt != 0:
        base += "{fmt};"
    if color is None:
        base += "{color}m"
        color = 0
    else:
        if bg is True:
            base += "4{color}m"
        else:
            base += "3{color}m"

    return base.format(fmt=fmt, color=color)

def get_or_fail(var: str) -> str:
    v = os.getenv(var)
    if v is None:
        raise Exception(f"{var!r} is not set in the .env file")
    return v

class DwelloBase(AutoShardedBot):

    DEFAULT_PREFIXES: ClassVar[List[str]] = ["dw.", "dwello.", "Dwello."]

    user: discord.ClientUser

    logger = logging.getLogger("logging")
    _ext_log = logging.getLogger("extensions")

    def __init__(self: Self, pool: asyncpg.Pool, session: aiohttp.ClientSession, *args: Any, **kwargs: Any) -> None:
        intents = discord.Intents.all()
        intents.typing = False

        super().__init__(
            intents=intents,
            command_prefix=self.get_prefix,
            case_insensitive=True,
            activity=discord.Streaming(name="Visual Studio Code", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            allowed_mentions=discord.AllowedMentions(),
            strip_after_prefix=True,
            chunk_guilds_at_startup=False,
            owner_ids=[548846436570234880],
            *args,
            **kwargs,
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

    @override
    async def setup_hook(self: Self) -> None:

        for ext in initial_extensions:
            await self.load_extension(ext, _raise=False)

        for ext in extensions:
            await self.load_extension(ext, _raise=False)

        self.tables = await self.db.create_tables()
        self.db_data = await self.db.fetch_table_data()
        asyncio.create_task(self.web.run(port=8081))

        await self.tree.sync(guild=discord.Object(822162578653577336))

    async def on_ready(self: Self):
        #bot.jobs_data = await bot.db.fetch_job_data() # check it | probably remove

        self.logger.info(f"{col()}Python Version: {sys.version} {col()}")
        self.logger.info(f"{col()}Discord Version: {discord.__version__} {col()}")
        self.logger.info(f"{col(2, bg=True)}Logged in as {self.user} {col()}")
    @override
    async def get_prefix(self: Self, message: discord.Message, /) -> List[str]:

        prefixes: List[str] = self.DEFAULT_PREFIXES.copy()

        #Disable default prefix when custom enabled? add checks to make sure custom prefix isnt the default one. make sure you cant remove prefix if default one is disabled
        for prefix in self.db_data['prefixes']:
            if prefix['guild_id'] == message.guild.id:
                prefixes.append(prefix['prefix'])

        return commands.when_mentioned_or(*prefixes)(self, message)

    @override
    async def get_context(self: Self, message, *, cls: Any = DwelloContext):
        return await super().get_context(message, cls=cls)
    
    @override
    async def load_extension(self: Self, name: str, *, package: Optional[str] = None, _raise: bool = True) -> None:
        self._ext_log.info(f"{col(7)}Attempting to load {col(7, fmt=4)}{name}{col()}")
        try:
            await super().load_extension(name, package=package)
            self._ext_log.info(f"{col(2)}Loaded extension {col(2, fmt=4)}{name}{col()}")

        except Exception as e:
            self._ext_log.error(f"Failed to load extension {name}", exc_info=e)
            if _raise:
                raise e

    @override
    async def unload_extension(self: Self, name: str, *, package: Optional[str] = None, _raise: bool = True) -> None:
        self._ext_log.info(f"{col(7)}Attempting to unload extension {col(7, fmt=4)}{name}{col()}")
        try:
            await super().unload_extension(name, package=package)
            self._ext_log.info(f"{col(2)}Unloaded extension {col(2, fmt=4)}{name}{col()}")

        except Exception as e:
            self._ext_log.error(f"Failed to unload extension {name}", exc_info=e)
            if _raise:
                raise e

    @override
    async def reload_extension(self: Self, name: str, *, package: Optional[str] = None, _raise: bool = True) -> None:
        self._ext_log.info(f"{col(7)}Attempting to reload extension {col(7, fmt=4)}{name}{col()}")
        try:
            await super().reload_extension(name, package=package)
            self._ext_log.info(f"{col(2)}Reloaded extension {col(2, fmt=4)}{name}{col()}")

        except Exception as e:
            self._ext_log.error(f"Failed to reload extension {name}", exc_info=e)
            if _raise:
                raise e