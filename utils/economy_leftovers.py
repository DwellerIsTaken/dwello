from __future__ import annotations

import text_variables as tv
import datetime, re, discord, asyncpg
from contextlib import suppress

from discord.ext import commands
from typing import Optional, Union, Literal, Tuple, TYPE_CHECKING

from utils.context import DwelloContext

# TRANSFER ONTO ECONOMY FOLDER  

if TYPE_CHECKING:
    from bot import Dwello 
    
else:
    from discord.ext.commands import Bot as Dwello

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
