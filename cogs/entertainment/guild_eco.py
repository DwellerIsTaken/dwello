from __future__ import annotations

from discord.app_commands import Choice
from discord.ext import commands
import text_variables as tv
import discord

from contextlib import suppress

from typing import Optional, Any
from utils import BaseCog, BotEcoUtils, DB_Operations, GuildEcoUtils, AutoComplete

class Guild_Economy(BaseCog):

    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        self.be = BotEcoUtils(self.bot)
        self.ge = GuildEcoUtils(self.bot)
        self.db = DB_Operations(self.bot)
        self.ac = AutoComplete(self.bot)

    #jobs -- lots of available jobs

    @commands.hybrid_group(name="server", invoke_without_command=True, with_app_command=True)
    async def server(self, ctx: commands.Context) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            embed = discord.Embed(title="Denied", description="```$server [subgroup name]```",color=tv.color) # TURN THESE DESCRIPTIONS INTO POINTERS TO HELP COMMAND
            return await ctx.reply(embed=embed)

    @server.group(name="job", invoke_without_command=True, with_app_command=True)
    async def jobs(self, ctx: commands.Context) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            embed = discord.Embed(title="Denied", description="```$job list```",color=tv.color)
            return await ctx.reply(embed=embed)

    @jobs.command(name = "list", description = "Shows a list of available jobs on the server set by the server administrator.")
    async def job_list(self, ctx: commands.Context) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            return await self.ge.jobs_display(ctx)

    @jobs.command(name = "create", description = "Creating a job. | Administration")
    @commands.has_permissions(administrator = True)
    async def job_create(self, ctx: commands.Context, name: str, salary: commands.Range[int, 2000, 20000], description: Optional[str]):
        async with ctx.typing(ephemeral=True):
            return await self.ge.server_job_create(ctx, name, salary, description)

    @jobs.command(name = "delete", description = "Purges job(s) from the guild. | Administration")
    @commands.has_permissions(administrator = True)
    async def job_delete(self, ctx: commands.Context, name: str):
        async with ctx.typing(ephemeral=True):
            return await self.ge.server_job_delete(ctx, name)

    @job_delete.autocomplete('name')
    async def autocomplete_callback(self, interaction: discord.Interaction, current: str):
        return await self.ac.choice_autocomplete(interaction, current, "jobs", "name", None, True)
    
    @jobs.command(name = "set", description = "You can set your server job here!")
    async def job_set(self, ctx: commands.Context, name: str) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            async with self.bot.pool.acquire() as conn:
                async with conn.transaction():

                    names = await conn.fetchval("SELECT array_agg(name) FROM jobs WHERE guild_id = $1", ctx.guild.id)

                    if name.isdigit():
                        if str(name) not in names:
                            return await ctx.reply("Please provide a correct job name.", ephemeral=True)

                    data = await conn.fetchrow("SELECT id, salary, description FROM jobs WHERE guild_id = $1 AND name = $2", ctx.guild.id, name)

                    if not data:
                        return await ctx.reply("The provided job doesn't exist.", ephemeral=True)
                    
                    await conn.execute("UPDATE users SET job_id = $1 WHERE user_id = $2 AND guild_id = $3 AND event_type = 'server'", data[0], ctx.author.id, ctx.guild.id)

            await self.db.fetch_table_data("jobs")
            return await ctx.reply(embed=discord.Embed(description=f"The job is set to: **{name}**", color = tv.color), mention_author=False)

    @job_set.autocomplete('name')
    async def autocomplete_callback(self, interaction: discord.Interaction, current: str):
        return await self.ac.choice_autocomplete(interaction, current, "jobs", "name", None, False)
    
    @jobs.command(name = "remove", description = "Removes member's job. | Admin-associated") # thus only one param is for admins
    async def job_remove(self, ctx: commands.Context, member: discord.Member = None):
        async with ctx.typing(ephemeral=True):
            return await self.ge.server_job_remove(ctx, member)

    @jobs.command(name = "display", description = "Displays member's current job.")
    async def display(self, ctx: commands.Context, member: discord.Member = None) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            try:
                name, salary, description, job_id =  await self.ge.fetch_basic_job_data_by_username(ctx, member)
                return await ctx.reply(embed =  discord.Embed(title="Your job", description=f"**{name}**\n*Salary:* {salary}\n*Description:* {description}", color=tv.color), mention_author=False)
            
            except TypeError:
                return

    @jobs.command(name = "work", description = "Your server work.")
    async def server_work(self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):
            return await self.be.work(ctx, "server")