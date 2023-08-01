from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, overload

import asyncpg
import discord

from .orm import Idea, Prefix, Warning

# import functools


if TYPE_CHECKING:
    from asyncpg import Record

    from core import Context, Dwello


class DataBaseOperations:
    def __init__(self, bot: Dwello):
        self.bot = bot
        self.pool = bot.pool

    async def create_tables(self) -> list[str]:
        async with self.bot.safe_connection() as conn:
            with open("schema.sql") as f:
                tables = f.read()

            table_names = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", tables)

            await conn.execute(tables)
        return table_names

    async def fetch_table_data(self, *tables: str) -> dict[str, Any | list]:
        async with self.bot.safe_connection() as conn:
            try:
                data = self.bot.db_data

            except AttributeError:
                data: dict[str, Any | list] = {}

            if not tables:
                tables: list[str] = self.bot.tables.copy()
                tables.remove("prefixes")

            for table in tables:
                if table == "prefixes":
                    continue
                query = f"SELECT * FROM {table}"
                table_data = await conn.fetch(query)
                data[table] = table_data
        return data

    # use ctx, member, message ... (find one class for that) as an object to get guild and author
    async def warn(
        self,
        user_id: int,
        guild: discord.Guild,
        author: discord.Member,
        *,
        reason: str | None = "Not specified",
    ) -> Warning:
        async with self.bot.safe_connection() as conn:
            record: Record = await conn.fetchrow(
                "INSERT INTO warnings(guild_id, user_id, warn_text, created_at, warned_by) "
                "VALUES($1, $2, $3, $4, $5) "
                "RETURNING *",
                guild.id,
                user_id,
                reason,
                discord.utils.utcnow().replace(tzinfo=None),
                author.id,
            )
        return Warning(record, self.bot)

    async def unwarn(self, warn_id: int, user_id: int, guild: discord.Guild, *, all=False) -> list[Warning]:
        async with self.bot.safe_connection() as conn:
            records: list[Record]
            if all:
                records = await conn.fetch(
                    "DELETE FROM warnings " "WHERE (guild_id, user_id) IN (($1, $2)) " "RETURNING *",
                    guild.id,
                    user_id,
                )
            else:
                records = await conn.fetch(
                    "DELETE FROM warnings " "WHERE (warn_id, guild_id, user_id) IN (($1, $2, $3)) " "RETURNING *",
                    warn_id,
                    guild.id,
                    user_id,
                )
        return [Warning(record, self.bot) for record in records]

    # @functools.lru_cache(maxsize=1)
    async def get_warnings(self, user_id: int, guild: discord.Guild) -> list[Warning]:
        async with self.bot.safe_connection() as conn:
            records: list[Record] = await conn.fetch(
                "SELECT * FROM warnings WHERE guild_id = $1 AND user_id = $2",
                guild.id,
                user_id,
            )
        return [Warning(record, self.bot) for record in records]

    async def get_warning_by_id(self, warn_id: int, user_id: int, guild: discord.Guild) -> Warning | None:
        async with self.bot.safe_connection() as conn:
            record: Record | None = await conn.fetchrow(
                "SELECT * FROM warnings WHERE (warn_id, guild_id, user_id) IN (($1, $2, $3))",
                warn_id,
                guild.id,
                user_id,
            )
        return Warning(record, self.bot) if record is not None else None

    @overload
    async def add_prefix(
        self,
        guild: discord.Guild,
        prefix: str,
        *,
        context: None,
    ) -> Prefix | None:
        ...

    @overload
    async def add_prefix(
        self,
        guild: discord.Guild,
        prefix: str,
        *,
        context: Context,
    ) -> Prefix | discord.Message:
        ...

    async def add_prefix(
        self,
        guild: discord.Guild,
        prefix: str,
        *,
        context: Context | None = None,
    ) -> Prefix | discord.Message:
        async with self.bot.safe_connection() as conn:
            try:
                record: Record | None = await conn.fetchrow(
                    "INSERT INTO prefixes(prefix, guild_id) VALUES($1, $2) " "RETURNING *",
                    prefix,
                    guild.id,
                )
            except asyncpg.exceptions.StringDataRightTruncationError:
                if context:
                    return await context.reply("This prefix is too long!", user_mistake=True)
                raise
            except asyncpg.exceptions.UniqueViolationError:
                if context:
                    return await context.reply("This prefix is already added!", user_mistake=True)
                raise

        return Prefix(record, self.bot)

    async def remove_prefix(self, prefix: str, guild: discord.Guild, *, all=False) -> list[Prefix]:
        async with self.bot.safe_connection() as conn:
            records: list[Record]
            if all:
                records = await conn.fetch(
                    "DELETE FROM prefixes " "WHERE guild_id = $1 " "RETURNING *",
                    guild.id,
                )
            else:
                records = await conn.fetch(
                    "DELETE FROM prefixes " "WHERE (prefix, guild_id) IN (($1, $2)) " "RETURNING *",
                    prefix,
                    guild.id,
                )
        return [Prefix(record, self.bot) for record in records]

    # @functools.lru_cache(maxsize=1)
    async def get_prefixes(self, guild: discord.Guild) -> list[Prefix]:
        async with self.bot.safe_connection() as conn:
            records: list[Record] = await conn.fetch(
                "SELECT * FROM prefixes WHERE guild_id = $1",
                guild.id,
            )
        return [Prefix(record, self.bot) for record in records]

    async def suggest_idea(
        self,
        title: str,
        content: str,
        author: discord.User | discord.Member,
    ) -> Idea:
        return await Idea.suggest(self.bot, title, content, author.id)

    async def get_ideas(self) -> list[Idea]:
        async with self.bot.safe_connection() as conn:
            records: list[Record] = await conn.fetch("SELECT * FROM ideas")
        return [Idea(record, self.bot) for record in records]
