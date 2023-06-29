from __future__ import annotations

import asyncio
import datetime
import logging
import os
import sys
from typing import Any, ClassVar, Dict, List, Optional

import aiohttp
import asyncpg
import discord
from discord.ext import commands
from discord.ext.commands import AutoShardedBot
from typing_extensions import Self, override

from utils.context import DwelloContext
from utils.db_operations import DB_Operations
from utils.levelling import LevellingUtils
from utils.listeners import ListenersFunctions
from utils.other import OtherUtils
from utils.twitch import Twitch
from utils.web import AiohttpWeb

from .autocomplete import AutoComplete

initial_extensions = ("jishaku",)

extensions = [
    "cogs.economy",
    "cogs.entertainment",
    "cogs.information",
    "cogs.moderation",
    "cogs.information.help",
    "cogs.guild",
    "cogs.other",
    "utils.error",
]


def col(color=None, /, *, fmt=0, bg=False):
    base = "\u001b["
    if fmt != 0:
        base += "{fmt};"
    if color is None:
        base += "{color}m"
        color = 0
    else:
        base += "4{color}m" if bg is True else "3{color}m"
    return base.format(fmt=fmt, color=color)


def get_or_fail(var: str) -> str:
    v = os.getenv(var)
    if v is None:
        raise Exception(f"{var!r} is not set in the .env file")
    return v


# <---CHECKS--->


def blacklist_check(ctx: DwelloContext) -> bool:
    return not ctx.bot.is_blacklisted(ctx.author.id)


class DwelloBase(AutoShardedBot):
    DEFAULT_PREFIXES: ClassVar[List[str]] = ["dw.", "Dw.", "dwello.", "Dwello."]

    user: discord.ClientUser

    logger = logging.getLogger("logging")
    _ext_log = logging.getLogger("extensions")

    def __init__(
        self: Self,
        pool: asyncpg.Pool,
        session: aiohttp.ClientSession,
        /,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        intents = discord.Intents.all()
        intents.typing = False

        super().__init__(
            intents=intents,
            command_prefix=self.get_prefix,
            case_insensitive=True,
            activity=discord.Streaming(
                name="Visual Studio Code",
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            ),
            allowed_mentions=discord.AllowedMentions(),
            strip_after_prefix=True,
            chunk_guilds_at_startup=False,
            owner_ids=[548846436570234880],
            *args,
            **kwargs,
        )

        self.pool = pool
        self.session = session

        self.reply_count: int = 0

        self.blacklisted_users: Dict[int, str] = {}
        self.bypass_cooldown_users: List[int] = []

        self.launch_time: datetime.datetime = datetime.datetime.now(
            datetime.timezone.utc
        )

        self.cooldown: commands.CooldownMapping[
            discord.Message
        ] = commands.CooldownMapping.from_cooldown(
            1,
            1.5,
            commands.BucketType.member,
        )

        self.levelling: LevellingUtils = LevellingUtils(self)
        self.autocomplete: AutoComplete = AutoComplete(self)
        self.otherutils: OtherUtils = OtherUtils(self)
        self.db: DB_Operations = DB_Operations(self)
        self.listeners = ListenersFunctions(self)
        self.web: AiohttpWeb = AiohttpWeb(
            self
        )  # redo all -> maybe class methods instead
        # self.twitch: Twitch = Twitch(self)

    @override
    async def setup_hook(self: Self) -> None:
        for ext in initial_extensions:
            await self.load_extension(ext, _raise=False)

        for ext in extensions:
            await self.load_extension(ext, _raise=False)

        self.twitch = await Twitch.create_access_token(self)

        self.tables = await self.db.create_tables()
        self.db_data = await self.db.fetch_table_data()

        records: List[Any] = await self.pool.fetch(
            "SELECT guild_id, array_agg(prefix) FROM prefixes GROUP BY guild_id"
        )
        self.guild_prefixes = dict(records)

        blacklist: List[asyncpg.Record] = await self.pool.fetch(
            "SELECT * FROM blacklist"
        )
        for record in blacklist:
            self.blacklisted_users[record["user_id"]] = record["reason"]

        self.add_check(blacklist_check)

        asyncio.create_task(self.web.run(port=8081))

        await self.tree.sync(guild=discord.Object(822162578653577336))

    async def on_ready(self: Self):
        # bot.jobs_data = await bot.db.fetch_job_data() # check it | probably remove

        self.logger.info(f"{col()}Python Version: {sys.version} {col()}")
        self.logger.info(f"{col()}Discord Version: {discord.__version__} {col()}")
        self.logger.info(f"{col(2, bg=True)}Logged in as {self.user} {col()}")

    @override
    async def get_prefix(self: Self, message: discord.Message, /) -> List[str]:
        prefixes: List[str] = self.DEFAULT_PREFIXES.copy()
        if guild_prefixes := self.guild_prefixes.get(message.guild.id):
            prefixes.extend(guild_prefixes)

        # Disable default prefix when custom enabled? add checks to make sure custom prefix isnt the default one. make sure you cant remove prefix if default one is disabled

        return commands.when_mentioned_or(*prefixes)(self, message)

    @override
    async def get_context(self: Self, message, *, cls: Any = DwelloContext):
        return await super().get_context(message, cls=cls)

    @override
    async def load_extension(
        self: Self, name: str, *, package: Optional[str] = None, _raise: bool = True
    ) -> None:
        self._ext_log.info(f"{col(7)}Attempting to load {col(7, fmt=4)}{name}{col()}")
        try:
            await super().load_extension(name, package=package)
            self._ext_log.info(f"{col(2)}Loaded extension {col(2, fmt=4)}{name}{col()}")

        except Exception as e:
            self._ext_log.error(f"Failed to load extension {name}", exc_info=e)
            if _raise:
                raise e

    @override
    async def unload_extension(
        self: Self, name: str, *, package: Optional[str] = None, _raise: bool = True
    ) -> None:
        self._ext_log.info(
            f"{col(7)}Attempting to unload extension {col(7, fmt=4)}{name}{col()}"
        )
        try:
            await super().unload_extension(name, package=package)
            self._ext_log.info(
                f"{col(2)}Unloaded extension {col(2, fmt=4)}{name}{col()}"
            )

        except Exception as e:
            self._ext_log.error(f"Failed to unload extension {name}", exc_info=e)
            if _raise:
                raise e

    @override
    async def reload_extension(
        self: Self, name: str, *, package: Optional[str] = None, _raise: bool = True
    ) -> None:
        self._ext_log.info(
            f"{col(7)}Attempting to reload extension {col(7, fmt=4)}{name}{col()}"
        )
        try:
            await super().reload_extension(name, package=package)
            self._ext_log.info(
                f"{col(2)}Reloaded extension {col(2, fmt=4)}{name}{col()}"
            )

        except Exception as e:
            self._ext_log.error(f"Failed to reload extension {name}", exc_info=e)
            if _raise:
                raise e

    def is_blacklisted(self: Self, user_id: int) -> bool:
        return (
            user_id in self.blacklisted_users
        )  # rewrite member and user and put it there as a property