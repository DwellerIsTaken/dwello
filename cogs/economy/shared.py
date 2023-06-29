from __future__ import annotations

import datetime
import re
from typing import Optional, Tuple, Union

import asyncpg
import discord

import constants as cs
from core import Bot, Context


class SharedEcoUtils:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def fetch_basic_job_data_by_username(
        self, ctx: Context, member: discord.Member = None
    ) -> Optional[Tuple[Optional[str], Optional[int], Union[str, None], Optional[int]]]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                if not member:
                    member = ctx.author

                record = await conn.fetchrow(
                    "SELECT job_id FROM users WHERE user_id = $1 AND guild_id = $2 AND event_type = 'server'",
                    member.id,
                    member.guild.id,
                )

                if not (record[0] if record else None):
                    return await ctx.reply(
                        embed=discord.Embed(description="The job isn't yet set.", color=cs.RANDOM_COLOR),
                        ephemeral=True,
                    )

                data = await conn.fetchrow(
                    "SELECT name, salary, description FROM jobs WHERE id = $1 AND guild_id = $2",
                    record[0],
                    member.guild.id,
                )

                if not data:
                    raise TypeError

                name, salary, description, job_id = (
                    str(data[0]),
                    int(data[1]),
                    str(data[2]) if data[2] else None,
                    int(record[0]),
                )

        return name, salary, description, job_id

    async def add_currency(self, member: discord.Member, amount: int, name: str) -> Optional[int]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                row = await conn.fetchrow(
                    "SELECT money FROM users WHERE user_id = $1 AND guild_id = $2 AND event_type = $3",
                    member.id,
                    not None if name == "bot" else member.guild.id,
                    name,
                )
                # DOESNT FETCH CORRECTLY

                money = row[0]
                balance = int(money) + amount

                await conn.execute(
                    "UPDATE users SET money = $1 WHERE user_id = $2 AND guild_id = $3 AND event_type = $4",
                    balance,
                    member.id,
                    not None if name == "bot" else member.guild.id,
                    name,
                )

                return balance

    async def work(self, ctx: Context, name: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                worked = await conn.fetchrow(
                    "SELECT worked FROM users WHERE user_id = $1 AND event_type = $2",
                    ctx.author.id,
                    name,
                )
                worked = bool(worked[0]) if worked[0] else False

                date = str(datetime.datetime.now())
                date = re.split("-| ", date)

                my_datetime = datetime.datetime(
                    int(date[0]), int(date[1]), int(date[2]) + 1, 10, 00, tzinfo=None
                )  # UTC tzinfo = pytz.utc 9, 00

                # limit_embed.set_footer(text = "Your next workday begins in")
                # limit_embed.timestamp = discord.utils.format_dt(my_datetime) # loop.EcoLoop.my_datetime1

                if worked:
                    embed: discord.Embed = discord.Embed(
                        title="→ \U0001d5e6\U0001d5fc\U0001d5ff\U0001d5ff\U0001d606 ←",
                        description=f"Your have already worked{' *on this server* ' if name == 'server' else ' '}today!\nYour next workday begins {discord.utils.format_dt(my_datetime, style='R')}",
                        color=cs.RANDOM_COLOR,
                    )
                    return await ctx.reply(embed=embed)

                try:
                    (
                        job_name,
                        salary,
                        description,
                        job_id,
                    ) = await self.fetch_basic_job_data_by_username(ctx)

                except TypeError:
                    return

                amount = salary if name == "server" else 250
                if not amount:
                    return await ctx.reply("You are unemployed.")

                balance = await self.add_currency(ctx.author, amount, name)

                embed: discord.Embed = discord.Embed(
                    title="→ \U0001d5e6\U0001d5ee\U0001d5f9\U0001d5ee\U0001d5ff\U0001d606 ←",  # 𝗦𝗮𝗹𝗮𝗿𝘆
                    description=f"Your day was very successful. Your salary for today is *{amount}*.",
                    color=cs.RANDOM_COLOR,
                )
                embed.timestamp = discord.utils.utcnow()
                embed.set_footer(
                    text=f"Your current balance: {balance}",
                    icon_url=ctx.author.display_avatar.url,
                )

                await conn.execute(
                    "UPDATE users SET worked = $1 WHERE user_id = $2 AND event_type = $3",
                    1,
                    ctx.author.id,
                    name,
                )

        return await ctx.reply(embed=embed, mention_author=False)
