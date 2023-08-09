from __future__ import annotations

from typing import Any, Literal

import asyncpg
import discord
from string import Template
from discord.ext import commands
from typing_extensions import Self

import constants as cs
from utils import User
from .tasks import update_counters
from core import BaseCog, Context, Dwello


class Events(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self.listeners = ListenerFunctions(self.bot)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.listeners.bot_join(guild)

    # ADD THIS TO USER CUSTOMISATION
    # THUS ONLY SEND IF ENABLED
    # https://discord.com/channels/822162578653577336/1081039402945478666/1138587797645697074
    #|xp until next level
    """level_embed_dis = f"*Your new level is: {new_level}*\n*Xp until your next level: {xp_till_next_level}*"

    level_embed = discord.Embed(
        title="Congratulations with your new level!",
        description=string.Template(level_embed_dis).safe_substitute(member=message.author.name),
    )

    level_embed.set_thumbnail(url=f"{message.author.display_avatar}")
    level_embed.set_author(
        name=f"{message.author.name}",
        icon_url=f"{message.author.display_avatar}",
    )
    level_embed.set_footer(text=f"{message.guild.name}")
    level_embed.timestamp = discord.utils.utcnow()"""

    # async with suppress(discord.HTTPException): await message.author.send(embed=level_embed)

    """try:
        await message.author.send(embed=level_embed)

    except discord.HTTPException:
        pass"""

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        user = await self.bot.db.create_user(message.author.id)
        await user.increase_xp(message) # user not being created in the func

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

    @commands.Cog.listener()
    async def on_command(self, ctx: Context) -> None:
        ...

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: Context) -> None:
        ctx.bot.commands_executed += 1
        return

    """@commands.Cog.listener()
    async def on_interaction(self, interaction: discord.interactions.Interaction):
        await levelling.create_user(interaction.user.id, interaction.guild.id)"""  # because on_member_join exist | can use this as a backup  # noqa: E501

    channel_type_list = ["category", "all", "member", "bot"]

    @commands.Cog.listener() # kinda fix
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
        await User.create(member.id, self.bot)
        await self.listeners.join_leave_event(member, "welcome")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.listeners.join_leave_event(member, "leave")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """https://discordpy.readthedocs.io/en/latest/api.html#discord-api-events"""

    @commands.Cog.listener()
    async def on_disconnect(self: Self) -> None:
        """return await self.bot.pool.close()"""  # THIS WAS CAUSING CLOSED POOL ISSUE


class ListenerFunctions:
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot

    async def bot_join(self, guild: discord.Guild) -> None:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                counter_names = ["all", "member", "bot", "category"]
                event_types = ["welcome", "leave", "twitch"]
                # counter_names = [counter if counter is not None else 'Not Specified' for counter in counter_names]
                await conn.executemany(
                    "INSERT INTO server_data(guild_id, counter_name, event_type) VALUES($1, $2, $3)",
                    [(guild.id, "Disabled", event) for event in event_types],
                )
                return await conn.executemany(
                    "INSERT INTO server_data(guild_id, counter_name, event_type) VALUES($1, $2, $3)",
                    [(guild.id, counter, "counter") for counter in counter_names],
                )
                # ADD SOME WELCOME MESSAGE FROM BOT OR SMTH

    # fix the whole func again?
    # again: counter class maybe?
    async def join_leave_event(self, member: discord.Member, name: Literal["welcome", "leave"]) -> discord.Message | None:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                await update_counters(member.guild)

                # adjust counters too in this event

                result = await conn.fetchrow(
                    "SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2",
                    member.guild.id,
                    name,
                )

                if not (result[0] if result else None):
                    return

                send_channel = discord.utils.get(member.guild.channels, id=int(result[0]))  # type: ignore

                guild = member.guild

                second_result = await conn.fetchrow(
                    "SELECT message_text FROM server_data WHERE guild_id = $1 AND event_type = $2",
                    guild.id,
                    name,
                )

                if str(name) == "welcome":
                    member_welcome_embed = discord.Embed(
                        title="You have successfully joined the guild!",
                        description=(
                            f"```Guild joined: {guild.name}\nMember joined: {member}\n"
                            f"Guild id: {guild.id}\nMember id: {member.id}```"
                        ),
                        color=discord.Color.random(),
                    )
                    member_welcome_embed.set_thumbnail(
                        url=guild.icon.url if guild.icon else self.bot.user.display_avatar.url  # type: ignore
                    )
                    member_welcome_embed.set_author(
                        name=member.name,
                        icon_url=member.display_avatar.url
                        if member.display_avatar
                        else self.bot.user.display_avatar.url,  # type: ignore
                    )
                    member_welcome_embed.set_footer(text=cs.FOOTER)
                    member_welcome_embed.timestamp = discord.utils.utcnow()

                    try:
                        await member.send(embed=member_welcome_embed)

                    except discord.HTTPException as e:
                        print(e)

                    if not second_result[0]:  # type: ignore
                        _message = (
                            f"You are the __*{len(list(member.guild.members))}th*__ user on this server.\n"
                            "I hope that you will enjoy your time on this server. Have a good day!"
                        )

                    _title = f"Welcome to {member.guild.name}!"

                elif str(name) == "leave":
                    if not second_result[0]:
                        _message = "If you left, you had a reason to do so. Farewell, dweller!"

                    _title = f"Goodbye {member}!"

                if second_result[0]:
                    _message = Template(second_result[0]).safe_substitute(
                        members=len(list(member.guild.members)),
                        mention=member.mention,
                        user=member.name,
                        guild=member.guild.name,
                        space="\n",
                    )

                _embed = discord.Embed(title=_title, description=_message, color=discord.Color.random())
                _embed.set_thumbnail(url=member.display_avatar.url)
                _embed.set_author(name=member.name, icon_url=member.display_avatar.url)
                _embed.set_footer(text=cs.FOOTER)
                _embed.timestamp = discord.utils.utcnow()

        return await send_channel.send(embed=_embed)
