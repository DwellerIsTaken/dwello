import asyncpg, discord, datetime, string, os
from dotenv import load_dotenv
import text_variables as tv

load_dotenv()

async def create_tables() -> None:
    pool = await asyncpg.create_pool(database= tv.db_name, user= tv.db_username, password= os.getenv('pg_password'))
    async with pool.acquire() as conn:
        async with conn.transaction():
            with open("databases/schema.sql", "r") as f:
                tables = f.read()

            await conn.execute(tables)
    await pool.close()

async def create_user(user_id: int, guild_id: int) -> None:
    async with asyncpg.create_pool(database= tv.db_name, user= tv.db_username, password= os.getenv('pg_password')) as pool:
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("INSERT INTO users(user_id, guild_id, event_type) VALUES($1, $2, 'server'), ($1, $2, 'bot') ON CONFLICT (user_id, guild_id, event_type) DO NOTHING", user_id, guild_id)

async def increase_xp(message, rate=5) -> None:
    async with asyncpg.create_pool(database= tv.db_name, user= tv.db_username, password= os.getenv('pg_password')) as pool:
        async with pool.acquire() as conn:
            async with conn.transaction():
                if message.author.bot:
                    return

                await create_user(message.author.id, message.guild.id)

                record = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1 AND guild_id = $2", message.author.id, message.guild.id)

                if record:
                    xp, level, messages, total_xp = record["xp"], record["level"], record["messages"], record["total_xp"]
                else:
                    xp, level, messages, total_xp = 0, 0, 0, 0

                level_formula = int(level * (level * 10))

                if xp >= level_formula:

                    new_level = int(level + 1)

                    new_level_formula = int(new_level * (new_level * 10))

                    xp_till_next_level = int(new_level_formula - 0)

                    level_embed_dis = f"*Your new level is: {new_level}*\n*Xp until your next level: {xp_till_next_level}*" # xp until next level

                    level_embed = discord.Embed(title = "Congratulations with your new level!", description = string.Template(level_embed_dis).safe_substitute(member=message.author.name), color = tv.color)

                    level_embed.set_thumbnail(url=f"{message.author.display_avatar}")
                    level_embed.set_author(name=f"{message.author.name}", icon_url=f"{message.author.display_avatar}")
                    level_embed.set_footer(text = f"{message.guild.name}")
                    level_embed.timestamp = datetime.datetime.utcnow()

                    try:
                        await message.author.send(embed=level_embed)

                    except:
                        pass

                    await conn.execute(
                        "UPDATE users SET xp = $1, total_xp = $2, level = $3, messages = $4 WHERE user_id = $5 AND guild_id = $6",
                        xp * 0, total_xp + rate, new_level, messages + 1, message.author.id, message.guild.id
                    )

                else:
                    pass

                await conn.execute(
                    "UPDATE users SET xp = $1, total_xp = $2, messages = $3 WHERE user_id = $4 AND guild_id = $5",
                    xp + rate, total_xp + rate, messages + 1, message.author.id, message.guild.id
                )

#counter_category_id BIGINT,
#all_counter_channel_id BIGINT, 
#members_counter_channel_id BIGINT, 
#bots_counter_channel_id BIGINT, 
#welcome_channel_id BIGINT, 
#leave_channel_id BIGINT, 
#twitch_channel_id BIGINT,
#twitch_client_id BIGINT,
#twitch_client_secret STRING,

'''async def create_user(user_id: int, guild_id: int) -> None:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            await cursor.execute(f"SELECT * FROM users WHERE guild_id = {guild_id} AND user_id = {user_id}")
            record = await cursor.fetchone()

            if record is not None:
                return

            await cursor.execute("INSERT INTO users(user_id, guild_id, event_type) VALUES(?, ?, ?)", (user_id, guild_id, "server"))
            await cursor.execute("INSERT INTO users(user_id, guild_id, event_type) VALUES(?, ?, ?)", (user_id, guild_id, "bot"))
            await connector.commit()

async def increase_xp(message, rate=5) -> None:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            if message.author.bot:
                return

            await create_user(message.author.id, message.guild.id)

            await cursor.execute("SELECT * FROM users WHERE user_id = ? AND guild_id = ?", (message.author.id, message.guild.id))
            records = await cursor.fetchall()

            for record in records:
                a, b, c, d = int(record['xp']), int(record['level']), int(record['messages']), int(record['total_xp'])
                xp, level, messages, total_xp = a, b, c, d

            level_formula = int(level*(level * 10))

            if xp >= level_formula:

                new_level = int(level + 1)

                new_level_formula = int(new_level*(new_level * 10))

                xp_till_next_level = int(new_level_formula - 0)

                level_embed_dis = f"*Your new level is: {new_level}*\n*Xp until your next level: {xp_till_next_level}*" # xp until next level

                level_embed = discord.Embed(title = "Congradulations with your new level!", description = string.Template(level_embed_dis).safe_substitute(member=message.author.name), color = tv.color)

                level_embed.set_thumbnail(url=f"{message.author.display_avatar}")
                level_embed.set_author(name=f"{message.author.name}", icon_url=f"{message.author.display_avatar}")
                level_embed.set_footer(text = f"{message.guild.name}")
                level_embed.timestamp = datetime.datetime.utcnow()

                try:
                    await message.author.send(embed=level_embed)

                except:
                    pass

                return await cursor.execute(f"UPDATE users SET xp = ?, total_xp = ?, level = ?, messages = ? WHERE user_id = ? AND guild_id = ?", (xp * 0, total_xp + rate, new_level, messages + 1, message.author.id, message.guild.id))

            else:
                pass

            await cursor.execute(
                "UPDATE users SET xp = ?, total_xp = ?, messages = ? WHERE user_id = ? AND guild_id = ?",
                (xp + rate,
                total_xp + rate,
                messages + 1,
                message.author.id,
                message.guild.id)
            )

            await connector.commit()

            # This function is used to increase a user's XP in the database
                async def increase_xp(message, rate=5) -> None:
                    async with asqlite.connect(tv.sql_dir) as connector:
                        async with connector.cursor() as cursor:
                            # Check if the message author is a bot, if so, return
                            if message.author.bot:
                                return
                            
                            # Create user in the database, if they do not exist
                            await create_user(message.author.id, message.guild.id)

                            # Get the user's records from the database
                            await cursor.execute("SELECT * FROM users WHERE user_id = ? AND guild_id = ?", (message.author.id, message.guild.id))
                            records = await cursor.fetchall()

                            # Unpack the user's records
                            for record in records:
                                a, b, c, d = int(record['xp']), int(record['level']), int(record['messages']), int(record['total_xp'])
                                xp, level, messages, total_xp = a, b, c, d

                            # Calculate the XP threshold for the current level
                            level_formula = int(level*(level * 10))

                            # Check if the user's XP is greater than or equal to the XP threshold for the current level
                            if xp >= level_formula:

                                # Increase user's level by 1
                                new_level = int(level + 1)

                                # Calculate the XP threshold for the next level
                                new_level_formula = int(new_level*(new_level * 10))

                                # Calculate the XP remaining until the next level
                                xp_till_next_level = int(new_level_formula - 0)

                                # Create the message to be sent to the user upon leveling up
                                level_embed_dis = f"*Your new level is: {new_level}*\n*Xp until your next level: {xp_till_next_level}*"

                                # Create an embed object to hold the message
                                level_embed = discord.Embed(title = "Congradulations with your new level!", description = string.Template(level_embed_dis).safe_substitute(member=message.author.name), color = tv.color)

                                # Set the embed thumbnail to the user's avatar
                                level_embed.set_thumbnail(url=f"{message.author.display_avatar}")
                                # Set the embed author to the user's name and avatar
                                level_embed.set_author(name=f"{message.author.name}", icon_url=f"{message.author.display_avatar}")
                                # Set the embed footer to the guild's name
                                level_embed.set_footer(text = f"{message.guild.name}")
                                # Set the embed timestamp to the current UTC time
                                level_embed.timestamp = datetime.datetime.utcnow()

                                # Try to send the message to the user
                                try:
                                    await message.author.send(embed=level_embed)
                                except:
                                    pass

                                await cursor.execute("UPDATE users SET xp = ?, total_xp = ?, level = ?, messages = ? WHERE user_id = ? AND guild_id = ?", (0, total_xp + rate, new_level, messages + 1, message.author.id, message.guild.id))
                            else:
                                await cursor.execute("UPDATE users SET xp = ?, total_xp = ?, messages = ? WHERE user_id = ? AND guild_id = ?", (xp + rate, total_xp + rate, messages + 1, message.author.id, message.guild.id))
                            await connector.commit()

async def get_user_data(user_id, guild_id): #-> dict[KT,VT]
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            await create_user(user_id, guild_id)

            await cursor.fetchone("SELECT * FROM users WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
            record = await cursor.fetchone()

            return dict(record)


async def get_rank(user_id, guild_id) -> int:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            await create_user(user_id, guild_id)

            await cursor.execute("SELECT * FROM users WHERE guild_id = ? ORDER BY total_xp DESC", (guild_id))
            records = await cursor.fetchall()

            rank = 0
            for record in records:
                rank += 1
                if record["user_id"] == user_id:
                    break

            return rank'''