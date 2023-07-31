from __future__ import annotations

from typing import Any, Literal, Optional, Tuple, Union

import asyncpg
import discord
from discord.ext import commands

import constants as cs
from core import BaseCog, Context, Dwello, Embed

from .shared import SharedEcoUtils


class GuildEcoUtils:
    def __init__(self, bot: Dwello):
        self.bot = bot
        self.se: SharedEcoUtils = SharedEcoUtils(self.bot)

    async def fetch_basic_job_data_by_job_name(
        self, ctx: Context, name: str
    ) -> Optional[Tuple[Optional[int], Optional[str]]]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                data = await conn.fetchrow(
                    "SELECT salary, description FROM jobs WHERE guild_id = $1 AND name = $2",
                    ctx.guild.id,
                    name,
                )

        return data[0], data[1]

    async def server_job_create(
        self, ctx: Context, name: str, salary: int, description: str
    ) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                if salary < 2000 or salary > 20000:
                    return await ctx.reply("Please provide the salary between 2000 and 20000.")

                data = await conn.fetch("SELECT name FROM jobs WHERE guild_id = $1", ctx.guild.id)

                job_count = 0
                for record in data or []:
                    if record["name"] == name:
                        return await ctx.reply("The job with this name already exists!")

                    if record:
                        job_count += 1

                if job_count == 10:
                    return await ctx.reply(
                        "You *cannot* have more than 10 jobs on your server, not yet!"
                    )  # UNLOCK WITH PAYMENT (?) BRUH

                await conn.execute(
                    "INSERT INTO jobs(guild_id, name, salary, description) VALUES($1, $2, $3, $4)",
                    ctx.guild.id,
                    name,
                    salary,
                    description,
                )

        embed: Embed = Embed(
            title="Job added",
            description=f"You have successfully created a job on your server.\n"
            f"\n*Job name:* {name}\n*Job salary:* {salary}\n*Job description:* ```{description}```",
        )

        await self.bot.db.fetch_table_data("jobs")
        return await ctx.reply(embed=embed, permission_cmd=True)

        # existing_id_list = []
        # new_job_id_list = []
        # limit = 10

        # existing_id_list.append(int(record["job_id"]) if record["job_id"] is not None else None)

        # new_job_id_list.append(str(''.join(["{}".format(random.randint(0, 9)) for num in range(0, limit)])))

        # new_job_id = int(new_job_id_list[-1])

        # while new_job_id in existing_id_list is True:
        # new_job_id_list.append(str(''.join(["{}".format(random.randint(0, 9)) for num in range(0, limit)])))

    async def jobs_display(self, ctx: Context) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                data = await conn.fetch(
                    "SELECT name, salary, description FROM jobs WHERE guild_id = $1",
                    ctx.guild.id,
                )

                job_embed: Embed = Embed(
                    title="Joblist",
                    description="Jobs currently available on this server",
                )
                failure_embed: Embed = Embed(
                    description="No jobs currently available on this server",
                    color=cs.WARNING_COLOR,
                )

                for record in data:
                    name, salary, description = (
                        record["name"],
                        record["salary"],
                        record["description"],
                    )

                    if not name:
                        continue

                    value = f"*Salary:* {salary}\n*Description:* {description or None}"
                    job_embed.add_field(name=name, value=value, inline=False)

                if not job_embed.fields:
                    job_embed = failure_embed

        return await ctx.reply(embed=job_embed, mention_author=False)

    async def server_job_remove(self, ctx: Context, member: Optional[discord.Member]) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                if not ctx.author.guild_permissions.administrator and member and member != ctx.author:
                    return await ctx.reply(
                        "You can't remove someone's job unless you are a server administrator.",
                        ephemeral=True,
                    )

                if not member:
                    member = ctx.author

                try:
                    (
                        name,
                        salary,
                        description,
                        job_id,
                    ) = await self.se.fetch_basic_job_data_by_username(ctx, member)

                except TypeError:
                    return
                # that means that secondary function probably already returned discord.Message, so handle it to prevent any
                # further issues | TRY TO HANDLE THIS OTHERWISE

                await conn.execute(
                    "UPDATE users SET job_id = NULL WHERE job_id = $1 AND guild_id = $2 AND user_id = $3 AND event_type = 'server'",  # noqa: E501
                    job_id,
                    ctx.guild.id,
                    member.id,
                )

        # MAYBE CREATE SOME LOG FOR CMDS WITHIN SERVER AND STORE UNOFFICIAL MANAGEMENT THERE, SO IT WOULD BE SEEN WHO CREATED/REMOVED THE JOB(S)  # noqa: E501
        embed: Embed = Embed(
            description=f"{'Your job' if member == ctx.author else f'The job of {member}'} is removed.\n"
            f"\n**Details**\nJob name: {name}\nSalary: {salary}\n"
            f"Description: {f'```{description}```' if description else description}",
        )
        return await ctx.reply(embed=embed)

    async def server_job_delete(self, ctx: Context, name: Union[str, Literal["all"]]) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                data = await conn.fetch("SELECT id FROM jobs WHERE guild_id = $1", ctx.guild.id)

                job_count = 0
                if not data:
                    return await ctx.reply("There are no jobs to remove yet...")

                if name == "all":
                    for record in data:
                        if record:
                            job_count += 1
                    await conn.execute(
                        "DELETE FROM jobs WHERE id IS NOT NULL AND guild_id = $1",
                        ctx.guild.id,
                    )
                    await conn.execute(
                        "UPDATE users SET job_id = NULL WHERE guild_id = $1 AND event_type = 'server'",
                        ctx.guild.id,
                    )

                else:
                    try:
                        (
                            salary,
                            description,
                        ) = await self.fetch_basic_job_data_by_job_name(ctx, name)

                    except TypeError:
                        return await ctx.reply("That job doesn't exist.", ephemeral=True)
                    job_id = await conn.fetchrow(
                        "SELECT id FROM jobs WHERE name = $1 AND guild_id = $2",
                        name,
                        ctx.guild.id,
                    )

                    await conn.execute(
                        "DELETE FROM jobs WHERE name = $1 AND guild_id = $2",
                        name,
                        ctx.guild.id,
                    )
                    await conn.execute(
                        "UPDATE users SET job_id = NULL WHERE job_id = $1 AND guild_id = $2 AND event_type = 'server'",
                        job_id[0],
                        ctx.guild.id,
                    )

                embed_string = "Successfully removed " + (
                    (f"*{job_count}* job(s).")
                    if name == "all"
                    else (
                        f"the job.\n\n**Details**\nJob name: {name}\nSalary: {salary}\nDescription: "
                        + (f"```{description}```" if description else description)
                    )
                )

                public_embed: Embed = Embed(
                    title="Removed!",
                    description=f"*Removed by:* {ctx.author.mention} \n{embed_string}",
                )
                public_embed.timestamp = discord.utils.utcnow()

        await self.bot.db.fetch_table_data("jobs", "users")
        return await ctx.reply(
            embed=public_embed, mention_author=False
        )  # KEEP IT PUBLIC? ADMIN COULD REMOVE IT AND NO ONE WILL KNOW WHO DID IT. MAYBE MAKE BOT/JOB LOGS TO ADD SIMILAIR ACTIONS TO THEM  # noqa: E501


class Guild_Economy(BaseCog): # REDO
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self.ge: GuildEcoUtils = GuildEcoUtils(self.bot)
        self.se: SharedEcoUtils = SharedEcoUtils(self.bot)

    # jobs -- lots of available jobs ?
    # DECIDE PERMISSIONS NEEDED FOR JOBS CREATION/REMOVAL

    @commands.hybrid_group(name="server", invoke_without_command=True, with_app_command=True)
    async def server(self, ctx: Context) -> Optional[discord.Message]:
        embed = Embed(
            title="Denied",
            description="```$server [subgroup name]```",
        )  # TURN THESE DESCRIPTIONS INTO POINTERS TO HELP COMMAND
        return await ctx.reply(embed=embed)

    @server.group(name="job", invoke_without_command=True, with_app_command=True)
    async def jobs(self, ctx: Context) -> Optional[discord.Message]:
        embed = Embed(title="Denied", description="```$job list```")
        return await ctx.reply(embed=embed)

    @jobs.command(
        name="list",
        description="Shows a list of available jobs on the server set by the server administrator.",
    )
    async def job_list(self, ctx: Context) -> Optional[discord.Message]:
        return await self.ge.jobs_display(ctx)

    @jobs.command(name="create", description="Creating a job.")
    @commands.has_permissions(administrator=True)
    async def job_create(
        self,
        ctx: Context,
        name: str,
        salary: commands.Range[int, 2000, 20000],
        description: Optional[str],
    ):
        return await self.ge.server_job_create(ctx, name, salary, description)

    @jobs.command(name="delete", description="Purges job(s) from the guild.")
    @commands.has_permissions(administrator=True)
    async def job_delete(self, ctx: Context, name: str):
        return await self.ge.server_job_delete(ctx, name)

    @job_delete.autocomplete("name")
    async def autocomplete_callback_job_delete(self, interaction: discord.Interaction, current: str):
        return await self.bot.autocomplete.choice_autocomplete(interaction, current, "jobs", "name", None, True)

    @jobs.command(name="set", description="You can set your server job here!")  # MAYBE PUT THIS IN ECONOMY.PY
    async def job_set(self, ctx: Context, name: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                names = await conn.fetchval("SELECT array_agg(name) FROM jobs WHERE guild_id = $1", ctx.guild.id)

                if name.isdigit() and name not in names:
                    return await ctx.reply(
                        "Please provide a correct job name.",
                        ephemeral=True,
                        mention_author=True,
                    )

                data = await conn.fetchrow(
                    "SELECT id, salary, description FROM jobs WHERE guild_id = $1 AND name = $2",
                    ctx.guild.id,
                    name,
                )

                if not data:
                    return await ctx.reply(
                        "The provided job doesn't exist.",
                        ephemeral=True,
                        mention_author=True,
                    )

                await conn.execute(
                    "UPDATE users SET job_id = $1 WHERE user_id = $2 AND guild_id = $3 AND event_type = 'server'",
                    data[0],
                    ctx.author.id,
                    ctx.guild.id,
                )

        await self.bot.db.fetch_table_data("jobs")
        return await ctx.reply(
            embed=Embed(description=f"The job is set to: **{name}**"),
            mention_author=False,
        )

    @job_set.autocomplete("name")
    async def autocomplete_callback_job_set(self, interaction: discord.Interaction, current: str):
        return await self.bot.autocomplete.choice_autocomplete(interaction, current, "jobs", "name", None, False)

    @jobs.command(name="remove", description="Removes member's job. | Admin-associated")  # thus only one param is for admins
    async def job_remove(self, ctx: Context, member: discord.Member = None):
        return await self.ge.server_job_remove(ctx, member)

    @jobs.command(name="display", description="Displays member's current job.")
    async def display(self, ctx: Context, member: discord.Member = None) -> Optional[discord.Message]:
        try:
            (
                name,
                salary,
                description,
                job_id,
            ) = await self.se.fetch_basic_job_data_by_username(ctx, member)
            embed: Embed = Embed(
                title="Your job",
                description=f"**{name}**\n*Salary:* {salary}\n*Description:* {description}",
                color=cs.RANDOM_COLOR,
            )
            return await ctx.reply(embed=embed, mention_author=False)

        except TypeError:
            return

    @jobs.command(name="work", description="Your server work.")
    async def server_work(self, ctx: Context):
        return await self.se.work(ctx, "server")
