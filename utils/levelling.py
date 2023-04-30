from __future__ import annotations

import asyncpg, discord, string, os
from contextlib import suppress
from discord.ext import commands
from typing import List, Dict, Any, Optional
import text_variables as tv

class LevellingUtils:

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.pool: asyncpg.Pool = self.bot.pool

    async def create_user(self, user_id: Optional[int], guild_id: Optional[int]) -> None:
        async with self.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():

                await conn.execute("INSERT INTO users(user_id, guild_id, event_type) VALUES($1, $2, 'server'), ($1, $2, 'bot') ON CONFLICT (user_id, guild_id, event_type) DO NOTHING", user_id, guild_id)

    async def increase_xp(self, message: discord.Message, rate: int = 5) -> None:
        async with self.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                if message.author.bot or not message.guild:
                    return

                await self.create_user(message.author.id, message.guild.id)

                records = await conn.fetch("SELECT * FROM users WHERE user_id = $1 AND guild_id = $2", message.author.id, message.guild.id)

                if records:
                    xp, level, messages, total_xp = records[0]["xp"], records[0]["level"], records[0]["messages"], records[0]["total_xp"]
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
                    level_embed.timestamp = discord.utils.utcnow()

                    #async with suppress(discord.HTTPException): await message.author.send(embed=level_embed)

                    '''try:
                        await message.author.send(embed=level_embed)

                    except discord.HTTPException:
                        pass'''

                    await conn.execute(
                        "UPDATE users SET xp = $1, total_xp = $2, level = $3, messages = $4 WHERE user_id = $5 AND guild_id = $6",
                        xp * 0, total_xp + rate, new_level, messages + 1, message.author.id, message.guild.id
                    )

                await conn.execute(
                    "UPDATE users SET xp = $1, total_xp = $2, messages = $3 WHERE user_id = $4 AND guild_id = $5",
                    xp + rate, total_xp + rate, messages + 1, message.author.id, message.guild.id
                )

    async def get_user_data(self, user_id: Optional[discord.Member.id] = int, guild_id: Optional[discord.Guild.id] = int) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():

                await self.create_user(user_id, guild_id)
            
                records = await conn.fetch("SELECT * FROM users WHERE user_id = $1 AND guild_id = $2", user_id, guild_id)
                results = []
                for record in records:
                    results.append(dict(record))

        return results


    async def get_rank(self, user_id: Optional[discord.Member.id] = int, guild_id: Optional[discord.Guild.id] = int) -> Optional[int]:
        async with self.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():

                await self.create_user(user_id, guild_id)

                records = await conn.fetch("SELECT * FROM users WHERE guild_id = $1 ORDER BY total_xp DESC", guild_id)

                rank = 0
                for record in records:
                    rank += 1
                    if record['user_id'] == user_id:
                        break
                        
        return rank