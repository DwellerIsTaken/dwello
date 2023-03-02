from features.economy.utils.server_attributes import server_job_info
import asqlite, discord, typing
import text_variables as tv
import datetime, re

async def add_currency(member, amount, name: typing.Literal['bot','server']) -> int:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            if str(name) != 'bot' and str(name) != 'server':
                raise TypeError
            
            await cursor.execute("SELECT money FROM users WHERE user_id = ? AND guild_id = ? AND event_type = ?", (member.id, not None if str(name) == 'bot' else member.guild.id, name))
            
            money = await cursor.fetchone()
            balance = int(money[0]) + int(amount)

            await cursor.execute("UPDATE users SET money = ? WHERE user_id = ? AND guild_id = ? AND event_type = ?", (balance, member.id, not None if str(name) == 'bot' else member.guild.id, name))
            await connector.commit()

            return balance

async def balance_check(ctx, amount, name: typing.Literal['bot','server']) -> bool:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:   

            if str(name) != 'bot' and str(name) != 'server':
                raise TypeError

            await cursor.execute("SELECT money FROM users WHERE user_id = ? AND guild_id = ? AND event_type = ?", (ctx.message.author.id, not None if str(name) == 'bot' else ctx.guild.id, name))

            money = await cursor.fetchone()
            money = int(money[0])

            if money < amount:
                await ctx.reply(embed = discord.Embed(title = "Permission denied", description="You don't have enough currency to execute this action!", color = tv.color))
                return False

            return True

async def work(ctx, name: typing.Literal['bot','server']) -> None: #amount: bool = None?
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            if str(name) != 'bot' and str(name) != 'server':
                raise TypeError

            await cursor.execute("SELECT worked FROM users WHERE user_id = ? AND event_type = ?", (ctx.message.author.id, name))
            worked = await cursor.fetchone()
            worked = bool(worked[0]) if worked[0] else False

            date = str(datetime.datetime.now())
            date = re.split('-| ', date)

            my_datetime = datetime.datetime(int(date[0]), int(date[1]), int(date[2]) + 1, 10, 00, tzinfo = None) # UTC tzinfo = pytz.utc 9, 00
            
            limit_embed = discord.Embed(title = "→ \U0001d5e6\U0001d5fc\U0001d5ff\U0001d5ff\U0001d606 ←", description=f"Your have already worked{' *on this server* ' if str(name) == 'server' else ' '}today!\nYour next workday begins {discord.utils.format_dt(my_datetime, style ='R')}",color=tv.color)
            #limit_embed.set_footer(text = "Your next workday begins in")
            #limit_embed.timestamp = discord.utils.format_dt(my_datetime) # loop.EcoLoop.my_datetime1

            if worked == True:
                return await ctx.reply(embed = limit_embed)

            job, salary, description = await server_job_info(ctx)

            amount = salary if str(name) == 'server' else 250
            if not amount:
                return await ctx.reply("You are unemployed.")

            exe = str(await add_currency(ctx.message.author, amount, name))

            string = f"Your current balance: {exe}"

            embed = discord.Embed(title="→ \U0001d5e6\U0001d5ee\U0001d5f9\U0001d5ee\U0001d5ff\U0001d606 ←", description = f"Your day was very successful. Your salary for today is *{amount}*.",color=tv.color) # 𝗦𝗮𝗹𝗮𝗿𝘆
            embed.timestamp = discord.utils.utcnow()
            embed.set_footer(text=string)

            await cursor.execute("UPDATE users SET worked = ? WHERE user_id = ? AND event_type = ?",(int(True), ctx.message.author.id, name))
            await ctx.reply(embed=embed,mention_author=False)

            await connector.commit()