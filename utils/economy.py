from __future__ import annotations

import text_variables as tv
import datetime, re, discord
from contextlib import suppress

from discord.ext import commands
from typing import Optional, Union, Literal, Tuple

from utils import DB_Operations

# COMPLETELY REMAKE THIS PIECE OF SHIT

class SharedEconomyUtils:

    def __init__(self, bot):
        self.bot = bot

class BotEcoUtils:

    def __init__(self, bot):
        self.bot = bot
        self.seu = SharedEconomyUtils(self.bot)

    async def add_currency(self, member: discord.Member, amount: int, name: str) -> Optional[int]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                
                row = await conn.fetchrow("SELECT money FROM users WHERE user_id = $1 AND guild_id = $2 AND event_type = $3", member.id, not None if str(name) == 'bot' else member.guild.id, name)
                
                money = row[0]
                balance = int(money) + int(amount)

                await conn.execute("UPDATE users SET money = $1 WHERE user_id = $2 AND guild_id = $3 AND event_type = $4", balance, member.id, not None if str(name) == 'bot' else member.guild.id, name)

                return balance

    async def balance_check(self, ctx: commands.Context, amount: int, name: str) -> Optional[bool]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction(): 

                row = await conn.fetchrow("SELECT money FROM users WHERE user_id = $1 AND guild_id = $2 AND event_type = $3", ctx.author.id, not None if str(name) == 'bot' else ctx.guild.id, name)

                money = int(row[0]) if row else None

                if money < amount:
                    return await ctx.reply(embed = discord.Embed(title = "Permission denied", description="You don't have enough currency to execute this action!", color = tv.color))

        return True

    async def work(self, ctx: commands.Context, name: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                worked = await conn.fetchrow("SELECT worked FROM users WHERE user_id = $1 AND event_type = $2", ctx.author.id, name)
                worked = bool(worked[0]) if worked[0] else False

                date = str(datetime.datetime.now())
                date = re.split('-| ', date)

                my_datetime = datetime.datetime(int(date[0]), int(date[1]), int(date[2]) + 1, 10, 00, tzinfo = None) # UTC tzinfo = pytz.utc 9, 00
                
                limit_embed = discord.Embed(title = "→ \U0001d5e6\U0001d5fc\U0001d5ff\U0001d5ff\U0001d606 ←", description=f"Your have already worked{' *on this server* ' if str(name) == 'server' else ' '}today!\nYour next workday begins {discord.utils.format_dt(my_datetime, style ='R')}",color=tv.color)
                #limit_embed.set_footer(text = "Your next workday begins in")
                #limit_embed.timestamp = discord.utils.format_dt(my_datetime) # loop.EcoLoop.my_datetime1

                if worked == True:
                    return await ctx.reply(embed = limit_embed)

                job, salary, description = await GuildEcoUtils.server_job_info(ctx)

                amount = salary if str(name) == 'server' else 250
                if not amount:
                    return await ctx.reply("You are unemployed.")

                balance = await self.add_currency(ctx.author, amount, name)

                string = f"Your current balance: {balance}"

                embed = discord.Embed(title="→ \U0001d5e6\U0001d5ee\U0001d5f9\U0001d5ee\U0001d5ff\U0001d606 ←", description = f"Your day was very successful. Your salary for today is *{amount}*.",color=tv.color) # 𝗦𝗮𝗹𝗮𝗿𝘆
                embed.timestamp = discord.utils.utcnow()
                embed.set_footer(text=string)

                await conn.execute("UPDATE users SET worked = $1 WHERE user_id = $2 AND event_type = $3", 1, ctx.author.id, name)

        return await ctx.reply(embed=embed, mention_author=False)

class GuildEcoUtils:

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DB_Operations(self.bot)
        self.seu = SharedEconomyUtils(self.bot)

    async def fetch_basic_job_data_by_job_name(self, ctx: commands.Context, name: str) -> Optional[Tuple[Optional[int], Optional[str]]]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                data = await conn.fetchrow("SELECT salary, description FROM jobs WHERE guild_id = $1 AND name = $2", ctx.guild.id, name)

        return data[0], data[1]

    async def fetch_basic_job_data_by_username(self, ctx: commands.Context, member: discord.Member) -> Optional[Tuple[Optional[str], Optional[int], Optional[str], Optional[int]]]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                if not member:
                    member = ctx.author

                record = await conn.fetchrow("SELECT job_id FROM users WHERE user_id = $1 AND guild_id = $2 AND event_type = 'server'", member.id, member.guild.id)

                if not (record[0] if record else None):
                    return await ctx.reply(embed=discord.Embed(description="The job isn't yet set.", color=tv.color), ephemeral = True) # ephemeral:  if member == ctx.author else False

                data = await conn.fetchrow("SELECT name, salary, description FROM jobs WHERE id = $1 AND guild_id = $2", record[0], member.guild.id)

                if not data:
                    raise TypeError
                
                name, salary, description, job_id = str(data[0]), int(data[1]), str(data[2]) if data[2] else None, int(record[0])

        return name, salary, description, job_id

    async def server_job_create(self, ctx: commands.Context, name: str, salary: int, description: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                if salary >= 2000 and salary <= 20000: # DIFFERENT SALARY SYSTEM
                    pass

                else:
                    return await ctx.reply("Please provide the salary between 2000 and 20000.")

                data = await conn.fetch("SELECT name FROM jobs WHERE guild_id = $1", ctx.guild.id)

                job_count = 0
                for record in data if data else []:
                    if record['name'] == name:
                        return await ctx.reply("The job with this name already exists!")

                    if record:
                        job_count += 1

                if job_count == 10:
                    return await ctx.reply("You *cannot* have more than 10 jobs on your server, not yet!") # UNLOCK WITH PAYMENT (?)

                await conn.execute("INSERT INTO jobs(guild_id, name, salary, description) VALUES($1, $2, $3, $4)", ctx.guild.id, name, salary, description)

        await self.db.fetch_table_data("jobs")
        return await ctx.reply(embed=discord.Embed(title="Job added",description=f"You have successfully created a job on your server.\n\n*Job name:* {name}\n*Job salary:* {salary}\n*Job description:* ```{description}```",color=tv.color),mention_author=False)

                #existing_id_list = []
                #new_job_id_list = []
                #limit = 10

                #existing_id_list.append(int(record["job_id"]) if record["job_id"] is not None else None)

                #new_job_id_list.append(str(''.join(["{}".format(random.randint(0, 9)) for num in range(0, limit)])))

                #new_job_id = int(new_job_id_list[-1])

                #while new_job_id in existing_id_list is True:
                #new_job_id_list.append(str(''.join(["{}".format(random.randint(0, 9)) for num in range(0, limit)])))

    async def jobs_display(self, ctx: commands.Context) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                data = await conn.fetch("SELECT name, salary, description FROM jobs WHERE guild_id = $1", ctx.guild.id)

                job_embed = discord.Embed(title="Joblist", description="Jobs currently available on this server", color = tv.color)
                failure_embed = discord.Embed(description="No jobs currently available on this server",color=tv.warn_color)

                for record in data:
                    name, salary, description = record['name'], record['salary'], record['description']

                    if not name:
                        continue
                    
                    value = f"*Salary:* {salary}\n*Description:* {description if description else None}"
                    job_embed.add_field(name = name, value = value, inline = False)

                if not job_embed.fields:
                    job_embed = failure_embed

        return await ctx.reply(embed = job_embed, mention_author = False)
    
    async def server_job_remove(self, ctx: commands.Context, member: Optional[discord.Member]) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                if not ctx.author.guild_permissions.administrator and member and member != ctx.author:
                    return await ctx.reply("You can't remove someone's job unless you are a server administrator.", ephemeral=True)
                
                if not member:
                    member = ctx.author
                
                try:
                    name, salary, description, job_id = await self.fetch_basic_job_data_by_username(ctx, member)
                
                except TypeError:
                    return # that means that secondary function probably already returned discord.Message, so handle it to prevent any further issues

                await conn.execute("UPDATE users SET job_id = NULL WHERE job_id = $1 AND guild_id = $2 AND user_id = $3 AND event_type = 'server'", job_id, ctx.guild.id, member.id)

        return await ctx.reply(embed=discord.Embed(description=f"{'Your job' if member == ctx.author else f'The job of {member}'} is removed.\n\n**Details**\nJob name: {name}\nSalary: {salary}\nDescription: {description if not description else f'```{description}```'}",color=tv.color))

    async def server_job_delete(self, ctx: commands.Context, name: Union[str, Literal['all']]) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                data = await conn.fetch("SELECT id FROM jobs WHERE guild_id = $1", ctx.guild.id)

                job_count = 0
                if not data:
                    return await ctx.reply("There are no jobs to remove yet...")

                if name == "all":
                    for record in data:
                        if record:
                            job_count += 1
                    await conn.execute("DELETE FROM jobs WHERE id IS NOT NULL AND guild_id = $1", ctx.guild.id)
                    await conn.execute("UPDATE users SET job_id = NULL WHERE guild_id = $1 AND event_type = 'server'", ctx.guild.id)

                else:
                    try:
                        salary, description = await self.fetch_basic_job_data_by_job_name(ctx, name)

                    except TypeError:
                        return await ctx.reply("That job doesn't exist.", ephemeral=True)
                    job_id = await conn.fetchrow("SELECT id FROM jobs WHERE name = $1 AND guild_id = $2", name, ctx.guild.id)

                    await conn.execute("DELETE FROM jobs WHERE name = $1 AND guild_id = $2", name, ctx.guild.id)
                    await conn.execute("UPDATE users SET job_id = NULL WHERE job_id = $1 AND guild_id = $2 AND event_type = 'server'", job_id[0], ctx.guild.id)
                
                embed_string = f"Successfully removed " + ((f'*{job_count}* job(s).') if name == 'all' else (f'the job.\n\n**Details**\nJob name: {name}\nSalary: {salary}\nDescription: ' + (description if not description else f'```{description}```')))

                public_embed = discord.Embed(title="Removed!", description=f"*Removed by:* {ctx.author.mention} \n{embed_string}", color=tv.color)
                public_embed.timestamp = discord.utils.utcnow()

        await self.db.fetch_table_data("jobs", "users")
        return await ctx.reply(embed = public_embed, mention_author=False) # KEEP IT PUBLIC? ADMIN COULD REMOVE IT AND NO ONE WILL KNOW WHO DID IT. MAYBE MAKE BOT/JOB LOGS TO ADD SIMILAIR ACTIONS TO THEM

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

    '''async def server_user_job_display(self, ctx: commands.Context, member: discord.Member) -> Optional[Tuple[Optional[str], Optional[int], Optional[str]]]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                name, salary, description = await self.fetch_basic_job_data_by_username(ctx, member)

                embed = discord.Embed(title="Your job", description=f"**{name}**\n*Salary:* {salary}\n*Description:* {description}", color=tv.color)
                #failure_embed = discord.Embed(title="You have no job!", description="> Go on and get it!", color=tv.color)
                return await ctx.reply(embed if name else failure_embed ,mention_author=False) #*ID:* `{job[1]}`

                if not member:
                    member = ctx.author

                record = await conn.fetchrow("SELECT job_id FROM users WHERE user_id = $1 AND guild_id = $2 AND event_type = 'server'", member.id, member.guild.id)

                if not (record[0] if record else None):
                    return await ctx.reply(embed=discord.Embed(description="The job isn't set.", color=tv.color), ephemeral = True if member == ctx.author else False)

                data = await conn.fetchrow("SELECT name, salary, description FROM jobs WHERE id = $1 AND guild_id = $2", record[0], member.guild.id)

                if not data:
                    print(data)
                    return 
                
                name, salary, description = str(data[0]), int(data[1]), str(data[2]) if data[2] else None

        return name, salary, description'''
