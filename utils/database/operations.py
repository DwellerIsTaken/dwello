from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, List, Union

import asyncpg
from typing_extensions import Self

if TYPE_CHECKING:
    from core import Dwello


class DataBaseOperations:
    def __init__(self, bot: Dwello):
        self.bot = bot

    async def create_tables(self: Self) -> List[str]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                with open("schema.sql", "r") as f:
                    tables = f.read()

                table_names = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", tables)

                await conn.execute(tables)
        return table_names

    async def fetch_table_data(self, *tables: str) -> Dict[str, Union[Any, list]]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
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

    async def fetch_job_data(self: Self) -> dict:  # remove later
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

                return job_dict
