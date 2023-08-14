from __future__ import annotations

from typing import Any, Literal

import io
import discord
import contextlib
from string import Template
from discord.ext import commands
from typing_extensions import Self
from asyncio import to_thread

from utils import User, Guild, get_welcome_card
from .tasks import update_counters
from core import BaseCog, Context, Dwello, Embed


class Events(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self.listeners = ListenerFunctions(self.bot)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await Guild.create(guild.id, self.bot)
        #await self.listeners.bot_join(guild)

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

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        guild = channel.guild
        _guild = await Guild.get(guild.id, self.bot)

        if channel.id in _guild.counters_dict:
            async with self.bot.safe_connection() as conn: # shouldn't use f-strings in sql maybe fix very later
                query = f"UPDATE guilds SET {_guild.counters_dict[channel.id]} = NULL WHERE id = $1"
                await conn.execute(query, guild.id)
        return

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await User.create(member.id, self.bot)
        await Guild.create(member.guild.id, self.bot) # for now
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

    # again: counter class maybe?
    async def join_leave_event(self, member: discord.Member, name: Literal["welcome", "leave"]) -> discord.Message | None:
        guild = member.guild

        #await update_counters(guild) fix later

        _guild = await Guild.get(guild.id, self.bot)

        _message = _guild.welcome_message if name == "welcome" else _guild.leave_message or None
        if _message:
            _message = Template(_message).safe_substitute(
                members=len(list(member.guild.members)),
                mention=member.mention,
                user=member.name,
                guild=member.guild.name,
                space="\n",
            ) # write a clear help guide on this

        if name == "welcome":
            with contextlib.suppress(discord.HTTPException):
                await member.send(
                    embed=Embed(
                        title="You have successfully joined the guild!",
                        timestamp=discord.utils.utcnow(),
                        description=(
                            f"```Guild joined: {guild.name}\nMember joined: {member.name}\n"
                            f"Guild id: {guild.id}\nMember id: {member.id}```"
                        ),
                    )
                    .set_thumbnail(url=guild.icon.url if guild.icon else self.bot.user.display_avatar.url)
                    .set_author(
                        name=member.name,
                        icon_url=member.display_avatar.url if member.display_avatar else self.bot.user.display_avatar.url,
                    )
                )
            if not _guild.welcome_message:
                _message = (
                    f"You are the __*{len(list(member.guild.members))}th*__ user on this server.\n"
                    "I hope that you will enjoy your time on this server. Have a good day!" # maybe randomize it a bit | ->
                    #pick random one from constants
                )
            _title = f"Welcome to {member.guild.name} {member.name}!"
        else:
            if not _guild.leave_message:
                _message = "If you left, you had a reason to do so. Farewell, dweller!" # better sentence
            _title = f"Goodbye {member.name}!"

        buffer = io.BytesIO()
        image = await to_thread(get_welcome_card, _title, member.display_avatar.url)
        image.save(buffer, format="PNG")
        buffer.seek(0)
        file: discord.File = discord.File(buffer, "welcome.png")

        #channel = guild.get_channel(_guild.welcome_channel_id if name == "welcome" else _guild.leave_channel_id) fix config.py
        channel = guild.get_channel(1080884328923414619)
        return await channel.send(
            embed=Embed(
                title=_title,
                description=_message,
                timestamp=discord.utils.utcnow(),
            )
            .set_thumbnail(url=member.display_avatar.url)
            .set_author(name=member.name, icon_url=member.display_avatar.url)
            .set_image(url="attachment://welcome.png"),
            file=file,
        )
