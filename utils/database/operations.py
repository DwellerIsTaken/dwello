from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

#import asyncpg
import discord
from typing_extensions import Self

from .orm import Warning

if TYPE_CHECKING:
    from core import Dwello
    from asyncpg import Record


class DataBaseOperations:
    def __init__(self, bot: Dwello):
        self.bot = bot
        self.pool = bot.pool

    async def create_tables(self: Self) -> List[str]:
        async with self.bot.safe_connection() as conn:
            with open("schema.sql", "r") as f:
                tables = f.read()

            table_names = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", tables)

            await conn.execute(tables)
        return table_names

    async def fetch_table_data(self, *tables: str) -> Dict[str, Union[Any, list]]:
        async with self.bot.safe_connection() as conn:
            try:
                data = self.bot.db_data

            except AttributeError:
                data: Dict[str, Union[Any, list]] = {}

            if not tables:
                tables: List[str] = self.bot.tables.copy()
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
        reason: Optional[str] = "Not specified",
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
    
    async def unwarn(self, warn_id: int, user_id: int, guild: discord.Guild, *, all=False) -> List[Warning]:
        async with self.bot.safe_connection() as conn:
            records: List[Record]
            if all:
                records = await conn.fetch(
                    "DELETE FROM warnings "
                    "WHERE (guild_id, user_id) IN (($1, $2)) "
                    "RETURNING *",
                    guild.id,
                    user_id,
                )
            else:
                records = await conn.fetch(
                    "DELETE FROM warnings "
                    "WHERE (warn_id, guild_id, user_id) IN (($1, $2, $3)) "
                    "RETURNING *",
                    warn_id,
                    guild.id,
                    user_id,
                )
        return [Warning(record, self.bot) for record in records]
    
    async def get_warnings(self, user_id: int, guild: discord.Guild) -> List[Warning]:
        async with self.bot.safe_connection() as conn:
            records: List[Record] = await conn.fetch(
                "SELECT * FROM warnings WHERE guild_id = $1 AND user_id = $2",
                guild.id,
                user_id,
            )
        return [Warning(record, self.bot) for record in records]
    
    async def get_warning_by_id(self, warn_id: int, user_id: int, guild: discord.Guild) -> Optional[Warning]:
        async with self.bot.safe_connection() as conn:
            record: Optional[Record] = await conn.fetchrow(
                "SELECT * FROM warnings WHERE (warn_id, guild_id, user_id) IN (($1, $2, $3))",
                warn_id,
                guild.id,
                user_id,
            )
        return Warning(record, self.bot) if record is not None else None

    '''async def fetch_job_data(self: Self) -> dict:  # remove later
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                job_dict = {}
                guild_check_list = []

                data = await conn.fetch("SELECT guild_id, name, id, salary, description FROM jobs")

                for record in data:
                    guild_id, name, id, salary, description = (
                        record["guild_id"],
                        record["name"],
                        record["id"],
                        record["salary"],
                        record["description"],
                    )

                    if int(guild_id) in guild_check_list:
                        v = job_dict.get(int(guild_id))
                        v["name"] += [str(name)]
                        v["id"] += [int(id)]
                        v["salary"] += [int(salary)]
                        v["description"] += [str(description)]
                        break

                    job_dict[int(guild_id)] = {
                        "name": [str(name)],
                        "id": [int(id)],
                        "salary": [int(salary)],
                        "description": [str(description)],
                    }
                    guild_check_list.append(int(guild_id))

                return job_dict'''
