from __future__ import annotations

from .levelling import LevellingUtils as levelling
from discord.ext import commands
import text_variables as tv
import asyncpg, discord, os

from typing import Optional, Literal
from contextlib import suppress
from string import Template

class EventFunctions():
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def join_leave_event(self, bot: discord.Client, member: discord.Member, name: Literal["welcome", "leave"]) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                if name != "welcome" and name != "leave": # ?
                    raise TypeError

                result = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2", member.guild.id, name)

                if (result[0] if result else None) is None:   
                    return

                send_channel = discord.utils.get(member.guild.channels, id=int(result[0]))

                guild = member.guild

                second_result = await conn.fetchrow("SELECT message_text FROM server_data WHERE guild_id = $1 AND event_type = $2", guild.id, name)

                if str(name) == 'welcome':
                    member_welcome_embed = discord.Embed(title = "You have successfully joined the guild!", description = f"```Guild joined: {guild.name}\nMember joined: {member}\nGuild id: {guild.id}\nMember id: {member.id}```", color = discord.Color.random())
                    member_welcome_embed.set_thumbnail(url=guild.icon.url if guild.icon is not None else bot.user.display_avatar.url)
                    member_welcome_embed.set_author(name=member.name, icon_url=member.display_avatar.url if member.display_avatar is not None else bot.user.display_avatar.url)
                    member_welcome_embed.set_footer(text=tv.footer)
                    member_welcome_embed.timestamp = discord.utils.utcnow()

                    async with suppress(discord.HTTPException): await member.send(embed=member_welcome_embed)

                    if second_result[0] is None:
                        _message = f"You are the __*{len(list(member.guild.members))}th*__ user on this server. \nI hope that you will enjoy your time on this server. Have a good day!"

                    _title = f"Welcome to {member.guild.name}!"

                elif str(name) == 'leave':
                    if second_result[0] is None:
                        _message = "If you left, you had a reason to do so. Farewell, dweller!"

                    _title = f"Goodbye {member}!"

                if second_result[0] is not None:
                    _message = Template(second_result[0]).safe_substitute(members=len(list(member.guild.members)),mention=member.mention,user=member.name,guild=member.guild.name,space="\n")

                _embed = discord.Embed(title = _title, description =  _message, color = discord.Color.random())
                _embed.set_thumbnail(url= member.display_avatar.url if member.display_avatar is not None else bot.user.display_avatar.url)
                _embed.set_author(name= member.name, icon_url= member.display_avatar.url if member.display_avatar is not None else bot.user.display_avatar.url)
                _embed.set_footer(text=tv.footer)
                _embed.timestamp = discord.utils.utcnow()

        return await send_channel.send(embed=_embed)

class Events(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await levelling.increase_xp(message)

        #await levelling.get_user_data(message.author.id, message.guild.id)

        '''if message.content.startswith('+'):
            prompt = message.content.split('+')
            prompt = prompt[1]

            response = requests.post("https://api.openai.com/v1/engines/davinci/completions",json={"prompt":prompt, "temperature":0.5, "max_tokens":100},headers=headers)

            await message.reply(embed=discord.Embed(description= response.json()["choices"][0]['text'], color=discord.Color.random()), mention_author=False)'''

    '''@commands.Cog.listener()
    async def on_interaction(self, interaction: discord.interactions.Interaction):
        await levelling.create_user(interaction.user.id, interaction.guild.id)'''

    channel_type_list = ['counter_category', 'all_counter', 'members_counter', 'bots_counter']

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                record_list = []

                for i in self.channel_type_list:
                    record = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2", channel.guild.id, str(i))
                    record_list.append((i, record[0]))

                for j in record_list:
                    try:
                        if channel.id == int(j[1]):
                            await conn.execute("UPDATE server_data SET channel_id = NULL WHERE channel_id IS NOT NULL AND guild_id = $1 AND event_type = $2", channel.guild.id, str(j[0]))

                    except TypeError as e:
                        raise e

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        await levelling.create_user(member.id, member.guild.id)
        await EventFunctions.join_leave_event(self.bot, member, "welcome")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await EventFunctions.join_leave_event(self.bot, member, "leave")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        '''https://discordpy.readthedocs.io/en/latest/api.html#discord-api-events'''

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        return await self.bot.pool.close()

async def setup(bot):
  await bot.add_cog(Events(bot))