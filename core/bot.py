from __future__ import annotations

import asyncio
import datetime
import logging
import os
import re
import sys
from typing import TYPE_CHECKING, Any, ClassVar, Generic, List, Optional, Set, Tuple, TypeVar, Union, overload  # noqa: F401

import aiohttp
import asyncpg
import discord
from discord import app_commands
from discord.ext import commands
from typing_extensions import override

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
else:
    try:
        import uvloop # type: ignore
    except ImportError:
        pass
    else:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from ._utils import ENV, AiohttpWeb, AutoComplete, DataBaseOperations, LevellingUtils, ListenersFunctions, OtherUtils, Twitch
from utils import get_avatar_dominant_color
from .context import DwelloContext
import constants as cs

if TYPE_CHECKING:
    from asyncpg import Connection, Pool
    from asyncpg.transaction import Transaction

DBT = TypeVar("DBT", bound="Dwello")
DCT = TypeVar("DCT", bound="DwelloContext")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] - %(name)s: %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S %Z%z",  # CET timezone format
)

LINKS_RE = re.compile(
    r"((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*",
    flags=re.IGNORECASE,
)

initial_extensions: Tuple[str] = ("jishaku",)
extensions: List[str] = [
    "cogs.economy",
    "cogs.entertainment",
    "cogs.information",
    "cogs.moderation",
    "cogs.information.help",
    "cogs.guild",
    "cogs.other.owner",
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
        if bg is True:
            base += "4{color}m"
        else:
            base += "3{color}m"
    return base.format(fmt=fmt, color=color)


def countlines(directory: str, /, lines=0, ext=".py", skip_blank=False):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if not filename.endswith(ext):
                continue
            file = os.path.join(root, filename)
            with open(file, "r", encoding="utf-8") as f:
                new_lines = len([i for i in f.readlines() if i.strip()]) if skip_blank else len(f.readlines())
                lines = lines + new_lines
    return lines


# GLOBAL CHECKS
def blacklist_check(ctx: DwelloContext) -> bool:
    return not ctx.bot.is_blacklisted(ctx.author.id)


# CONTEXT MENUS
async def my_cool_context_menu(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.send_message("Very cool message!", ephemeral=True)


# TRANSLATOR
class MyTranslator(app_commands.Translator):
    async def translate(
        self, string: app_commands.locale_str, locale: discord.Locale, context: app_commands.TranslationContext
    ):  # noqa: E501
        print(string, string.message, locale, context, context.location, context.data)
        """# check if locale is the lang we want
    # using dutch as an example
    if locale is not discord.Locale.nl:
      # its not nl -> return None
      return None

    # check if the command description is being translated
    if context.location is app_commands.TranslationContextLocation.command_description:
      print(context.data) # will the command instance (app_commands.Command)
      # check original description
      if string.message == "english":
        # return translated description
        return "engels"

    # no translation string for a command or anything? return None"""
        return None


class ContextManager(Generic[DBT]):
    __slots__: tuple[str, ...] = ("bot", "timeout", "_pool", "_conn", "_tr")

    def __init__(self, bot: Dwello, *, timeout: float = 10.0) -> None:
        self.bot: DBT = bot
        self.timeout: float = timeout
        self._pool: Pool = bot.pool
        self._conn: Connection | None = None
        self._tr: Transaction | None = None

    async def acquire(self) -> Connection:
        return await self.__aenter__()

    async def release(self) -> None:
        return await self.__aexit__(None, None, None)

    async def __aenter__(self) -> Connection:
        self._conn = conn = await self._pool.acquire(timeout=self.timeout)  # type: ignore
        conn: Connection
        self._tr = conn.transaction()
        await self._tr.start()
        return conn  # type: ignore

    async def __aexit__(self, exc_type, exc, tb):
        if exc and self._tr:
            await self._tr.rollback()

        elif not exc and self._tr:
            await self._tr.commit()

        if self._conn is not None:
            await self._pool.release(self._conn)


class Dwello(commands.AutoShardedBot):
    user: discord.ClientUser
    DEFAULT_PREFIXES: ClassVar[List[str]] = ["dw.", "Dw.", "dwello.", "Dwello."]

    logger = logging.getLogger("logging")
    _ext_log = logging.getLogger("extensions")

    def __init__(self, pool: asyncpg.Pool, session: aiohttp.ClientSession, **kwargs) -> None:
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
        self.http_session = session

        self.repo = cs.GITHUB

        self.reply_count: int = 0
        self._was_ready = False
        self.test_instance = False
        self.main_prefix: str = self.DEFAULT_PREFIXES[0]
        self.total_lines: int = countlines('G:\My Drive\discordbot', skip_blank=True)  # noqa: W605
        # wont work on host, somehow automatically determine the directory

        self.blacklisted_users: dict[int, str] = {}
        self.bypass_cooldown_users: list[int] = []

        self.cooldown: commands.CooldownMapping[discord.Message] = commands.CooldownMapping.from_cooldown(
            1,
            1.5,
            commands.BucketType.member,
        )

        self.autocomplete = AutoComplete(self)
        self.listeners = ListenersFunctions(self)
        self.levelling = LevellingUtils(self)
        self.db = DataBaseOperations(self)
        self.otherutils = OtherUtils(self)
        self.web = AiohttpWeb(self)

        # Caching Variables (for now)
        # TODO: Use LRU Cache
        self.message_cache: dict[int, discord.Message] = {}

    @property
    def color(self) -> Optional[discord.Color]:
        return self.default_color
    
    @property
    def colour(self) -> Optional[discord.Colour]:
        return self.default_color

    async def setup_hook(self) -> None:
        try:
            for ext in initial_extensions:
                await self.load_extension(ext, _raise=False)

            for ext in extensions:
                await self.load_extension(ext, _raise=False)
        except Exception as e:
            raise e

        self.tables = await self.db.create_tables()
        self.db_data = await self.db.fetch_table_data()
        records: list[Any] = await self.pool.fetch("SELECT guild_id, array_agg(prefix) FROM prefixes GROUP BY guild_id")
        self.guild_prefixes = dict(records)

        blacklist: list[asyncpg.Record] = await self.pool.fetch("SELECT * FROM blacklist")
        self.twitch = await Twitch.create_access_token(self)
        for record in blacklist:
            self.blacklisted_users[record["user_id"]] = record["reason"]

        self.add_check(blacklist_check)

        self.tree.add_command(
            discord.app_commands.ContextMenu(
                name="Cool Command Name",
                callback=my_cool_context_menu,
            )
        )

        await self.tree.set_translator(MyTranslator())

        asyncio.create_task(self.web.run(port=8081))

    async def is_owner(self, user: discord.User | discord.Member) -> bool:
        """This makes jishaku usable by any of the team members or the application owner if the bot isn't in a team"""
        ids = set()

        if app := self.application:
            if app.team:
                ids = {user.id for user in app.team.members}
            elif app.owner:
                ids = {
                    app.owner.id,
                }

        return True if user.id in ids else await super().is_owner(user)

    def safe_connection(self, *, timeout: float = 10.0) -> ContextManager:
        return ContextManager(self, timeout=timeout)

    def is_blacklisted(self, user_id: int) -> bool:
        return user_id in self.blacklisted_users  # rewrite member and user and put it there as a property

    @override
    async def get_context(self, message, *, cls: Any = DwelloContext):
        return await super().get_context(message, cls=cls)

    @override
    async def get_prefix(self, message: discord.Message) -> list[str]:
        if guild_prefixes := self.guild_prefixes.get(message.guild.id):  # type: ignore
            prefixes = []
            prefixes.extend(guild_prefixes)
        else:
            prefixes = self.DEFAULT_PREFIXES

        return commands.when_mentioned_or(*prefixes)(self, message)

    async def on_ready(self) -> None:
        self.logger.info(f"{col()}Python Version: {sys.version} {col()}")
        self.logger.info(f"{col()}Discord Version: {discord.__version__} {col()}")
        self.logger.info(f"{col(2, bg=True)}Logged in as {self.user} {col()}")
        self._was_ready = True

        if self.user.id == 1125762669056630915:
            self.DEFAULT_PREFIXES: List[str] = ["t.", "dt.", "Dt.", "beta.", "Beta."]
            self.test_instance = True

        if not hasattr(self, "uptime"):
            self.uptime = datetime.datetime.now(datetime.timezone.utc)

        if not hasattr(self, "default_color"):
            self.default_color = await get_avatar_dominant_color(self.user)

    @override
    async def load_extension(self, name: str, *, package: Optional[str] = None, _raise: bool = True) -> None:
        self._ext_log.info(f"{col(7)}Attempting to load {col(7, fmt=4)}{name}{col()}")
        try:
            await super().load_extension(name, package=package)
            self._ext_log.info(f"{col(2)}Loaded extension {col(2, fmt=4)}{name}{col()}")

        except Exception as e:
            self._ext_log.error(f"Failed to load extension {name}", exc_info=e)
            if _raise:
                raise e

    @override
    async def unload_extension(self, name: str, *, package: Optional[str] = None, _raise: bool = True) -> None:
        self._ext_log.info(f"{col(7)}Attempting to unload extension {col(7, fmt=4)}{name}{col()}")
        try:
            await super().unload_extension(name, package=package)
            self._ext_log.info(f"{col(2)}Unloaded extension {col(2, fmt=4)}{name}{col()}")

        except Exception as e:
            self._ext_log.error(f"Failed to unload extension {name}", exc_info=e)
            if _raise:
                raise e

    @override
    async def reload_extension(self, name: str, *, package: Optional[str] = None, _raise: bool = True) -> None:
        self._ext_log.info(f"{col(7)}Attempting to reload extension {col(7, fmt=4)}{name}{col()}")
        try:
            await super().reload_extension(name, package=package)
            self._ext_log.info(f"{col(2)}Reloaded extension {col(2, fmt=4)}{name}{col()}")

        except Exception as e:
            self._ext_log.error(f"Failed to reload extension {name}", exc_info=e)
            if _raise:
                raise e

    @overload
    async def get_or_fetch_message(
        self,
        channel: ...,
        message: ...,
    ) -> Optional[discord.Message]:
        ...

    @overload
    async def get_or_fetch_message(
        self,
        channel: ...,
        message: ...,
        *,
        partial: bool = ...,
        force_fetch: bool = ...,
        dm_allowed: bool = ...,
    ) -> Optional[Union[discord.Message, discord.PartialMessage]]:
        ...

    @overload
    async def get_or_fetch_message(
        self,
        channel: Union[str, int],
    ) -> Optional[discord.Message]:
        ...

    async def get_or_fetch_message(
        self,
        channel: Union[str, int, discord.PartialMessageable],
        message: Optional[Union[int, str]] = None,
        *,
        partial: bool = False,
        force_fetch: bool = False,
        dm_allowed: bool = False,
    ) -> Optional[Union[discord.Message, discord.PartialMessage]]:
        if message is None:
            dummy_message = str(channel)
            if link := LINKS_RE.match(dummy_message):
                dummy_message_id = int(link.string.split("/")[-1])
                if dummy_message_id in self.message_cache:
                    return self.message_cache[dummy_message_id]

                dummy_channel_id = int(link.string.split("/")[-2])
                dummy_channel = await self.getch(self.get_channel, self.fetch_channel, dummy_channel_id)
                if dummy_channel is not None and force_fetch:
                    msg = await dummy_channel.fetch_message(dummy_message_id)
                    if msg:
                        self.message_cache[msg.id] = msg
                    return msg

            try:
                return self.message_cache[int(dummy_message)]
            except (ValueError, KeyError):
                return None

        message = int(message)

        channel_id = int(channel) if isinstance(channel, (int, str)) else channel.id
        channel = await self.getch(self.get_channel, self.fetch_channel, channel_id)

        if channel is None:
            return None

        if isinstance(channel, discord.DMChannel) and not dm_allowed:
            raise ValueError("DMChannel is not allowed")

        if force_fetch:
            msg = await channel.fetch_message(message)  # type: ignore
            self.message_cache[message] = msg
            return msg

        if msg := self._connection._get_message(message):
            self.message_cache[message] = msg
            return msg

        if partial:
            return channel.get_partial_message(message)  # type: ignore

        try:
            msg = self.message_cache[message]
            return msg
        except KeyError:
            async for msg in channel.history(  # type: ignore
                limit=1,
                before=discord.Object(message + 1),
                after=discord.Object(message - 1),
            ):
                self.message_cache[message] = msg
                return msg

        return None

    async def getch(self, get_function, fetch_function, *args, **kwargs) -> Any:
        if args[0] <= 0:
            return None

        return get_function(*args) or await fetch_function(**kwargs)


async def runner():
    credentials = {
        "user": ENV["pg_username"],
        "password": ENV["pg_password"],
        "database": ENV["pg_name"],
        "host": ENV["pg_host"],
        "port": ENV["pg_port"],
    }

    async with asyncpg.create_pool(**credentials) as pool, aiohttp.ClientSession() as session, Dwello(pool, session) as bot:
        await bot.start(ENV["token"])


def run():
    asyncio.run(runner())
