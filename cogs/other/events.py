from __future__ import annotations

import discord, asyncpg
from discord.ext import commands

from typing import Any
from utils import BaseCog, ListenersFunctions, LevellingUtils

class Events(BaseCog):

    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        self.levelling = LevellingUtils(self.bot)
        self.listeners = ListenersFunctions(self.bot)

        self.pool: asyncpg.Pool = self.bot.pool

    @commands.hybrid_command(name="table",with_app_command=False)
    async def test(self, ctx: commands.Context):
        await self.listeners.bot_join(ctx.guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):

        await self.listeners.bot_join(guild)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await self.levelling.increase_xp(message)

        #await levelling.get_user_data(message.author.id, message.guild.id)

        '''if message.content.startswith('+'):
            prompt = message.content.split('+')
            prompt = prompt[1]

            response = requests.post("https://api.openai.com/v1/engines/davinci/completions",json={"prompt":prompt, "temperature":0.5, "max_tokens":100},headers=headers)

            await message.reply(embed=discord.Embed(description= response.json()["choices"][0]['text'], color=discord.Color.random()), mention_author=False)'''

    '''@commands.Cog.listener()
    async def on_interaction(self, interaction: discord.interactions.Interaction):
        await levelling.create_user(interaction.user.id, interaction.guild.id)''' # because on_member_join exist | can use this as a backup

    channel_type_list = ['category', 'all', 'member', 'bot']

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        async with self.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                record_list = []

                for i in self.channel_type_list:
                    record = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = 'counter' AND counter_name = $2", channel.guild.id, str(i))
                    record_list.append((i, record[0] if record else None))

                for j in record_list:
                    try:
                        if channel.id == int(j[1]):
                            await conn.execute("UPDATE server_data SET channel_id = NULL WHERE channel_id IS NOT NULL AND guild_id = $1 AND event_type = 'counter' AND counter_name = $2", channel.guild.id, str(j[0]))

                    except TypeError as e:
                        raise e

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        await self.levelling.create_user(member.id, member.guild.id)
        await self.listeners.join_leave_event(member, "welcome")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.listeners.join_leave_event(member, "leave")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        '''https://discordpy.readthedocs.io/en/latest/api.html#discord-api-events'''

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        '''return await self.bot.pool.close()''' # THIS WAS CAUSING CLOSED POOL ISSUE