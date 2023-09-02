from __future__ import annotations

from typing import Any, Literal

import discord
from discord.ext import commands
from discord.ui import button

import constants as cs
from core import BaseCog, Context, Dwello, Embed, View
from utils import HandleHTTPException, Guild


class ChannelsFunctions:
    def __init__(self, bot: Dwello) -> None:
        self.bot: Dwello = bot

    async def counter_func(
        self,
        ctx: Context,
        _type: Literal["all", "member", "bot", "category"],
    ) -> discord.abc.GuildChannel | None:
                
        _guild = await Guild.get(ctx.guild.id, self.bot)

        bot_counter = sum(bool(member.bot) for member in ctx.guild.members)
        member_counter = len(ctx.guild.members) - bot_counter

        count = {
            "all": ctx.guild.member_count or len(ctx.guild.members),
            "bot": bot_counter,
            "member": member_counter,
        }.get(_type)

        if _type == "category":
            if _guild.category_counter.id:
                await ctx.reply(
                    "This category already exists.",
                    mention_author=True,
                    ephemeral=True,
                )
                return
            channel = await ctx.guild.create_category(
                "\N{BAR CHART} Server Counters\N{BAR CHART}", reason=None,
            )
            await channel.edit(position=0)
            await _guild.add_counter("category", channel.id)
        else:
            # if not removed when channel is deleted by user this might trigger
            # then they won't be able to create a new counter
            _channel = _guild.get_channel_by_type(_type)
            if _channel.id if _channel else _channel:
                await ctx.reply(
                    "Sorry, you can't create this counter because it already exists",
                    user_mistake=True,
                )
                return

            w = _guild.counter_category_denied
            if (w is True or w is None) and not _guild.category_counter.id:
                # so, if `_guild.counter_category_denied` is stored as False in db then this check won't be triggered
                # however, if the category is deleted and db stores True from a previous response
                # then this check will trigger again once someone creates a counter
                await ctx.reply(
                    embed=Embed(
                        description="**Do you want to create a category for your counters?**",
                    ),
                    view=CategoryAskView(ctx, _type),
                    user_mistake=True,
                )
                return

            channel = await ctx.guild.create_voice_channel(
                f"\N{BAR CHART} {_type.capitalize()} counter: {count}",
                reason=None,
                category=_guild.category_counter.instance,
            )
            await _guild.add_counter(_type, channel.id)

        await ctx.reply(
            embed=Embed(
                description=f"{channel.mention} is successfully created!",
            ),
            permission_cmd=True,
        )
        return channel

    async def move_channel(self, ctx: Context, category: discord.CategoryChannel) -> None:
        _guild = await Guild.get(ctx.guild.id, self.bot)

        for counter in _guild.counters:
            channel = counter.instance
            async with HandleHTTPException(ctx, title=f"Failed to move {channel.name} into {category}"):
                await channel.move(category=category, beginning=True)
        return


class CategoryAskView(View):
    """Asks the person if they would like to have a category for their counters."""
    def __init__(self, ctx: Context, _type: str) -> None:
        super().__init__(ctx)
        self.type = _type

        self.cf_: ChannelsFunctions = ChannelsFunctions(self.bot)

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
        await self.bot.db.update_guild_config(self.ctx.guild.id, {"counter_category_denied": True})
        category = await self.cf_.counter_func(self.ctx, "category")
        await self.cf_.counter_func(self.ctx, self.type)
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
        await self.bot.db.update_guild_config(self.ctx.guild.id, {"counter_category_denied": False})
        await self.cf_.counter_func(self.ctx, self.type)
        return await interaction.response.edit_message(content=None, view=None)


class Channels(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self.cf: ChannelsFunctions = ChannelsFunctions(self.bot)

    @commands.hybrid_group(
        name="counter",
        description="Counter group.",
        invoke_without_command=True,
        with_app_command=True,
    )
    @commands.bot_has_permissions(manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def counter(self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            return await ctx.send_help(ctx.command)

    @counter.command(
        name="all",
        help="Creates a [voice] channel with all-user (bots included) count on this server.",
    )
    async def all(self, ctx: Context):
        return await self.cf.counter_func(ctx, "all")

    @counter.command(
        name="members",
        help="Creating a [voice] channel with all-member count on this specific server.",
    )
    async def members(self, ctx: Context):
        return await self.cf.counter_func(ctx, "member")

    @counter.command(
        name="bots",
        help="Creating a [voice] channel with all-bot count on this specific server.",
    )
    async def bots(self, ctx: Context):
        return await self.cf.counter_func(ctx, "bot")

    @counter.command(name="category", help="Creates a category where your counter(s) will be stored.")
    async def category(self, ctx: Context):
        category = await self.cf.counter_func(ctx, "category")
        return await self.cf.move_channel(ctx, category)

    @counter.command(name="list", aliases=["show", "display"], help="Shows a list of counters you can create.")
    async def list(self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            embed: Embed = Embed(
                title=":bar_chart: AVAILABLE COUNTERS :bar_chart:",
                description=cs.server_statistics_list_help_embed_description,
                color=cs.WARNING_COLOR,
            ).set_footer(text=cs.FOOTER)
            return await ctx.reply(embed=embed, ephemeral=True, mention_author=False)
