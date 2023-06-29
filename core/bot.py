from __future__ import annotations

import asyncio
import datetime
import os
from typing import Any

import aiohttp
import asyncpg
import discord
from discord.ext import commands

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
else:
    try:
        import uvloop
    except ImportError:
        pass
    else:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from ._utils import (
    ENV,
    LOADABLE_EXTENSIONS,
    AiohttpWeb,
    AutoComplete,
    ContextManager,
    DataBaseOperations,
    LevellingUtils,
    ListenersFunctions,
    OtherUtils,
    Twitch,
)
from .context import Context


def blacklist_check(ctx: Context) -> bool:
    return not ctx.bot.is_blacklisted(ctx.author.id)


class Bot(commands.AutoShardedBot):
    DEFAULT_PREFIXES = ["dw.", "dwello."]
    http_session: aiohttp.ClientSession

    def __init__(self, pool: asyncpg.Pool, **kwargs):
        super().__init__(
            command_prefix=self.get_prefix,  # type: ignore
            strip_after_prefix=True,
            intents=discord.Intents.all(),
            case_insensitive=True,
            activity=discord.Streaming(
                name="Visual Studio Code",
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            ),
            allowed_mentions=discord.AllowedMentions.all(),
            chunk_guilds_at_startup=False,
            owner_ids={548846436570234880},
        )

        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.pool = pool

        self.reply_count: int = 0
        self._was_ready = False

        self.blacklisted_users: dict[int, str] = {}
        self.bypass_cooldown_users: list[int] = []

        self.autocomplete = AutoComplete(self)
        self.listeners = ListenersFunctions(self)
        self.levelling = LevellingUtils(self)
        self.db = DataBaseOperations(self)
        self.otherutils = OtherUtils(self)
        self.web = AiohttpWeb(self)

    async def setup_hook(self) -> None:
        for ext in LOADABLE_EXTENSIONS:
            try:
                await self.load_extension(ext)
            except Exception:
                pass

        self.tables = await self.db.create_tables()
        self.db_data = await self.db.fetch_table_data()
        records: list[Any] = await self.pool.fetch("SELECT guild_id, array_agg(prefix) FROM prefixes GROUP BY guild_id")
        self.guild_prefixes = dict(records)

        blacklist: list[asyncpg.Record] = await self.pool.fetch("SELECT * FROM blacklist")
        self.twitch = await Twitch.create_access_token(self)
        for record in blacklist:
            self.blacklisted_users[record["user_id"]] = record["reason"]

        self.add_check(blacklist_check)

        asyncio.create_task(self.web.run(port=8081))

    def safe_connection(self, *, timeout: float = 10.0) -> ContextManager:
        return ContextManager(self, timeout=timeout)

    def is_blacklisted(self, user_id: int) -> bool:
        return user_id in self.blacklisted_users  # rewrite member and user and put it there as a property

    async def get_prefix(self, message: discord.Message) -> list[str]:
        if guild_prefixes := self.guild_prefixes.get(message.guild.id):  # type: ignore
            prefixes = []
            prefixes.extend(guild_prefixes)
        else:
            prefixes = self.DEFAULT_PREFIXES

        return commands.when_mentioned_or(*prefixes)(self, message)

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} ({self.user.id})")  # type: ignore
        self._was_ready = True

        if not hasattr(self, "uptime"):
            self.uptime = datetime.datetime.now(datetime.timezone.utc)


async def runner():
    credentials = {
        "user": ENV["pg_username"],
        "password": ENV["pg_password"],
        "database": ENV["pg_name"],
        "host": ENV["pg_host"],
        "port": ENV["pg_port"],
    }

    async with asyncpg.create_pool(**credentials) as pool, aiohttp.ClientSession() as session, Bot(  # type: ignore
        pool
    ) as bot:
        bot.http_session = session
        await bot.start(ENV["token"])  # type: ignore


def run():
    asyncio.run(runner())
