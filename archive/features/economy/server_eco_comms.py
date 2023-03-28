from features.economy.utils.server_attributes import *
from features.economy.utils.common_attributes import *
from utils.db_operations import DB_Operations as db
from discord.app_commands import Choice
from discord.ext import commands
import text_variables as tv
import asqlite, discord

class WorkingClass(commands.Cog, name = "WorkingClass"):

    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    #jobs -- lots of available jobs

    @commands.hybrid_group(name="server",invoke_without_command=True,with_app_command=True)
    async def server(self,ctx):

        embed = discord.Embed(title="Denied", description="Use `$server [subgroup name]` instead.",color=tv.color)

        return await ctx.reply(embed=embed)

    @server.group(name="job",invoke_without_command=True,with_app_command=True)
    async def jobs(self,ctx):

        embed = discord.Embed(title="Denied", description="Use `$job list` instead.",color=tv.color)

        return await ctx.reply(embed=embed)

    @jobs.command(name = "list", description = "Shows a list of available jobs on the server set by the server administrator.")
    async def job_list(self, ctx):
        
        embed = await jobs_display(ctx)
        await ctx.reply(embed = embed, mention_author = False) # if isinstance(embed, list) else embed

    @jobs.command(name = "create", description = "Creating jobs. Only for administrator!")
    #@discord.app_commands.rename(name='job_name') #\U00000020
    @commands.has_permissions(administrator = True)
    async def job_create(self, ctx, job_name: str, salary: commands.Range[int, 2000, 20000], job_description: str = None):
        
        await server_job_create(ctx, job_name, salary, job_description)
        self.bot.jobs_data = await db.fetch_job_data()

    @jobs.command(name = "remove", description = "Removing jobs. Only for administrator!")
    @commands.has_permissions(administrator = True)
    async def job_remove(self, ctx, job_name: str):
        
        await server_job_remove(ctx, job_name)
        self.bot.jobs_data = await db.fetch_job_data()

    @job_remove.autocomplete('job_name')
    async def autocomplete_callback(self, interaction: discord.Interaction, current: str):
        async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:

                await cursor.execute("SELECT id, name FROM jobs WHERE guild_id = ?",(interaction.guild.id))

                choices = []
                item = len(current)

                choices.append(Choice(name = "all", value = "all"))

                async for id, name in cursor:
                    #job_id = record["job_id"]
                    #job_name = record["jobs"]

                    if id is None:
                        if name is None:
                            continue

                    if current:
                        pass

                    if current.startswith(str(name).lower()[:int(item)]):
                        choices.append(Choice(name = str(name), value = int(id)))
                        pass
                        
                    elif current.startswith(str(id)[:int(item)]):
                        choices.append(Choice(name = str(name), value = int(id)))
                        pass

                if len(choices) > 5:
                    return choices[:5]

                return choices

    @jobs.command(name = "set", description = "You can set your server job here!")
    async def job_set(self, ctx, job_name: str):
        async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:

                await cursor.execute("SELECT id, name FROM jobs WHERE guild_id = ?",(ctx.guild.id))
                data = await cursor.fetchall()
                check = 0

                for record in data:
                    name, id = record['name'], record['id']
                    if job_name == str(name) or int(job_name if job_name.isdigit() else False) == int(id):
                        await cursor.execute("UPDATE users SET job_id = ? WHERE user_id = ? AND guild_id = ? AND event_type = ?",(id, ctx.message.author.id, ctx.guild.id,"server"))
                        check += 1

                        break

                    else:
                        continue
                
                if check == 0:
                    return await ctx.reply("The provided job doesn't exist.")

                await ctx.reply(embed=discord.Embed(description=f'The job is set to: **{name}**', color = tv.color),mention_author=False)
                self.bot.jobs_data = await db.fetch_job_data()

            await connector.commit()


    @job_set.autocomplete('job_name')
    async def autocomplete_callback(self, interaction: discord.Interaction, current: str):
        async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:

                #DICT STRUCTURE: {guild_id: {'name': [], 'id': [], 'salary': [], 'description': []}}
                d = self.bot.jobs_data

                choices = []
                item = len(current)
                new_list = [(str(d[int(interaction.guild.id)]['name'][i]), int(d[int(interaction.guild.id)]['id'][i])) for i in range(len(d[int(interaction.guild.id)]['id']))]

                for record in new_list:
                    name, id = str(record[0]), int(record[1])

                    if id is None:
                        if name is None:
                            continue

                    if current:
                        pass

                    if current.startswith(name.lower()[:int(item)]):
                        choices.append(Choice(name = name, value = str(id)))
                        pass
                        
                    elif current.startswith(name[:int(item)]):
                        choices.append(Choice(name = name, value = str(id)))
                        pass

                if len(choices) > 5:
                    return choices[:5]

                return choices

    @jobs.command(name = "display", description = "Displays member's current job!")
    async def server_user_job_display(self, ctx, member: discord.Member = None):

        name, salary, description =  await server_job_info(ctx, member)
        embed = discord.Embed(title="Your job", description=f"**{name}**\n*Salary:* {salary}\n*Description:* {description}", color=tv.color)
        failure_embed = discord.Embed(title="You have no job!", description="> Go on and get it!", color=tv.color)
        await ctx.reply(embed if name else failure_embed ,mention_author=False) #*ID:* `{job[1]}`

    @jobs.command(name = "work", description = "Your server work.")
    async def server_work(self, ctx):
        
        await work(ctx, "server")

async def setup(bot):
  await bot.add_cog(WorkingClass(bot))