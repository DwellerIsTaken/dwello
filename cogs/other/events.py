from __future__ import annotations

from typing import Any

import asyncpg
import discord
from discord.ext import commands
from typing_extensions import Self

from bot import Dwello, DwelloContext
from utils import BaseCog


class Events(BaseCog):
    def __init__(self: Self, bot: Dwello, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)

    @commands.hybrid_command(name="table", with_app_command=False)
    async def test(self: Self, ctx: DwelloContext):
        await self.bot.listeners.bot_join(ctx.guild)

    @commands.Cog.listener()
    async def on_guild_join(self: Self, guild: discord.Guild):
        await self.bot.listeners.bot_join(guild)

    @commands.Cog.listener()
    async def on_message(self: Self, message: discord.Message) -> None:
        await self.bot.levelling.increase_xp(message)

        if message.content == f"<@{self.bot.user.id}>" and not message.author.bot:
            content: str = (
                f"Hello there! I'm {self.bot.user.name}. Use `dw.help` for more."
            )
            await message.reply(content=content)

        if message.author == self.bot.user:
            self.bot.reply_count += 1

        # await levelling.get_user_data(message.author.id, message.guild.id)

        """if message.content.startswith('+'):
            prompt = message.content.split('+')
            prompt = prompt[1]

            response = requests.post("https://api.openai.com/v1/engines/davinci/completions",json={"prompt":prompt, "temperature":0.5, "max_tokens":100},headers=headers)

            await message.reply(embed=discord.Embed(description= response.json()["choices"][0]['text'], color=discord.Color.random()), mention_author=False)"""

    """@commands.Cog.listener()
    async def on_interaction(self, interaction: discord.interactions.Interaction):
        await levelling.create_user(interaction.user.id, interaction.guild.id)"""  # because on_member_join exist | can use this as a backup

    channel_type_list = ["category", "all", "member", "bot"]

    @commands.Cog.listener()
    async def on_guild_channel_delete(
        self: Self, channel: discord.abc.GuildChannel
    ) -> None:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                record_list = []

                for i in self.channel_type_list:
                    record = await conn.fetchrow(
                        "SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = 'counter' AND counter_name = $2",
                        channel.guild.id,
                        str(i),
                    )
                    record_list.append((i, record[0] if record else None))

                for j in record_list:
                    try:
                        if channel.id == int(j[1]):
                            await conn.execute(
                                "UPDATE server_data SET channel_id = NULL WHERE channel_id IS NOT NULL AND guild_id = $1 AND event_type = 'counter' AND counter_name = $2",
                                channel.guild.id,
                                str(j[0]),
                            )

                    except TypeError as e:
                        raise e

    @commands.Cog.listener()
    async def on_member_join(self: Self, member: discord.Member):
        await self.bot.levelling.create_user(member.id, member.guild.id)
        await self.bot.listeners.join_leave_event(member, "welcome")

    @commands.Cog.listener()
    async def on_member_remove(self: Self, member: discord.Member):
        await self.bot.listeners.join_leave_event(member, "leave")

    @commands.Cog.listener()
    async def on_member_update(self: Self, before, after):
        """https://discordpy.readthedocs.io/en/latest/api.html#discord-api-events"""

    @commands.Cog.listener()
    async def on_disconnect(self: Self) -> None:
        """return await self.bot.pool.close()"""  # THIS WAS CAUSING CLOSED POOL ISSUE
