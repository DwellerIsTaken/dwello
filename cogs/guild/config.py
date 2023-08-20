from __future__ import annotations

from typing import Any

import discord
from discord.ext import commands
from discord.ui import Modal, TextInput

import constants as cs  # noqa: F401
from core import BaseCog, Context, Dwello, Embed
from utils import Guild, GuildChannel


class EditChannelMessageModal(Modal, title="Edit channel message."):
    """This modal is only called when the message for a channel isn't provided."""

    # maybe add title for the welcome message embed
    # maybe do that in customisation instead
    # like, modal, so the user would be construct the embed themselves
    # title for welcome embed, description, maybe even on/off button for banner that will be generated
    # same for embed author etc
    # maybe not cause there should also be like a general embed config by user
    content: TextInput = TextInput(
        label="Content (optional)",
        required=False,
        min_length=1,
        max_length=1000,
        style=discord.TextStyle.long,
        placeholder=f"Example:\n{cs.EXAMPLE_WELCOME_MESSAGE}",
    )

    def __init__(self, cog: Config, channel: GuildChannel) -> None:
        super().__init__()

        self.cog: Config = cog
        self.channel: GuildChannel = channel

        self.content.default = channel.message or ""

    async def on_submit(self, interaction: discord.Interaction) -> None:
        content = self.content
        channel = self.channel
        value = content.value or None
        await channel.guild.add_message(channel.type, value)
        await interaction.response.send_message(
            f"Done, the message now is:\n> {value or content.placeholder}", ephemeral=True,
        )


class Config(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)

        self.extra_help: dict[str, str] = {}  # add later for each group

    async def cog_check(self, ctx: Context) -> bool:
        return ctx.guild is not None
    
    async def _add_message(self, ctx: Context, _type: str, text: str = None) -> discord.Message | None:
        _guild = await Guild.get(ctx.guild.id, self.bot)
        _channel = _guild.get_channel_by_type(_type)

        if not text and ctx.interaction and _channel:
            await ctx.interaction.response.send_modal(EditChannelMessageModal(self, _channel))
            return
        else:
            if not _channel or not _channel.id:
                return await ctx.reply(
                    content=f"{_type.capitalize()} channel isn't yet set.",
                    embed=Embed(
                        description=(
                            "## But how do I set it?\n"
                            "Like this:"
                            f"```{self.bot.main_prefix}{_type} channel set```"
                        ),
                    ),
                    user_mistake=True,
                ) # i mean, u should be able to set a message without a channel, but this is like a reminder smh
        await _guild.add_message(_type, text)
        return await ctx.reply(
            embed=Embed(
                description=f"{_type.capitalize()} message has been {'updated' if _channel.text else 'set'} to: ```{text}```"
            ),
            permission_cmd=True,
        )

    async def _add_channel(
        self,
        ctx: Context,
        _type: str,
        channel: discord.TextChannel | commands.CurrentChannel,
        /,
        notify_in_channel: bool = False,
    ) -> discord.Message | None:
        _guild = await Guild.get(ctx.guild.id, self.bot)
        _channel = _guild.get_channel_by_type(_type)

        _channel_id = _channel.id if _channel else None

        string = f"The channel has been {'updated' if _channel_id else 'set'} to {channel.mention}."

        if _channel_id == channel.id:
            return await ctx.reply(
                f"{_type.capitalize()} channel has already been set to this channel!",
                user_mistake=True,
            )
        await _guild.add_channel(_type, channel.id)
        if notify_in_channel:
            await channel.send(
                embed=Embed(
                    description=f"This channel has been set as a *{_channel.name.lower()}* channel.",
                )
            )
        return await ctx.reply(embed=Embed(description=string), permission_cmd=True)

    async def _message_display(self, ctx: Context, _type: str) -> discord.Message | None:
        _guild = await Guild.get(ctx.guild.id, self.bot)
        _channel = _guild.get_channel_by_type(_type)
        _message = _channel.text if _channel else None

        if not _message:
            return await ctx.reply(
                content=f"{_type.capitalize()} message isn't yet set.",
                embed=Embed(
                    description=(
                        "## But how do I set it?\n"
                        "Like this:"
                        f"```{self.bot.main_prefix}{_type} message set```"
                    ),
                ),
                user_mistake=True,
            )
        return await ctx.reply(
            embed=Embed(
                title=f"{_type.capitalize()} message",
                description=f"```{_message}```", # maybe different output style?
            ),
            permission_cmd=True,
        )

    async def _channel_display(self, ctx: Context, _type: str) -> discord.Message | None:
        _guild = await Guild.get(ctx.guild.id, self.bot)
        _channel = _guild.get_channel_by_type(_type)
        _id = _channel.id if _channel else None

        if not _id:
            return await ctx.reply(
                content=f"{_type.capitalize()} channel isn't yet set.",
                embed=Embed(
                    description=(
                        "## But how do I set it?\n"
                        "Like this:"
                        f"```{self.bot.main_prefix}{_type} channel set```"
                    ),
                ),
                user_mistake=True,
            )
        return await ctx.reply(
            embed=Embed(
                description=f"{_type.capitalize()} channel is currently set to <#{_channel.id}>.",
            ),
            permission_cmd=True,
        )

    async def _remove(self, ctx: Context, _type: str) -> discord.Message | None:
        _guild = await Guild.get(ctx.guild.id, self.bot)
        
        if _channel:= _guild.get_channel_by_type(_type):
            await _channel.remove()
        else:
            return await ctx.reply(
                content=f"{_type.capitalize()} channel isn't yet set.",
                embed=Embed(
                    description=(
                        "## But how do I set it?\n"
                        "Like this:"
                        f"```{self.bot.main_prefix}{_type} channel set```"
                    ),
                ),
                user_mistake=True,
            )
        return await ctx.reply(
            embed=Embed(
                description=f"{_channel.name} channel has been removed.",
            ),
            permission_cmd=True,
        )

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
        return await self._add_channel(ctx, "welcome", channel)

    @welcome_mesage.command(name="edit", description="You can use this command to set a welcome message.")
    async def welcome_message_set(self, ctx: Context, *, text: str = None):  # if not text trigger modal
        return await self._add_message(ctx, "welcome", text)

    @welcome_mesage.command(
        name="display",
        description="Displays the current welcome message if there is one.",
    )
    async def welcome_message_display(self, ctx: Context):
        return await self._message_display(ctx, "welcome")

    @welcome_channel.command(
        name="display",
        description="Displays the current welcome channel if there is one.",
    )
    async def welcome_channel_display(self, ctx: Context):
        return await self._channel_display(ctx, "welcome")

    @welcome_channel.command(name="remove", description="Removes the welcome channel.")
    async def welcome_channel_remove(self, ctx: Context):
        return await self._remove(ctx, "welcome")

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
        return await self._add_channel(ctx, "leave", channel)

    @leave_message.command(name="edit", description="You can use this command to set a leave message.")
    async def leave_message_set(self, ctx: Context, *, text: str = None):
        return await self._add_message(ctx, "leave", text)

    @leave_message.command(
        name="display",
        description="Displays the current leave message if there is one.",
    )
    async def leave_message_display(self, ctx: Context):
        return await self._message_display(ctx, "leave")

    @leave_channel.command(
        name="display",
        description="Displays the current leave channel if there is one.",
    )
    async def leave_channel_display(self, ctx: Context):
        return await self._channel_display(ctx, "leave")

    @leave_channel.command(name="remove", description="Removes the leave channel.")
    async def leave_channel_remove(self, ctx: Context):
        return await self._remove(ctx, "leave")

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
        return await self._add_channel(ctx, "twitch", channel)

    @twitch_message.command(name="edit", help="Sets a notification message.")
    async def twitch_message_set(self, ctx: Context, *, text: str = None):
        return await self._add_message(ctx, "twitch", text)

    @twitch_message.command(
        name="display",
        description="Displays the current twitch message if there is one.",
    )
    async def twitch_message_display(self, ctx: Context):
        return await self._message_display(ctx, "twitch")

    @twitch_channel.command(
        name="display",
        description="Displays the current twitch channel if there is one.",
    )
    async def twitch_channel_display(self, ctx: Context):
        return await self._channel_display(ctx, "twitch")

    @twitch_channel.command(name="remove", description="Removes the twitch channel.")
    async def twitch_channel_remove(self, ctx: Context):
        return await self._remove(ctx, "twitch")  # MAYBE REMOVE CHANNEL_REMOVE COMMS

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

    @twitch_streamer_remove.autocomplete("username")
    async def autocomplete_callback_twitch_remove(self, _: discord.Interaction, current: str):
        return await self.bot.db.autocomplete(current, "twitch_users", "username", "user_id", all=True)


# RESTRUCTURE GROUP-SUBGROUP CONNECTIONS LIKE: welcome set channel/message | welcome display channel/message (?)
# GLOBAL CHANNEL/MESSAGE DISPLAY THAT WILL SHOW MESSAGE/CHANNEL FOR EACH EVENT_TYPE (?)
# CHANNEL/MESSAGE DISPLAY FOR ALL
# TWITCH (DB) SUBSCRIPTION TO USERS (USER LIST THAT GUILD IS SUBSCRIBED TO) DISPLAY
# twitch.py IN UTILS
# MAYBE A LIST OF EVENTSUBS PER TWITCH USER (LET PEOPLE SUBSCRIBE TO OTHER EVENTS INSTEAD OF JUST SUBSCRIBING TO ON_STREAM)
# SOME IDEAS ^
# SWITCH TO TWITCHAPI LIB
