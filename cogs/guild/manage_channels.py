from __future__ import annotations

from typing import Any, Literal, TypeVar

import discord
from discord import Interaction
from discord.ext import commands
from discord.ui import Select, button, select

from core import BaseCog, Context, Dwello, Embed, View
from utils import HandleHTTPException, Guild


CPT = TypeVar("CPT", bound="CountersPreview")

COUNTER_SELECT_DICT = {
    "all": {
        "label": "All Counter",
        "value": "all",
        "description": "Creates a channel with all-user count on this server.",
    },
    "bot": {
        "label": "Bot Counter",
        "value": "bot",
        "description": "Creates a channel with all-bot count on this server.",
    },
    "member": {
        "label": "Member Counter",
        "value": "member",
        "description": "Creates a channel with all-member count on this server.",
    },
    "category": {
        "label": "Counter Category",
        "value": "category",
        "description": "Creates a category where your counters will be stored.",
    },
}

CHANNEL_SELECT_DICT = {
    "text": {
        "label": "Text Channel",
        "value": "text",
        "description": "Creates the counter as a text channel.",
    },
    "voice": {
        "label": "Voice Channel",
        "value": "voice",
        "description": "Creates the counter as a voice channel.",
    },
    "stage": {
        "label": "Stage Channel",
        "value": "stage",
        "description": "Creates the counter as a stage channel.",
    },
}


async def add_counter(
    obj: Context | Interaction[Dwello],
    _type: Literal["all", "member", "bot", "category"],
    _channel_type: Literal["text", "voice", "stage"] = "text",
) -> discord.abc.GuildChannel | None:
    
    guild = obj.guild
    if isinstance(obj, Interaction):
        bot = obj.client
        reply = obj.response.send_message
    else:
        bot = obj.bot
        reply = obj.send
            
    _guild = await Guild.get(guild.id, bot)

    bot_counter = sum(bool(member.bot) for member in guild.members)
    member_counter = len(guild.members) - bot_counter

    count = {
        "all": guild.member_count or len(guild.members),
        "bot": bot_counter,
        "member": member_counter,
    }.get(_type)

    method = {
        "text": guild.create_text_channel,
        "voice": guild.create_voice_channel,
        "stage": guild.create_stage_channel,
    }.get(_channel_type, guild.create_voice_channel)

    if _type == "category":
        if _guild.category_counter.id:
            await reply("This category already exists.", ephemeral=True)
            return
        channel = await guild.create_category(
            "\N{BAR CHART} Server Counters\N{BAR CHART}", reason=None,
        )
        await channel.edit(position=0)
        await _guild.add_counter("category", channel.id)
    else:
        # if not removed when channel is deleted by user this might trigger
        # then they won't be able to create a new counter
        _channel = _guild.get_channel_by_type(_type)
        if _channel.id if _channel else _channel:
            await reply("Sorry, you can't create this counter because it already exists", ephemeral=True)
            return

        w = _guild.counter_category_denied
        if (w is True or w is None) and not _guild.category_counter.id:
            # so, if `_guild.counter_category_denied` is stored as False in db then this check won't be triggered
            # however, if the category is deleted and db stores True from a previous response
            # then this check will trigger again once someone creates a counter
            await reply(
                embed=Embed(
                    description="**Do you want to create a category for your counters?**",
                ),
                view=CategoryAskView(obj, _type),
                ephemeral=True,
            )
            return

        channel = await method(
            f"\N{BAR CHART} {_type.capitalize()} counter: {count}",
            reason=f"{_type} counter created.",
            category=_guild.category_counter.instance,
        )
        await _guild.add_counter(_type, channel.id)

    await reply(
        embed=Embed(
            description=f"{channel.mention} is successfully created!",
        ), ephemeral=True,
    )
    return channel

async def move_channel(ctx: Context, category: discord.CategoryChannel) -> None:
    _guild = await Guild.get(ctx.guild.id, ctx.bot)

    for counter in _guild.counters:
        channel = counter.instance
        async with HandleHTTPException(ctx, title=f"Failed to move {channel.name} into {category}"):
            await channel.move(category=category, beginning=True)
    return


class CategoryAskView(View):
    """Asks the person if they would like to have a category for their counters."""

    def __init__(self, obj: Context | Interaction[Dwello], _type: str) -> None:
        super().__init__(obj)
        self.type = _type

    @property
    def obj(self) -> Context | Interaction[Dwello]:
        return self.ctx or self.interaction

    @button(
        style=discord.ButtonStyle.green,
        label="Approve",
        custom_id="approve_button",
    )
    async def approve(self, interaction: discord.Interaction, _) -> None:
        """
        When you accept, a category channel is created
        and then your previously requested counter is created and moved into it.
        """
        await self.bot.db.update_guild_config(self.obj.guild.id, {"counter_category_denied": True})
        category = await add_counter(self.obj, "category")
        await add_counter(self.obj, self.type)
        return await interaction.response.edit_message(
            content=f"The **{category.name}** is successfully created by **{interaction.user}**!",
            embed=None,
            view=None,
        )

    @button(
        style=discord.ButtonStyle.red,
        label="Deny",
        custom_id="deny_button",
    )
    async def deny(self, interaction: discord.Interaction, _) -> None:
        """
        If you deny however, a category channel isn't created
        and then your previously requested counter is created.
        """
        await self.bot.db.update_guild_config(self.obj.guild.id, {"counter_category_denied": False})
        await add_counter(self.obj, self.type)
        return await interaction.response.edit_message(content=None, view=None)


class CountersPreview(View):
    def __init__(self, obj: Context | Interaction[Dwello], **kwargs) -> None:
        super().__init__(obj, **kwargs)

        self.main_embed = Embed(
            title="Counter Select",
            description=(
                "Hey there! "
                "Here you can choose which counter you'd like to create and which channel it should be created as. "
                "Basically, counter is displayed as a channel's name. That means that you would still be able to use them "
                "and the counter itself shouldn't be affected as long as you don't change the channel's name."
                # maybe check if a channel name is updated in events, and if its a counter -> change it back right away
            ),
        )

    @select(placeholder="Select counter type")
    async def counter_select(self, interaction: Interaction, select: Select):
        select.placeholder = COUNTER_SELECT_DICT.get(select.values[0])["label"]
        await interaction.response.edit_message(view=self)

    @select(placeholder="Select channel type")
    async def channel_select(self, interaction: Interaction, select: Select):
        select.placeholder = CHANNEL_SELECT_DICT.get(select.values[0])["label"]
        await interaction.response.edit_message(view=self)
        
    @button(label="Submit", style=discord.ButtonStyle.blurple)
    async def submit(self, interaction: Interaction, _):
        try:
            value = self.channel_select.values[0]
        except IndexError:
            value = "voice"
        if isinstance(await add_counter(interaction, self.counter_select.values[0], value), discord.abc.GuildChannel):
            await self.message.edit(view=None)

    def build_select(self) -> None:
        self.counter_select.options = []
        self.channel_select.options = []
        for i in COUNTER_SELECT_DICT.values():
            self.counter_select.add_option(**i)
        for b in CHANNEL_SELECT_DICT.values():
            self.channel_select.add_option(**b)

    @classmethod
    async def start(
        cls: type[CPT],
        obj: Context | Interaction[Dwello],
        /,
        **kwargs,
    ) -> CPT:
        self = cls(obj, **kwargs)

        self.build_select()
        embed = self.main_embed

        if self.ctx:
            self.message = await self.ctx.send(embed=embed, view=self)
        else:
            obj = self.interaction
            await obj.response.send_message(embed=embed, view=self)
            self.message = await obj.original_response()
        await self.wait()
        return self

class Channels(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        
    @commands.command(
        name="counter",
        aliases=["counters"],
        brief="Adds a counter of your preference.",
    )
    @commands.check_any(
        commands.guild_only(),
        commands.bot_has_permissions(manage_channels=True),
        commands.has_permissions(manage_channels=True),
    )
    async def counter(self, ctx: Context, counter: str = None, _type: str = "text"):
        """
        A command designed for the specific purpose of manipulating the guild's counters, particularly for creating them.
        If you wish to delete your counter, just do it yourself.
        Currently, this group provides three types of counters: an 'all counter' (counts everyone in the guild),
        a 'member counter' (counts only 'real' users), and a 'bot counter' (counts the bots present in the guild).
        Additionally, it technically has access to a fourth counter,
        which is a 'counter category' for organizing all your counters.
        """
        if not counter:
            return await CountersPreview.start(ctx)
        if counter.lower() not in ["all", "member", "bot", "category"]:
            raise commands.BadArgument(f"Sorry, the input must be one of `all`, `member`, `bot`, or `category`, not `{counter}`")  # noqa: E501
        if _type.lower() not in ["text", "voice", "stage"]:
            raise commands.BadArgument(f"Sorry, the input must be one of `text`, `voice`, or `stage`, not `{_type}`")
        return await add_counter(ctx, counter.lower(), _type.lower())
    
    @discord.app_commands.command(name="counter", description="Adds a counter of your preference.")
    @commands.check_any(
        commands.guild_only(),
        commands.bot_has_permissions(manage_channels=True),
        commands.has_permissions(manage_channels=True),
    )
    async def app_counter(
        self, ctx: Context,
        counter: Literal["All", "Member", "Bot", "Category"] = None,
        type: Literal["Text", "Voice", "Stage"] = "Text",
    ):
        if not counter:
            return await CountersPreview.start(ctx)
        return await add_counter(ctx, counter.lower(), type.lower())

    '''@counter.command(
        name="all",
        brief="Creates a [voice] channel with all-user count on this server.",
        description="Creates a [voice] channel with all-user count on this server.",
    )
    async def all(self, ctx: Context):
        """Adds a counter that counts everyone in the current guild."""
        return await self.cf.add_counter(ctx, "all")

    @counter.command(
        name="member",
        aliases=["members"],
        brief="Creating a [voice] channel with all-member count on this server.",
        description="Creating a [voice] channel with all-member count on this server.",
    )
    async def members(self, ctx: Context):
        """Creates a counter that counts all 'human' members."""
        return await self.cf.add_counter(ctx, "member")

    @counter.command(
        name="bot",
        aliases=["bots"],
        brief="Creating a [voice] channel with all-bot count on this server.",
        description="Creating a [voice] channel with all-bot count on this server.",
    )
    async def bots(self, ctx: Context):
        """Creates a counter that counts all the bots this guild has to offer."""
        return await self.cf.add_counter(ctx, "bot")

    @counter.command(
        name="category",
        brief="Creates a category where your counters will be stored.",
        description="Creates a category where your counters will be stored.",
    )
    async def category(self, ctx: Context):
        """Adds a category that will help you organize your counters."""
        category = await self.cf.add_counter(ctx, "category")
        return await self.cf.move_channel(ctx, category)

    @counter.command(
        name="list",
        aliases=["show", "display"],
        brief="Shows a list of counters you can create.",
        description="Shows a list of counters you can create.",
    )
    async def list(self, ctx: Context): # add to help cmd instead? <-
        async with ctx.typing(ephemeral=True):
            embed: Embed = Embed(
                title=":bar_chart: AVAILABLE COUNTERS :bar_chart:",
                description=cs.server_statistics_list_help_embed_description,
                color=cs.WARNING_COLOR,
            ).set_footer(text=cs.FOOTER)
            return await ctx.reply(embed=embed, ephemeral=True, mention_author=False)'''
