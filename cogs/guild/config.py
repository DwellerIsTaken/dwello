from __future__ import annotations

from typing import Any

import asyncpg
import discord
from discord.app_commands import Choice  # noqa: F401
from discord.ext import commands

import constants as cs  # noqa: F401
from core import BaseCog, Context, Dwello, Embed


class Config(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)

        self._channel: ChannelConfig = ChannelConfig(bot)

        self.extra_help: dict[str, str] = {}  # add later for each group

    async def cog_check(self, ctx: Context) -> bool:
        return ctx.guild is not None

    @commands.hybrid_group(invoke_without_command=True, with_app_command=True)
    @commands.has_permissions(manage_channels=True, manage_messages=True)
    async def welcome(self, ctx: Context) -> discord.Message | None:
        async with ctx.typing(ephemeral=True):
            return await ctx.send_help(ctx.command)

    @welcome.group(invoke_without_command=True, with_app_command=True, name="message")
    async def welcome_mesage(self, ctx: Context):
        return ctx.send_help(ctx.command)

    @welcome.group(invoke_without_command=True, with_app_command=True, name="channel")
    async def welcome_channel(self, ctx: Context):
        return ctx.send_help(ctx.command)

    @welcome_channel.command(name="set", description="Sets chosen channel as a welcome channel.")
    async def welcome_channel_set(
        self,
        ctx: Context,
        channel: discord.TextChannel | None = commands.CurrentChannel,
    ):
        return await self._channel.add_channel(ctx, "welcome", channel)

    @welcome_mesage.command(name="set", description="You can use this command to set a welcome message.")
    async def welcome_message_set(self, ctx: Context, *, text: str):  # ,* (?)
        return await self._channel.add_message(ctx, "welcome", text)

    @welcome_mesage.command(
        name="display",
        description="Displays the current welcome message if there is one.",
    )
    async def welcome_message_display(self, ctx: Context):
        return await self._channel.message_display(ctx, "welcome")

    @welcome_channel.command(
        name="display",
        description="Displays the current welcome channel if there is one.",
    )
    async def welcome_channel_display(self, ctx: Context):
        return await self._channel.channel_display(ctx, "welcome")

    @welcome_channel.command(name="remove", description="Removes the welcome channel.")
    async def welcome_channel_remove(self, ctx: Context):
        return await self._channel.remove(ctx, "welcome")

    """@welcome.command(name="help", description="Welcome help.")
    async def help(self, ctx: Context): # maybe add a dict attribute to this class and save it like {'welcome': "extra description on formatting etc"}  # noqa: E501
        async with ctx.typing(ephemeral=True):
            help_welcome_help_embed = Embed(
                title="✨ COMPREHENSIVE WELCOME/LEAVE HELP ✨",
                description=cs.on_member_join_help_welcome_help_embed_description,
                color=cs.RANDOM_COLOR,
            )  # DEFINE THIS IN HELP CMD THEN MAKE USER CALL IT INSTEAD OR BOTH
            help_welcome_help_embed.set_image(
                url="\n https://cdn.discordapp.com/attachments/811285768549957662/989299841895108668/ggggg.png"
            )
            help_welcome_help_embed.set_footer(text=cs.FOOTER)

            return await ctx.reply(embed=help_welcome_help_embed)  # add to help cmd instead"""  # noqa: E501
    # again: add some big descriptions to help cmd, but how tho

    @commands.hybrid_group(invoke_without_command=True, with_app_command=True)
    @commands.has_permissions(manage_channels=True, manage_messages=True)  # REDO PERMS
    async def leave(self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            return ctx.send_help(ctx.command)

    @leave.group(invoke_without_command=True, with_app_command=True, name="message")
    async def leave_message(self, ctx: Context):
        return ctx.send_help(ctx.command)

    @leave.group(invoke_without_command=True, with_app_command=True, name="channel")
    async def leave_channel(self, ctx: Context):
        return ctx.send_help(ctx.command)

    @leave_channel.command(name="set", description="Sets chosen channel as a leave channel.")
    async def leave_channel_set(
        self,
        ctx: Context,
        channel: discord.TextChannel | None = commands.CurrentChannel,
    ):
        return await self._channel.add_channel(ctx, "leave", channel)

    @leave_message.command(name="set", description="You can use this command to set a leave message.")
    async def leave_message_set(self, ctx: Context, *, text: str):
        return await self._channel.add_message(ctx, "leave", text)

    @leave_message.command(
        name="display",
        description="Displays the current leave message if there is one.",
    )
    async def leave_message_display(self, ctx: Context):
        return await self._channel.message_display(ctx, "leave")

    @leave_channel.command(
        name="display",
        description="Displays the current leave channel if there is one.",
    )
    async def leave_channel_display(self, ctx: Context):
        return await self._channel.channel_display(ctx, "leave")

    @leave_channel.command(name="remove", description="Removes the leave channel.")
    async def leave_channel_remove(self, ctx: Context):
        return await self._channel.remove(ctx, "leave")

    @commands.hybrid_group(invoke_without_command=True, with_app_command=True)
    @commands.has_permissions(manage_channels=True, manage_messages=True)  # change to admin maybe
    async def twitch(self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            return ctx.send_help(ctx.command)

    @twitch.group(invoke_without_command=True, with_app_command=True, name="message")
    async def twitch_message(self, ctx: Context):
        return ctx.send_help(ctx.command)

    @twitch.group(invoke_without_command=True, with_app_command=True, name="channel")
    async def twitch_channel(self, ctx: Context):
        return ctx.send_help(ctx.command)

    @twitch_channel.command(
        name="set",
        help="Sets a channel where your twitch notifications will be posted.",
    )
    async def twitch_channel_set(
        self,
        ctx: Context,
        channel: discord.TextChannel | None = commands.CurrentChannel,
    ):
        return await self._channel.add_channel(ctx, "twitch", channel)

    @twitch_message.command(name="set", help="Sets a notification message.")
    async def twitch_message_set(self, ctx: Context, *, text: str):
        return await self._channel.add_message(ctx, "twitch", text)

    @twitch_message.command(
        name="display",
        description="Displays the current twitch message if there is one.",
    )
    async def twitch_message_display(self, ctx: Context):
        return await self._channel.message_display(ctx, "twitch")

    @twitch_channel.command(
        name="display",
        description="Displays the current twitch channel if there is one.",
    )
    async def twitch_channel_display(self, ctx: Context):
        return await self._channel.channel_display(ctx, "twitch")

    @twitch_channel.command(name="remove", description="Removes the twitch channel.")
    async def twitch_channel_remove(self, ctx: Context):
        return await self._channel.remove(ctx, "twitch")  # MAYBE REMOVE CHANNEL_REMOVE COMMS

    @twitch.command(
        name="add",
        help="Sets a twitch streamer. The notification shall be posted when the streamer goes online.",
    )
    async def add_twitch_streamer(self, ctx: commands.Context, twitch_streamer_name: str):
        return await self.bot.twitch.event_subscription(ctx, "stream.online", twitch_streamer_name)

    @twitch.command(name="list", help="Shows the list of streamers guild is subscribed to.")
    async def twitch_streamer_list(self, ctx: Context):
        return await self.bot.twitch.guild_twitch_subscriptions(ctx)

    @twitch.command(name="remove", help="Removes a twitch subscription.")
    async def twitch_streamer_remove(self, ctx: Context, username: str):  # add choice to delete all
        return await self.bot.twitch.twitch_unsubscribe_from_streamer(ctx, username)

    @twitch_streamer_remove.autocomplete("username")  # make it global
    async def autocomplete_callback_twitch_remove(self, interaction: discord.Interaction, current: str):
        return await self.bot.autocomplete.choice_autocomplete(
            interaction, current, "twitch_users", "username", "user_id", True
        )  # autocoplete per cmd or global?


# RESTRUCTURE GROUP-SUBGROUP CONNECTIONS LIKE: welcome set channel/message | welcome display channel/message (?)
# GLOBAL CHANNEL/MESSAGE DISPLAY THAT WILL SHOW MESSAGE/CHANNEL FOR EACH EVENT_TYPE (?)
# CHANNEL/MESSAGE DISPLAY FOR ALL
# TWITCH (DB) SUBSCRIPTION TO USERS (USER LIST THAT GUILD IS SUBSCRIBED TO) DISPLAY
# twitch.py IN UTILS
# MAYBE A LIST OF EVENTSUBS PER TWITCH USER (LET PEOPLE SUBSCRIBE TO OTHER EVENTS INSTEAD OF JUST SUBSCRIBING TO ON_STREAM)
# SOME IDEAS ^
# SWITCH TO TWITCHAPI LIB


# counter class (?)
class ChannelConfig:
    def __init__(self, bot: Dwello) -> None:
        self.bot: Dwello = bot

    async def add_message(self, ctx: Context, name: str, text: str) -> discord.Message | None:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                record = await conn.fetchrow(
                    "SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2",
                    ctx.guild.id,
                    name,
                )

                if (record[0] if record else None) is None:
                    return await ctx.reply(
                        f"Please use `${name} channel` first.",
                        ephemeral=True,
                        mention_author=True,
                    )  # adjust based on group/subgroup

                if not text:  # check will only work in ctx.prefix case
                    return await ctx.reply(
                        f"Please enter the {name} message, if you want to be able to use this command properly.",
                        ephemeral=True,
                        mention_author=True,
                    )

                result = await conn.fetchrow(
                    "SELECT message_text FROM server_data WHERE guild_id = $1 AND event_type = $2",
                    ctx.guild.id,
                    name,
                )

                query: str = """
                    UPDATE server_data SET message_text = $1, event_type = COALESCE(event_type, $2)
                    WHERE guild_id = $3 AND COALESCE(event_type, $2) = $2
                    """
                await conn.execute(
                    query,
                    text,
                    name,
                    ctx.guild.id,
                )
                string = f"{name.capitalize()} message has been {'updated' if result[0] else 'set'} to: ```{text}```"

        return await ctx.reply(
            embed=Embed(description=string),
            permission_cmd=True,
        )

    async def add_channel(
        self,
        ctx: Context,
        name: str,
        channel: discord.TextChannel | None = commands.CurrentChannel,
    ) -> discord.Message | None:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                result = await conn.fetchrow(
                    "SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2",
                    ctx.guild.id,
                    name,
                )

                status = "updated" if (result[0] if result else None) else "set"
                string = f"The channel has been {status} to {channel.mention}"

                if (result[0] if result else None) == channel.id:
                    return await ctx.reply(
                        f"{name.capitalize()} channel has already been set to this channel!",
                        user_mistake=True,
                    )

                # await conn.execute("UPDATE server_data SET channel_id = $1, event_type = COALESCE(event_type, $2)
                # WHERE guild_id = $3 AND COALESCE(event_type, $2) = $2", channel.id, name, ctx.guild.id)

                await conn.execute(
                    "UPDATE server_data SET channel_id = $1 WHERE guild_id = $2 AND event_type = $3",
                    channel.id,
                    ctx.guild.id,
                    name,
                )

        await channel.send(
            embed=Embed(
                description=f"This channel has been set as a *{name}* channel.",
            )
        )
        return await ctx.reply(
            embed=Embed(description=string),
            permission_cmd=True,
        )

    async def message_display(self, ctx: Context, name: str) -> discord.Message | None:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                result = await conn.fetchrow(
                    "SELECT message_text FROM server_data WHERE guild_id = $1 AND event_type = $2",
                    ctx.guild.id,
                    name,
                )

                if not (result[0] if result else None):
                    return await ctx.reply(
                        f"{name.capitalize()} message isn't yet set. \n```/{name} message set```",
                        user_mistake=True,
                    )

        return await ctx.reply(
            embed=Embed(
                title=f"{name.capitalize()} channel message",
                description=f"```{result[0]}```",
            ),
            permission_cmd=True,
        )

    async def channel_display(self, ctx: Context, name: str) -> discord.Message | None:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                result = await conn.fetchrow(
                    "SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2",
                    ctx.guild.id,
                    name,
                )

                if (result[0] if result else None) is None:
                    return await ctx.reply(
                        f"{name.capitalize()} channel isn't yet set. \n```/{name} channel set```",
                        user_mistake=True,
                    )

                # channel = discord.Object(int(result[0]))
                channel = ctx.guild.get_channel(result[0])

        return await ctx.reply(
            embed=Embed(
                description=f"{name.capitalize()} channel is currently set to {channel.mention}",
            ),
            permission_cmd=True,
        )

    async def remove(self, ctx: Context, name: str) -> discord.Message | None:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                result = await conn.fetchrow(
                    "SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2",
                    ctx.guild.id,
                    name,
                )

                if (result[0] if result else None) is None:
                    return await ctx.reply(
                        f"{name.capitalize()} channel isn't yet set. \n```/{name} channel set```",
                        user_mistake=True,
                    )

                await conn.execute(
                    "UPDATE server_data SET channel_id = NULL WHERE guild_id = $1 AND event_type = $2",
                    ctx.guild.id,
                    name,
                )
        return await ctx.reply(
            embed=Embed(
                description=f"{name.capitalize()} channel has been removed.",
            ),
            permission_cmd=True,
        )
