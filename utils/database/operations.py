from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, overload #Literal

import asyncpg
import discord
import aiofiles

from discord.app_commands import Choice

from .orm import Idea, Prefix, Warning

# import functools


if TYPE_CHECKING:
    from asyncpg import Record

    from core import Context, Dwello


class DataBaseOperations:
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot
        self.pool = bot.pool

    discord.utils.format_dt

    async def autocomplete(
        self,
        current: str,
        table: str,
        name: str,
        value: str,
        *,
        all: bool = False,
        choice_length: int = 5,
    ) -> list[Choice]:
        """
        Autocompletes the input string by fetching data from the specified table.

        Parameters
        ----------
        current: :class:`str`
            The string that needs to be autocompleted.
        table: :class:`str`
            The table where the data will be fetched.
        name: :class:`str`
            The column whose items will be displayed as choices' names.
        value: :class:`str`
            The column whose items will be used as values.
        all: :class:`bool`
            If True, adds an option 'all' to choices. (Default: False)
        choice_length :class:`int`
            Parameter representing the length of the choice list that is returned. (Default: 5)

        Returns
        -------
        :class:`list[Choice]`
            A list of Choice objects representing the autocomplete options.

        Note
        ----
        - The data type of the 'value' parameter needs to match the annotation.
        - The 'value' column must contain strings.
        - The 'current' argument's type must match the type of 'value' and vice versa.
        """

        query = f"SELECT * FROM {table}"
        async with self.bot.safe_connection() as conn:
            records: list[Record] = await conn.fetch(query)

        choices = []
        item = len(current)

        if all:
            choices.append(Choice(name="all", value="all"))

        for record in records:
            if not any(name_:=record[name], value_:=record[value]):
                continue
            
            name_, value_ = str(name_), str(value_)
            if (
                current.startswith(name_.lower()[:item])
                or current.startswith(value_[:item])
            ):
                choices.append(Choice(name=name_, value=value_))

        return choices[:choice_length]

    async def create_tables(self) -> list[str]:
        async with self.bot.safe_connection() as conn:
            async with aiofiles.open("schema.sql") as f:
                tables = await f.read()

            table_names = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", tables)

            await conn.execute(tables)
        return table_names

    async def fetch_table_data(self, *tables: str) -> dict[str, Any | list]:
        async with self.bot.safe_connection() as conn:
            data: dict[str, Any | list] = {}
            for table in tables:
                if table == "prefixes":
                    continue # stored in dict already
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
                    "INSERT INTO prefixes(prefix, guild_id) VALUES($1, $2) RETURNING *",
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
                    "DELETE FROM prefixes WHERE guild_id = $1 RETURNING *",
                    guild.id,
                )
            else:
                records = await conn.fetch(
                    "DELETE FROM prefixes WHERE (prefix, guild_id) IN (($1, $2)) RETURNING *",
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
        return [await Idea.get(record, self.bot) for record in records]
