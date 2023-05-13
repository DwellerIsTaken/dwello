import asyncpg
import re

from typing import Union, Literal, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Dwello 
    
else:
    from discord.ext.commands import Bot as Dwello

class DB_Operations:

    def __init__(self, bot: Dwello):
        self.bot = bot
    
    async def create_tables(self) -> List[str]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():  
                with open("schema.sql", "r") as f:
                    tables = f.read()

                table_names = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", tables)

                await conn.execute(tables)
                return table_names
    
    async def fetch_table_data(self, *tables) -> Dict[str, Union[Any, list]]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():           
                try:
                    data = self.bot.db_data

                except AttributeError:
                    data: Dict[str, Union[Any, list]] = {}

                if not tables:
                    tables: List[str] = self.bot.tables

                for table in tables:
                    query = "SELECT * FROM " + table
                    table_data = await conn.fetch(query)
                    data[table] = table_data
                    
                    if table == "prefixes":
                        prefixes_by_guild = {}
                        for record in table_data:
                            guild_id = record['guild_id']
                            prefix = record['prefix']

                            if guild_id not in prefixes_by_guild:
                                prefixes_by_guild[guild_id] = []

                            prefixes_by_guild[guild_id].append(prefix)
        return data

    async def fetch_job_data(self) -> dict: # remove later
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():

                job_dict = {}
                guild_check_list = []

                data = await conn.fetch("SELECT guild_id, name, id, salary, description FROM jobs")

                for record in data:
                    guild_id, name, id, salary, description = record['guild_id'], record['name'], record['id'], record['salary'], record['description']

                    if int(guild_id) in guild_check_list:
                        v = job_dict.get(int(guild_id))
                        v['name'] += [str(name)]
                        v['id'] += [int(id)]
                        v['salary'] += [int(salary)]
                        v['description'] += [str(description)]
                        break
                    
                    job_dict[int(guild_id)] = {'name':[str(name)], 'id':[int(id)], 'salary':[int(salary)], 'description':[str(description)]}
                    guild_check_list.append(int(guild_id))

                return job_dict