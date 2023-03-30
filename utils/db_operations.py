import asyncpg, os
import text_variables as tv
from discord.ext import commands

class DB_Operations():

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def create_pool(self) -> None: # ADD SSH KEY CONNECTION
        pool = await asyncpg.create_pool(database= os.getenv('pg_name'), user= os.getenv('pg_username'), password= os.getenv('pg_password'))
        #pool = await asyncpg.create_pool(database= "postgres", user= "postgres", password= "")
        return pool

    async def fetch_job_data(self) -> dict:
        async with self.bot.pool.acquire() as conn:
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

'''async def job_transform_data() -> dict:

    count = 0
    jobs_dict = {}
    total_list = []
    column_name_list = []

    data = fetch_job_data()[0]

    for record in data:
        print(record)
        print('########################')
        print(type(record))
        print('########################')
        print(record[0])

    async for data, names in fetch_job_data():
        for name in names:
            column_name_list.append(str(name))

        for record in data:
            print(record)
            print('########################')
            print(type(record))
            print('########################')
            print(record[0])
            jobs_dict[column_name_list[count]] = record

    return jobs_dict'''

'''count = 0
jobs_dict = {}
column_name_list = []
data, names = fetch_job_data() 

for name in names:
    column_name_list.append(str(name))

for record in data:
    jobs_dict[column_name_list[count]] = record'''