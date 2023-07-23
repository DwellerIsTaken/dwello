from __future__ import annotations

import asyncpg
import discord

from discord.ext import commands
from typing_extensions import Self
from core import BaseCog, Context, Dwello


class Events(BaseCog):
    def __init__(self, bot: Dwello):
        self.bot = bot

    '''@commands.hybrid_command(name="table", with_app_command=False)
    async def test(self, ctx: Context):
        await self.bot.listeners.bot_join(ctx.guild)'''

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.bot.listeners.bot_join(guild)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await self.bot.levelling.increase_xp(message)

        if message.content == f"<@{self.bot.user.id}>" and not message.author.bot:
            prefix: str = str(self.bot.DEFAULT_PREFIXES[0])
            content: str = f"Hello there! I'm {self.bot.user.name}. Use `{prefix}help` for more."
            if self.bot.test_instance:
                content = (
                    f"Hello there! I'm {self.bot.user.name}, the test instance of Dwello, "
                    f"but you can use me regardless. Use `{prefix}help` for more."
                )
            await message.reply(content=content)

        if message.author == self.bot.user:
            self.bot.reply_count += 1

        # await levelling.get_user_data(message.author.id, message.guild.id)
        
    @commands.Cog.listener()
    async def on_command(self, ctx: Context) -> None:
        ...
        
    @commands.Cog.listener()
    async def on_command_completion(self, ctx: Context) -> None:
        self.bot.commands_executed += 1

    """@commands.Cog.listener()
    async def on_interaction(self, interaction: discord.interactions.Interaction):
        await levelling.create_user(interaction.user.id, interaction.guild.id)"""  # because on_member_join exist | can use this as a backup  # noqa: E501

    channel_type_list = ["category", "all", "member", "bot"]

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                record_list = []

                for i in self.channel_type_list:
                    record = await conn.fetchrow(
                        "SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = 'counter' AND counter_name = $2",  # noqa: E501
                        channel.guild.id,
                        str(i),
                    )
                    record_list.append((i, record[0] if record else None))

                for j in record_list:
                    try:
                        if channel.id == int(j[1]):
                            await conn.execute(
                                "UPDATE server_data SET channel_id = NULL WHERE channel_id IS NOT NULL AND guild_id = $1 AND event_type = 'counter' AND counter_name = $2",  # noqa: E501
                                channel.guild.id,
                                str(j[0]),
                            )

                    except TypeError as e:
                        raise e

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.bot.levelling.create_user(member.id, member.guild.id)
        await self.bot.listeners.join_leave_event(member, "welcome")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.bot.listeners.join_leave_event(member, "leave")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """https://discordpy.readthedocs.io/en/latest/api.html#discord-api-events"""

    @commands.Cog.listener()
    async def on_disconnect(self: Self) -> None:
        """return await self.bot.pool.close()"""  # THIS WAS CAUSING CLOSED POOL ISSUE
