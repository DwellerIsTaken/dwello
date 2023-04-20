import asyncpg, os
import text_variables as tv
from discord.ext import commands

from typing import Literal, List, Dict, Any

async def create_pool() -> asyncpg.Pool: # ADD SSH KEY CONNECTION
    pool = await asyncpg.create_pool(database= os.getenv('pg_name'), user= os.getenv('pg_username'), password= os.getenv('pg_password'), host= tv.host, port= tv.port)
    return pool

class DB_Operations:

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.pool: asyncpg.Pool = self.bot.pool
    
    async def create_tables(self) -> None:
        async with self.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                with open("schema.sql", "r") as f:
                    tables = f.read()

                return await conn.execute(tables)
    
    async def fetch_data(self) -> dict:
        async with self.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                
                # Fetch data from users table
                data_users = await conn.fetch("SELECT * FROM users")

                # Fetch data from twitch_users table
                data_twitch_users = await conn.fetch("SELECT * FROM twitch_users")

                # Fetch data from warnings table
                data_warnings = await conn.fetch("SELECT * FROM warnings")

                # Fetch data from server_data table
                data_server_data = await conn.fetch("SELECT * FROM server_data")

                # Fetch data from jobs table
                data_jobs = await conn.fetch("SELECT * FROM jobs")

                all_data = {
                'users': data_users,
                'twitch_users': data_twitch_users,
                'warnings': data_warnings,
                'server_data': data_server_data,
                'jobs': data_jobs
                }

        return all_data
    
    async def fetch_table_data(self, *tables: Literal["jobs", "users", "warnings", "server_data", "twitch_users"]) -> List[Dict[str, Any]]: # not sure annotation is correct
        async with self.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                for table in tables:
                    query = "SELECT * FROM " + table
                    data = await conn.fetch(query)
                    self.bot.db_data[table] = data
        
        return [].extend(data)

    async def fetch_job_data(self) -> dict: # remove later
        async with self.pool.acquire() as conn:
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