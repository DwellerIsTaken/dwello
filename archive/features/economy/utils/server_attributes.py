from __future__ import annotations
import discord, asqlite, typing
import text_variables as tv

async def server_job_create(ctx, name: str, salary: int, description: str = None) -> None:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            if salary >= 2000 and salary <= 20000:
                pass

            else:
                return await ctx.reply("Please provide the salary between 2000 and 20000.")

            await cursor.execute("SELECT name FROM jobs WHERE guild_id = ?",(ctx.guild.id))
            data = await cursor.fetchone()

            job_count = 0
            for record in data if data else []:
                if str(record) == str(name):
                    return await ctx.reply("The job with this name already exists!")

                if record is not None:
                    job_count += 1

            if job_count == 10:
                return await ctx.reply("You *cannot* have more than 10 jobs on your server, not yet!") # UNLOCK WITH PAYMENT

            await cursor.execute("INSERT INTO jobs (guild_id, name, salary, description) VALUES(?,?,?,?)",(ctx.guild.id, name, salary, description))
            await connector.commit()
            await ctx.reply(embed=discord.Embed(title="Job added",description=f"You have successfully created a job on your server.\n\n*Job name:* {name}\n*Job salary:* {salary}\n*Job description:* ```{description}```",color=tv.color),mention_author=False)

            #existing_id_list = []
            #new_job_id_list = []
            #limit = 10

            #existing_id_list.append(int(record["job_id"]) if record["job_id"] is not None else None)

            #new_job_id_list.append(str(''.join(["{}".format(random.randint(0, 9)) for num in range(0, limit)])))

            #new_job_id = int(new_job_id_list[-1])

            #while new_job_id in existing_id_list is True:
            #new_job_id_list.append(str(''.join(["{}".format(random.randint(0, 9)) for num in range(0, limit)])))

        await cursor.close()
        await connector.close()

async def jobs_display(ctx) -> discord.Embed:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            await cursor.execute("SELECT name, salary, description FROM jobs WHERE guild_id = ?",(ctx.guild.id))
            data = cursor.fetchall()

            embed = discord.Embed(title="Joblist", description="Jobs currently available on this server", color = tv.color)
            failure_embed = discord.Embed(description="b",color=tv.warn_color)

            embed_value_list = []
            for record in data:
                name, salary, description = record['name'], record['salary'], record['description']

                if name is None:
                    continue
                
                value = f"*Salary:* {salary}\n{description if description else None}"
                embed.add_field(name = name, value = value, inline = False)
                embed_value_list.append(f"\n**{name}**\n{value}")

            if not embed_value_list:
                return failure_embed

            return embed

async def server_job_remove(ctx, name: typing.Union[int, typing.Literal['all']]) -> None:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            await cursor.execute("SELECT id FROM jobs WHERE guild_id = ?",(ctx.guild.id))
            data = await cursor.fetchone()

            job_count = 0
            for record in data:
                if record is not None:
                    job_count += 1
            
            if job_count == 0:
                return await ctx.reply("There are no jobs to remove yet...")

            display = await jobs_display(ctx)

            if name == "all":
                await cursor.execute("DELETE FROM jobs WHERE id IS NOT NULL AND guild_id = ?", (ctx.guild.id))

            else:
                await cursor.execute("DELETE FROM jobs WHERE id = ? AND guild_id = ?",(name, ctx.guild.id))
            await connector.commit()
            
            string = "" #"\n.join(list)"
            for j in range(job_count):
                string += f"\n{display[-1][j]}"

            public_embed = discord.Embed(title="Removed!", description=f'*Removed by:* {ctx.author.mention} \nSuccessfully removed *{job_count}* job(s).{string}',color=tv.color)
            public_embed.timestamp = discord.utils.utcnow()

            await ctx.reply(embed = public_embed, mention_author=False)

'''async def user_job_display(ctx, member = None) -> None:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            if not member:
                member = ctx.message.author

            await cursor.execute(f"SELECT job_id FROM main WHERE guild_id = ? AND user_id = ?",(ctx.guild.id, member.id))
            job_id = await cursor.fetchone()

            id_ = None

            for i in job_id if job_id is not None else []:
                if i is not None:
                    id_ = i

            if id_ is None and member != ctx.message.author:
                return await ctx.reply("Unemployed!")

            elif id_ is None:
                return await ctx.reply("You are unemployed!")

            await cursor.execute(f"SELECT * FROM main WHERE guild_id = ? AND job_id = ?",(ctx.guild.id, id_))
            records = await cursor.fetchall()

            for record in records:

                name = record['jobs']
                salary = record['job_salary']
                description = record['job_description']

                if name is not None:
                    return [str(name), int(id_), int(salary), str(description)]

        await cursor.close()
    await connector.close()'''

async def server_job_info(ctx, member=None) -> tuple[str | None, int | None, str | None]:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            if not member:
                member = ctx.message.author

            await cursor.execute("SELECT job_id FROM users WHERE user_id = ? AND guild_id = ? AND event_type = ?", (member.id, member.guild.id, "server"))
            job_id = await cursor.fetchone()

            job_id = int(job_id[0]) if job_id[0] else None

            await cursor.execute("SELECT name, salary, description FROM jobs WHERE id = ? AND guild_id = ?", (job_id, member.guild.id))
            data = await cursor.fetchall()

            name = data["name"][0] if data else None
            salary = data["salary"][0] if data else None
            description = data["description"][0] if data else None

            name = str(name) if name else None
            salary = int(salary) if salary else None
            description = str(description) if description else None

            # OR [None, str(name)][bool(name)]

            return name, salary, description
