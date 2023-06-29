from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Generic, Optional, Tuple, TypeVar

import aiohttp
import asyncpg
from dotenv import load_dotenv
from typing_extensions import Self

from utils.bases.bot_base import DwelloBase, get_or_fail
from utils.context import DwelloContext

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

load_dotenv()


class ContextManager(Generic[DBT]):
    """A simple context manager used to manage database connections.

    Attributes
    ----------
    bot: :class:`Dwello`
        The bot instance.
    timeout: :class:`float`
        The timeout for acquiring a connection.
    """

    __slots__: Tuple[str, ...] = ("bot", "timeout", "_pool", "_conn", "_tr")

    def __init__(self, bot: DBT, *, timeout: float = 10.0) -> None:
        self.bot: DBT = bot
        self.timeout: float = timeout
        self._pool: Pool[asyncpg.Record] = bot.pool
        self._conn: Optional[Connection] = None
        self._tr: Optional[Transaction] = None

    async def acquire(self) -> Connection:
        return await self.__aenter__()

    async def release(self) -> None:
        return await self.__aexit__(None, None, None)

    async def __aenter__(self) -> Connection[asyncpg.Record]:
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


class Dwello(DwelloBase):
    def safe_connection(self: Self, *, timeout: float = 10.0) -> ContextManager:
        """A context manager that will acquire a connection from the bot's pool.

        This will neatly manage the connection and release it back to the pool when the context is exited.

        .. code-block:: python3

            async with bot.safe_connection(timeout=10) as conn:
                await conn.execute('SELECT * FROM table')
        """
        return ContextManager(self, timeout=timeout)


if __name__ == "__main__":
    credentials = {
        "user": get_or_fail("pg_username"),
        "password": get_or_fail("pg_password"),
        "database": get_or_fail("pg_name"),
        "host": get_or_fail("pg_host"),
        "port": get_or_fail("pg_port"),
    }

    async def main():  # ADD SSH KEY CONNECTION
        async with asyncpg.create_pool(**credentials) as pool, aiohttp.ClientSession() as session, Dwello(
            pool, session
        ) as bot:
            token = get_or_fail("token")
            await bot.start(token)

    asyncio.run(main())

# This command doesn't exist: function (error handler)
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
#
# for members' names discord.utils.escape_markdown(member)
