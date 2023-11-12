from __future__ import annotations

import asyncpg
import discord

from core import Context, Dwello, Embed


class SharedEcoUtils:
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot

    async def fetch_basic_job_data_by_username(
        self, ctx: Context, member: discord.Member | None = None
    ) -> tuple[str | None, int | None, str | None, int | None] | None:
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
                        embed=Embed(description="The job isn't yet set."),
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

    async def add_currency(self, member: discord.Member, amount: int, name: str) -> int | None:
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
