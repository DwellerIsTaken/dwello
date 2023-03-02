from features.required_permissions.utils.join_leave_func import join_leave_event
from features.levelling.utils import levelling
from discord.ext import commands
import text_variables as tv
import asqlite, discord
import requests, random

secret = "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"

headers = {"Content-Type":"application/json",
"Authorization":f"Bearer {secret}"}

class Events(commands.Cog, name = "Events"):

    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    #-------------------------------------------| ON_MESSAGE |-------------------------------------------#

    @commands.Cog.listener()
    async def on_message(self, message):

        #if message.author.bot:
            #return

        try:
            await levelling.create_user(message.author.id, message.guild.id)
            await levelling.increase_xp(message)
        
        except AttributeError:
            pass

        '''if message.content.startswith('+'):
            prompt = message.content.split('+')
            prompt = prompt[1]

            response = requests.post("https://api.openai.com/v1/engines/davinci/completions",json={"prompt":prompt, "temperature":0.5, "max_tokens":100},headers=headers)

            await message.reply(embed=discord.Embed(description= response.json()["choices"][0]['text'], color=discord.Color.random()), mention_author=False)'''

    #-----------------------------------------| ON_INTERACTION |-----------------------------------------#

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.interactions.Interaction):

        await levelling.create_user(interaction.user.id, interaction.guild.id)

    #------------------------------------| ON_GUILD_CHANNEL_DELETE |-------------------------------------#
    #24

    channel_type_list = ['counter_category', 'all_counter', 'members_counter', 'bots_counter']

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:
                record_list = []

                for i in self.channel_type_list:
                    await cursor.execute("SELECT channel_id FROM server_data WHERE guild_id = ? AND event_type = ?", (channel.guild.id, str(i)))
                    record = await cursor.fetchone()
                    self.record_list.append((i, record[0]))

                for j in self.record_list:
                    try:
                        if channel.id == int(j[1]):
                            await cursor.execute("UPDATE server_data SET channel_id = NULL WHERE channel_id IS NOT NULL AND guild_id = ? AND event_type = ?",(channel.guild.id, str(j[0])))

                    except TypeError:
                        pass

                await connector.commit()

    #-----------------------------------------| ON_MEMBER_JOIN |-----------------------------------------#

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await join_leave_event(self.bot, member, "welcome")

    #-----------------------------------------| ON_MEMBER_LEAVE |----------------------------------------#

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await join_leave_event(self.bot, member, "leave")

    #-----------------------------------------| ON_MEMBER_UPDATE |---------------------------------------#

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        '''https://discordpy.readthedocs.io/en/latest/api.html#discord-api-events'''

async def setup(bot):
  await bot.add_cog(Events(bot))