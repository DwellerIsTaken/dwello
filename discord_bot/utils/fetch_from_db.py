import asqlite
import text_variables as tv

async def fetch_job_data() -> dict:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            job_dict = {}
            guild_check_list = []

            await cursor.execute("SELECT guild_id, name, id, salary, description FROM jobs")
            data = await cursor.fetchall()

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