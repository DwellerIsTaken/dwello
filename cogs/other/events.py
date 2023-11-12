from __future__ import annotations

from typing import Any, Literal

import re
import io
import sys
import time
import asyncio
import difflib
import discord
import traceback
from contextlib import suppress
from string import Template
from discord.ext import commands
from typing_extensions import Self
from asyncio import to_thread

from constants import PERMISSIONS_URL, WARNING_COLOR
from utils import User, Guild, get_welcome_card, extract_ids_from_discord_message_link
from core import BaseCog, Context, Dwello, Embed


class Events(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)

    async def send_welcome_or_leave_message(
        self, member: discord.Member, _type: Literal["welcome", "leave"],
    ) -> discord.Message | None:
        guild = member.guild
        welcome = _type == "welcome"

        await self.bot.db.update_counters(guild)

        _guild = await Guild.get(guild.id, self.bot)
        _channel = _guild.get_channel_by_type(_type)

        _message = _channel.message if _channel else None
        if _message:
            _message = Template(_message).safe_substitute(
                members=len(list(member.guild.members)),
                mention=member.mention,
                user=member.name,
                guild=member.guild.name,
                space="\n",
            ) # write a clear help guide on this

        file = None
        if welcome:
            with suppress(discord.HTTPException):
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
            if not _message:
                _message = (
                    f"You are the __*{len(list(member.guild.members))}th*__ user on this server.\n"
                    "I hope that you will enjoy your time on this server. Have a good day!" # maybe randomize it a bit | ->
                    #pick random one from constants
                )
            _title = f"Welcome to {member.guild.name} {member.name}!"

            buffer = io.BytesIO()
            image = await to_thread(get_welcome_card, _title, member.display_avatar.url)
            image.save(buffer, format="PNG")
            buffer.seek(0)
            file: discord.File = discord.File(buffer, "welcome.png")
        else:
            if not _message:
                _message = "If you left, you had a reason to do so. Farewell, dweller!" # better sentence
            _title = f"Goodbye {member.name}!"

        channel = guild.get_channel(_channel.id)
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

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await Guild.create(guild.id, self.bot)
        #await self.listeners.bot_join(guild)

    # ADD THIS TO USER CUSTOMISATION
    # THUS ONLY SEND IF ENABLED
    # USER_CONFIG DICT
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
        if not message.author.bot: # sometimes get the NoneType error
            _user = await User.get(message.author.id, self.bot)
            await _user.increase_xp(message)

        #with suppress(AttributeError):
        #await Guild.get(message.guild.id, self.bot) # for now

        try:
            _guild = await Guild.get(message.guild.id, self.bot)
        except AttributeError:
            _guild = None
            
        if message.content == f"<@{self.bot.user.id}>" and not message.author.bot:
            prefix: str = str(self.bot.DEFAULT_PREFIXES[0])
            content: str = f"Hello there! I'm {self.bot.user.name}. Use `{prefix}help` for more."
            if self.bot.test_instance:
                content = (
                    f"Hello there! I'm {self.bot.user.name}, the test instance of Dwello, "
                    f"but you can use me regardless. Use `{prefix}help` for more."
                )
            await message.reply(content=content)

        # turns message link into an embed
        # should be customised
        if _guild and _guild.turn_link_into_message:  # noqa: SIM102
            if match:= re.compile(r"https?://(.+)?.?discord\.com/channels/\d+/\d+/\d+").search(message.content):
                link = match.group()
                guild_id, channel_id, message_id = extract_ids_from_discord_message_link(link)
                if (
                    guild_id == message.guild.id
                    and (msg := await self.bot.get_or_fetch_message(channel_id, message_id))
                    and (not msg.channel.is_nsfw() or (msg.channel.is_nsfw() and message.channel.is_nsfw()))
                    and msg.content
                ):
                    content_preview = msg.content[:300] + ('...' if len(msg.content) > 300 else '')
                    await message.channel.send(
                        embed=Embed(description=f"**Contents**\n{content_preview}")
                        .set_author(name=msg.author.name, icon_url=msg.author.display_avatar.url)
                        .add_field(name="Message", value=f"[Jump!](<{msg.jump_url}>)")
                    )

        if message.author == self.bot.user:
            self.bot.reply_count += 1

    cmd_execution_times: dict[str, float] = {}

    def _key(self, ctx: Context) -> str:
        return '-'.join(
            map(str, [ctx.guild.id, ctx.channel.id, ctx.message.id] if ctx.guild else [ctx.channel.id, ctx.message.id])
        )

    @commands.Cog.listener()
    async def on_command(self, ctx: Context) -> None:
        self.cmd_execution_times[self._key(ctx)] = time.monotonic()

        #await self.bot.reaction_typing(ctx.message)
        # await ctx.message.add_reaction(TYPING_EMOJI)
        # typing may be added and removed too fast that for some cmds it wouldn't matter to have it
        # so maybe do smh like async with ctx.add_typing_reaction lol
        # so you would have the reaction instead of actuall discord typing (because it can only be ephemeral
        # or not, but not both); and when finished you can add white mark as a reaction ig
        # but probably just have that typing reaction while smh is happening within `async with ctx.typing_reaction`

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: Context) -> None:
        value = (time.monotonic() - self.cmd_execution_times.pop(self._key(ctx))) * 1000
        self.bot.execution_times = [value] + self.bot.execution_times[:99]
        ctx.command.extras["execution_times"] = [value] + ctx.command.extras["execution_times"][:24]
        # this basically stores starting time in a dict with three ids (a single string) as a key
        # when the starting time is extracted the item is removed from dict
        # then the final time is stored as float in milliseconds in bot's list and await Guild.get(self.guild.id, self.bot)
        # in ctx.command's extras dictionary

        ctx.command.extras["times_executed"] += 1
        ctx.bot.commands_executed += 1 # could just iterate through all cmds and get their "times_executed" in extras

        _guild = await Guild.get(ctx.guild.id, self.bot)

        if _guild.reactions_on_command:
            with suppress(discord.NotFound):
                await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await (await User.get(ctx.author.id, self.bot)).increase_command_count() # setter maybe?

        await asyncio.sleep(_guild.delete_reaction_after)
        with suppress(discord.Forbidden, discord.NotFound):
            await ctx.message.clear_reaction("\N{WHITE HEAVY CHECK MARK}")
        # maybe get that specific reaction got by the bot
        # too much brainfuckery tho
        return
    
    @commands.Cog.listener("on_command_completion")
    async def on_command_completion_invoker_msg_deletion(self, ctx: Context) -> None:
        _guild = await Guild.get(ctx.guild.id, ctx.bot)
        if _guild.delete_invoker_message and ctx.me.guild_permissions.manage_messages:
            await asyncio.sleep(_guild.delete_invoker_message_after) if _guild.delete_invoker_message_after else 0.0
            await ctx.message.delete()

    """@commands.Cog.listener()
    async def on_interaction(self, interaction: discord.interactions.Interaction):
        await levelling.create_user(interaction.user.id, interaction.guild.id)"""  # because on_member_join exist | can use this as a backup  # noqa: E501

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        await self.bot.db.remove_counter(channel)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await User.get(member.id, self.bot)
        await self.send_welcome_or_leave_message(member, "welcome")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.send_welcome_or_leave_message(member, "leave")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """https://discordpy.readthedocs.io/en/latest/api.html#discord-api-events"""

    @commands.Cog.listener()
    async def on_disconnect(self: Self) -> None:
        """return await self.bot.pool.close()"""  # THIS WAS CAUSING CLOSED POOL ISSUE

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: Exception) -> discord.Message | None:
        """The event triggered when an error is raised while invoking a command.
        Parameters
        ------------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
        """

        _guild = await Guild.get(ctx.guild.id, self.bot)

        with suppress(KeyError, discord.Forbidden):
            self.cmd_execution_times.pop(self._key(ctx))
            await ctx.message.clear_reactions()
        # manage messages perm required
        if _guild.reactions_on_command:
            await ctx.message.add_reaction("\N{CROSS MARK}")

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, "on_error"):
            return

        if (cog := ctx.cog) and cog._get_overridden_method(cog.cog_command_error) is not None:
            return

        ignored = ()  # make that a check or no ?

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, "original", error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return
        
        match type(error):
            case commands.CommandNotFound:
                if (
                    _guild.cmd_matches and ctx.prefix and ctx.bot.all_commands
                    and (content:=ctx.message.content[len(ctx.prefix):])
                    and (matches:= difflib.get_close_matches(content, ctx.bot.all_commands.keys()))
                ):
                    return await ctx.reply("**Did you mean...**\n" + "\n".join(matches))
                return
            
            case commands.MissingRequiredArgument:
                return await ctx.reply(error, user_mistake=True)
            
            case commands.DisabledCommand:
                return await ctx.reply(f"{ctx.command} has been disabled.", user_mistake=True)
            
            case commands.NoPrivateMessage:
                with suppress(discord.HTTPException):
                    return await ctx.author.send(f"{ctx.command} can not be used in Private Messages.")
                
            case commands.MissingPermissions:
                return await ctx.reply(
                    embed=Embed(
                        title="Permission Denied.",
                        color=WARNING_COLOR,
                        description=(
                            "You don't have permission to use this command.\n"
                            "You should have the following permission(s) to use this command:\n"
                            +"\n".join([f"• [`{perm}`]({PERMISSIONS_URL}.{perm})" for perm in error.missing_permissions])
                        ),
                    )
                    .set_image(url="https://media.tenor.com/bIJa2uRURiQAAAAd/lord-of-the-rings-you-shall-not-pass.gif"),
                    user_mistake=True,
                )
            
            case commands.MemberNotFound:
                return await ctx.reply(error, user_mistake=True)

            case commands.BadArgument:
                return await ctx.reply(error, user_mistake=True)

            case commands.CheckFailure:
                ...

            case commands.CommandOnCooldown:
                return await ctx.reply(f"You are on cooldown. Try again in {error.retry_after:.2f}s", user_mistake=True)

            case commands.BotMissingPermissions:
                return await ctx.reply(
                    embed=Embed(
                        title="Permission Denied.",
                        color=WARNING_COLOR,
                        description=(
                            f"{self.bot.user.name} doesn't have the necessary permissions to use this command.\n"
                            "It should have the following permission(s) to use this command:\n"
                            +"\n".join([f"• [`{perm}`]({PERMISSIONS_URL}.{perm})" for perm in error.missing_permissions])
                        ),
                    ), user_mistake=True,
                )

        # All other Errors not returned come here. And we can just print the default TraceBack.
        # self.bot.logger.error("An error occurred", exc_info=error) report error to special log TODO

        guild: str = f"Guild ID: {ctx.guild.id}\n" if ctx.guild else ""
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        return await ctx.reply(
            embed=Embed(
                title=f"Ignoring exception in {ctx.command}:",
                description=f"```py\n{error}```\nThe developers have receieved this error and will fix it.",
                color=0xF02E2E,
            )
            .add_field(
                name="Information",
                value=(
                    f"Error Name: {type(error).__name__}\nError Type: {type(error)}\n"
                    f"Message: {ctx.message.content}\n{guild}Channel ID: {ctx.channel.id}"
                ),
            )
            .set_author(name=f"{ctx.author.name}", icon_url=ctx.author.display_avatar),
        )
    
