from __future__ import annotations

from typing import Any, TypeVar

import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, Select, select, button

import constants as cs  # noqa: F401
from core import BaseCog, Context, Dwello, Embed, View
from utils import Guild, GuildChannel


CPT = TypeVar("CPT", bound="ChannelsPreview")

_Interaction = discord.Interaction[Dwello]


class EditChannelMessageModal(Modal, title="Edit channel message."):
    """This modal is only called when the message for a channel isn't provided."""

    # maybe add title for the welcome message embed
    # maybe do that in customisation instead
    # like, modal, so the user would be construct the embed themselves
    # title for welcome embed, description, maybe even on/off button for banner that will be generated
    # same for embed author etc
    # maybe not cause there should also be like a general embed config by user

    def __init__(self, _channels: list[GuildChannel], _view: ChannelsPreview = None) -> None:
        super().__init__()

        self.channels: list[GuildChannel] = _channels
        self.view: ChannelsPreview = _view
        self.fields: dict[str, TextInput] = {}
        _k = {
            'label': 'Content (optional)',
            'required': False,
            'min_length': 1,
            'max_length': 1000, # maybe make smaller depending on db
            'style': discord.TextStyle.paragraph,
            'placeholder': f'Example:\n{cs.EXAMPLE_WELCOME_MESSAGE}',
        }
        if len(_channels) > 1:
            _k.pop('label')
            self.fields.update({
                'welcome': TextInput(
                    label="Welcome text (optional)",
                    **_k,
                ),
                'leave': TextInput(
                    label="Leave text (optional)",
                    **_k
                ),
            })
        else:
            self.fields[_channels[0].type] = TextInput(**_k)

        for n, input in enumerate(self.fields.values()):
            input.default = _channels[n].message or ""
            self.add_item(input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if (md:= self.view.msg_dict if self.view else None) is not None:
            for db_name, _input in self.fields.items():
                md[db_name] = _input.value or None
            await interaction.response.edit_message(view=self.view)
        else:
            c = self.channels[0]
            _input = self.fields.get(c.type)
            value = _input.value or None
            await c.add_message(value)
            await interaction.response.send_message(
                f"Done, the message now is:\n> {value or _input.placeholder}", ephemeral=True,
            )
        

class ChannelsPreview(View):
    def __init__(self, obj: Context | _Interaction, **kwargs) -> None:
        super().__init__(obj, **kwargs)

        self.guild: Guild | None = None
        self.msg_dict: dict[str, str | None] = {}

    @select(placeholder="Select channel type")
    async def type_select(self, interaction: _Interaction, select: Select):
        if len(select.values[0].split('|')) == 1:
            select.placeholder = self.guild.CHANNEL_DICT.get(select.values[0])["label"]
        else:
            select.placeholder = "Welcome & Leave channel"
        await interaction.response.edit_message(view=self)

    @select(placeholder="Select a channel")
    async def channel_select(self, interaction: _Interaction, select: Select):
        if channel:= self.author.guild.get_channel(int(select.values[0])):
            select.placeholder = channel.name
        await interaction.response.edit_message(view=self)
        
    @button(label="Input", style=discord.ButtonStyle.blurple)
    async def input(self, interaction: _Interaction, _):
        channels: list[GuildChannel] = []
        try:
            for i in self.type_select.values[0].split('|'):
                channels.append(self.guild.get_channel_by_type(i.strip()))
            await interaction.response.send_modal(EditChannelMessageModal(channels, self))
        except IndexError:
            await interaction.response.send_message("Please choose one of the given channel types first.", ephemeral=True)

    @button(label="Submit", style=discord.ButtonStyle.blurple)
    async def submit(self, interaction: _Interaction, _):
        try:
            _type = self.type_select.values[0]
        except IndexError:
            return await interaction.response.send_message(
                "You can't submit the form without a selected channel type.", ephemeral=True,
            )
        try:
            _id = self.channel_select.values[0]
        except IndexError:
            _id = None
        if not _id and not self.msg_dict:
            return await interaction.response.send_message("You can't submit an empty result.", ephemeral=True)
        if _id:
            for t in _type.split('|'):
                await self.guild.add_channel(t.strip(), int(_id))
        if self.msg_dict:
            for name, message in self.msg_dict.items():
                await self.guild.get_channel_by_type(name).add_message(message)

        self.clear_items()
        await interaction.response.edit_message(view=self)

    def build_select(self) -> None:
        self.type_select.options = []
        self.channel_select.options = []
        self.type_select.add_option(label="Welcome & Leave channel", value="welcome_channel | leave_channel")
        for channel in self.author.guild.text_channels:
            self.channel_select.add_option(label=channel.name, value=channel.id)
        alias_checklist = []
        for i, d in self.guild.CHANNEL_DICT.items():
            if any([alias.startswith(i) for alias in alias_checklist]):
                # dict has to start from long names and descend into smaller ones in order for this to work
                continue
            alias_checklist.append(i)
            self.type_select.add_option(label=d["label"], value=d["channel"])

    @classmethod
    async def start(
        cls: type[CPT],
        obj: Context | _Interaction,
        /,
        **kwargs,
    ) -> CPT:
        self = cls(obj, **kwargs)

        self.guild = await Guild.get(self.author.guild.id, self.bot)
        self.build_select()

        embed = Embed(
            title="Channel Customisation",
            description=(
                "Greetings! "
                "In here you are able to configure some channels based on their type. "
                "For example, if you'd like to set a welcome channel then you can choose it as type, choose a channel within"
                " your guild that will be configured as a welcome channel and - if you wish to - you can also select some "
                "adittional features related to that channel, such as a welcome message, in this case, that will be "
                "displayed whenever a person joins your glorious guild! "
            ),
        )
        if self.ctx:
            self.message = await self.ctx.send(embed=embed, view=self)
        else:
            obj = self.interaction
            await obj.response.send_message(embed=embed, view=self)
            self.message = await obj.original_response()
        await self.wait()
        return self
    

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
            await ctx.interaction.response.send_modal(EditChannelMessageModal([_channel]))
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
        """
        A command group designed for manipulating welcome content,
        including tasks like configuring and removing welcome channels and messages.
        Similair to `leave` command group.
        """
        try:
            return await ChannelsPreview.start(ctx)
        except ValueError:
            return await ctx.send_help(ctx.command) # maybe some extra handling here
        except:  # noqa: E722
            return await ctx.send_help(ctx.command)

    @welcome.group(invoke_without_command=True, with_app_command=True, name="message")
    async def welcome_mesage(self, ctx: Context):
        """Manage welcome messages."""
        return await ctx.send_help(ctx.command)

    @welcome.group(invoke_without_command=True, with_app_command=True, name="channel")
    async def welcome_channel(self, ctx: Context):
        """Manage welcome channels."""
        return await ctx.send_help(ctx.command)

    @welcome_channel.command(
        name="set",
        brief="Sets chosen channel as a welcome channel.",
        description="Sets chosen channel as a welcome channel.",
    )
    async def welcome_channel_set(
        self,
        ctx: Context,
        channel: discord.TextChannel | None = commands.CurrentChannel,
    ):
        """Set a specific channel as the welcome channel. Otherwise, the current channel is selected."""
        return await self._add_channel(ctx, "welcome", channel)

    @welcome_mesage.command(
        name="edit",
        brief="You can use this command to set a welcome message.",
        description="You can use this command to set a welcome message.",
    )
    async def welcome_message_set(self, ctx: Context, *, text: str = None):
        """
        Personalize your welcome message by either providing a custom message as a parameter,
        or if you haven't set one, a modal will automatically appear.
        This modal will display your current welcome message and allow you to make any desired edits to it.
        """
        return await self._add_message(ctx, "welcome", text)

    @welcome_mesage.command(
        name="display",
        brief="Displays the current welcome message.",
        description="Displays the current welcome message.",
    )
    async def welcome_message_display(self, ctx: Context):
        """Display the current welcome message."""
        return await self._message_display(ctx, "welcome")

    @welcome_channel.command(
        name="display",
        brief="Displays the current welcome channel.",
        description="Displays the current welcome channel.",
    )
    async def welcome_channel_display(self, ctx: Context):
        """Display the current welcome channel."""
        return await self._channel_display(ctx, "welcome")

    @welcome_channel.command(
        name="remove",
        brief="Removes the welcome channel.",
        description="Removes the welcome channel.",
    )
    async def welcome_channel_remove(self, ctx: Context):
        """
        Remove the current welcome channel.\n
        **Note**: if the welcome channel is removed then no welcome messages would be sent in the current guild.
        """
        return await self._remove(ctx, "welcome")

    @commands.hybrid_group(invoke_without_command=True)
    @commands.has_permissions(manage_channels=True, manage_messages=True)  # REDO PERMS
    async def leave(self, ctx: Context):
        """
        A command group designed for manipulating leave content,
        including tasks like configuring and removing leave channels and messages.
        Similair to `welcome` command group.
        """
        async with ctx.typing(ephemeral=True):
            return await ctx.send_help(ctx.command)

    @leave.group(invoke_without_command=True, name="message")
    async def leave_message(self, ctx: Context):
        """Subgroup for managing the leave messages."""
        return await ctx.send_help(ctx.command)

    @leave.group(invoke_without_command=True, name="channel")
    async def leave_channel(self, ctx: Context):
        """Subgroup for managing the leave channels."""
        return await ctx.send_help(ctx.command)

    @leave_channel.command(
        name="set",
        brief="Sets chosen channel as a leave channel.",
        description="Sets chosen channel as a leave channel.",
    )
    async def leave_channel_set(
        self,
        ctx: Context,
        channel: discord.TextChannel | None = commands.CurrentChannel,
    ):
        """Set a specific channel as the leave channel. Otherwise, the current channel is selected."""
        return await self._add_channel(ctx, "leave", channel)

    @leave_message.command(
        name="edit",
        brief="You can use this command to set a leave message.",
        description="You can use this command to set a leave message.",
    )
    async def leave_message_set(self, ctx: Context, *, text: str = None):
        """
        Personalize your leave message by either providing a custom message as a parameter,
        or if you haven't set one, a modal will automatically appear.
        This modal will display your current leave message and allow you to make any desired edits to it.
        """
        return await self._add_message(ctx, "leave", text)

    @leave_message.command(
        name="display",
        brief="Displays the current leave message if there is one.",
        description="Displays the current leave message if there is one.",
    )
    async def leave_message_display(self, ctx: Context):
        """Display the current leave message."""
        return await self._message_display(ctx, "leave")

    @leave_channel.command(
        name="display",
        brief="Displays the current leave channel if there is one.",
        description="Displays the current leave channel if there is one.",
    )
    async def leave_channel_display(self, ctx: Context):
        """Display the current leave channel."""
        return await self._channel_display(ctx, "leave")

    @leave_channel.command(
        name="remove",
        brief="Removes the leave channel.",
        description="Removes the leave channel.",
    )
    async def leave_channel_remove(self, ctx: Context):
        """
        Remove the current leave channel.\n
        **Note**: if the leave channel is removed then no leave messages would be sent in the current guild.
        """
        return await self._remove(ctx, "leave")

    @commands.hybrid_group(invoke_without_command=True)
    @commands.has_permissions(manage_channels=True, manage_messages=True)  # change to admin maybe
    async def twitch(self, ctx: Context):
        """
        A command group designed for manipulating twitch content,
        including tasks like configuring and removing twitch channels, notification messages and twitch streamers.
        """
        async with ctx.typing(ephemeral=True):
            return await ctx.send_help(ctx.command)

    @twitch.group(invoke_without_command=True, name="message")
    async def twitch_message(self, ctx: Context):
        """Subgroup for managing the twitch notification messages."""
        return await ctx.send_help(ctx.command)

    @twitch.group(invoke_without_command=True, name="channel")
    async def twitch_channel(self, ctx: Context):
        """Subgroup for managing the channels where the notifications will be sent to."""
        return await ctx.send_help(ctx.command)

    @twitch_channel.command(
        name="set",
        brief="Sets a channel where your twitch notifications will be posted.",
        description="Sets a channel where your twitch notifications will be posted.",
    )
    async def twitch_channel_set(
        self,
        ctx: Context,
        channel: discord.TextChannel | None = commands.CurrentChannel,
    ):
        """Set a specific channel as the twitch channel. Otherwise, the current channel is selected."""
        return await self._add_channel(ctx, "twitch", channel)

    @twitch_message.command(
        name="edit",
        brief="Sets a notification message.",
        description="Sets a notification message.",
    )
    async def twitch_message_set(self, ctx: Context, *, text: str = None):
        """
        Personalize your twitch message by either providing a custom message as a parameter,
        or if you haven't set one, a modal will automatically appear.
        This modal will display your current twitch message and allow you to make any desired edits to it.
        """
        return await self._add_message(ctx, "twitch", text)

    @twitch_message.command(
        name="display",
        brief="Displays the current twitch message if there is one.",
        description="Displays the current twitch message if there is one.",
    )
    async def twitch_message_display(self, ctx: Context):
        """Display the current twitch notification message."""
        return await self._message_display(ctx, "twitch")

    @twitch_channel.command(
        name="display",
        brief="Displays the current twitch channel if there is one.",
        description="Displays the current twitch channel if there is one.",
    )
    async def twitch_channel_display(self, ctx: Context):
        """Display the current twitch channel."""
        return await self._channel_display(ctx, "twitch")

    @twitch_channel.command(
        name="remove",
        brief="Removes the twitch channel.",
        description="Removes the twitch channel.",
    )
    async def twitch_channel_remove(self, ctx: Context):
        """
        Remove the current twitch channel.\n
        **Note**: if the twitch channel is removed then no twitch messages would be sent in the current guild.
        """
        return await self._remove(ctx, "twitch")  # MAYBE REMOVE CHANNEL_REMOVE COMMS (?)

    @twitch.command(
        name="add",
        brief="Subsribes this guild to a certain twitch streamer.",
        description="Subsribes this guild to a certain twitch streamer.",
    )
    async def add_twitch_streamer(self, ctx: commands.Context, twitch_streamer_name: str):
        """
        Add a twitch streamer to your guild.
        The notification will be sent to the selected twitch channel once the streamer starts their stream.
        """
        return await self.bot.twitch.event_subscription(ctx, "stream.online", twitch_streamer_name)

    @twitch.command(
        name="list",
        brief="Shows the list of streamers this guild is subscribed to.",
        description="Shows the list of streamers this guild is subscribed to.",
    )
    async def twitch_streamer_list(self, ctx: Context):
        """Returns a list of twitch streamers this guild is subscribed to."""
        return await self.bot.twitch.guild_twitch_subscriptions(ctx)

    @twitch.command(
        name="remove",
        brief="Unsubscribes this guild from a twitch streamer.",
        description="Unsubscribes this guild from a twitch streamer.",
    )
    async def twitch_streamer_remove(self, ctx: Context, username: str):  # add choice to delete all
        """
        Removes a selected twitch streamer,
        or all streamers this guild is subscribed to - if you use this command with slash.
        """
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
