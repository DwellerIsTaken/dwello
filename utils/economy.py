from __future__ import annotations

import text_variables as tv
import datetime, re, discord

from discord.ext import commands
from typing import Optional, Union, Literal, Tuple

# COMPLETELY REMAKE THIS PIECE OF SHIT

class BotEcoUtils(commands.Cog):

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

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
                    await ctx.reply(embed = discord.Embed(title = "Permission denied", description="You don't have enough currency to execute this action!", color = tv.color))
                    return False

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

                exe = str(await self.add_currency(ctx.author, amount, name))

                string = f"Your current balance: {exe}"

                embed = discord.Embed(title="→ \U0001d5e6\U0001d5ee\U0001d5f9\U0001d5ee\U0001d5ff\U0001d606 ←", description = f"Your day was very successful. Your salary for today is *{amount}*.",color=tv.color) # 𝗦𝗮𝗹𝗮𝗿𝘆
                embed.timestamp = discord.utils.utcnow()
                embed.set_footer(text=string)

                await conn.execute("UPDATE users SET worked = $1 WHERE user_id = $2 AND event_type = $3", 1, ctx.author.id, name)

        return await ctx.reply(embed=embed, mention_author=False)

class GuildEcoUtils(commands.Cog):

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def server_job_create(self, ctx: commands.Context, name: str, salary: int, description: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                if salary >= 2000 and salary <= 20000:
                    pass

                else:
                    return await ctx.reply("Please provide the salary between 2000 and 20000.")

                data = await conn.fetch("SELECT name FROM jobs WHERE guild_id = $1", ctx.guild.id)

                job_count = 0
                for record in data if data else []:
                    if str(record) == str(name):
                        return await ctx.reply("The job with this name already exists!")

                    if record is not None:
                        job_count += 1

                if job_count == 10:
                    return await ctx.reply("You *cannot* have more than 10 jobs on your server, not yet!") # UNLOCK WITH PAYMENT

                await conn.execute("UPDATE jobs SET name = $1, salary = $2, description = $3 WHERE guild_id = $4", name, salary, description, ctx.guild.id)

        return await ctx.reply(embed=discord.Embed(title="Job added",description=f"You have successfully created a job on your server.\n\n*Job name:* {name}\n*Job salary:* {salary}\n*Job description:* ```{description}```",color=tv.color),mention_author=False)

                #existing_id_list = []
                #new_job_id_list = []
                #limit = 10

                #existing_id_list.append(int(record["job_id"]) if record["job_id"] is not None else None)

                #new_job_id_list.append(str(''.join(["{}".format(random.randint(0, 9)) for num in range(0, limit)])))

                #new_job_id = int(new_job_id_list[-1])

                #while new_job_id in existing_id_list is True:
                #new_job_id_list.append(str(''.join(["{}".format(random.randint(0, 9)) for num in range(0, limit)])))

    async def jobs_display(self, ctx: commands.Context) -> Optional[discord.Embed]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                data = await conn.fetch("SELECT name, salary, description FROM jobs WHERE guild_id = $1", ctx.guild.id)

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

        return embed # MAYBE SEND IMMEDIATELY | WTF IS THIS SHIT

    async def server_job_remove(self, ctx: commands.Context, name: Union[int, Literal['all']]) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                data = await conn.fetchrow("SELECT id FROM jobs WHERE guild_id = $1", ctx.guild.id)

                job_count = 0
                for record in data:
                    if record is not None:
                        job_count += 1
                
                if job_count == 0:
                    return await ctx.reply("There are no jobs to remove yet...")

                display = await self.jobs_display(ctx)

                if name == "all":
                    await conn.execute("DELETE FROM jobs WHERE id IS NOT NULL AND guild_id = $1", ctx.guild.id)

                else:
                    await conn.execute("DELETE FROM jobs WHERE id = $1 AND guild_id = $2", name, ctx.guild.id)
                
                string = "" #"\n.join(list)"
                for j in range(job_count):
                    string += f"\n{display[-1][j]}"

                public_embed = discord.Embed(title="Removed!", description=f'*Removed by:* {ctx.author.mention} \nSuccessfully removed *{job_count}* job(s).{string}',color=tv.color)
                public_embed.timestamp = discord.utils.utcnow()

        return await ctx.reply(embed = public_embed, mention_author=False)

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

    async def server_job_info(self, ctx: commands.Context, member: discord.Member) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                if not member:
                    member = ctx.message.author

                job_id = await conn.fetchrow("SELECT job_id FROM users WHERE user_id = $1 AND guild_id = $2 AND event_type = $3", member.id, member.guild.id, "server")

                job_id = int(job_id[0]) if job_id[0] else None

                data = await conn.fetch("SELECT name, salary, description FROM jobs WHERE id = $1 AND guild_id = $2", job_id, member.guild.id)

                name = data["name"][0] if data else None
                salary = data["salary"][0] if data else None
                description = data["description"][0] if data else None

                name = str(name) if name else None
                salary = int(salary) if salary else None
                description = str(description) if description else None

                # OR [None, str(name)][bool(name)]

        return name, salary, description
