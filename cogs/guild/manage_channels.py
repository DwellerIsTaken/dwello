from __future__ import annotations

from typing import Literal, Optional, Union

import asyncpg
import discord
from discord.ext import commands
from discord.ui import Button, View, button
from typing_extensions import Self

import constants as cs
from core import Bot, Cog, Context
from utils import HandleHTTPException


class ChannelsFunctions:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def counter_func(
        self,
        ctx: Context,
        name: Literal["all", "member", "bot", "category"],
    ) -> Optional[
        Union[discord.VoiceChannel, discord.CategoryChannel]
    ]:  # Optional[Tuple[discord.Message, Union[discord.VoiceChannel, discord.CategoryChannel]]]
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                count = ctx.guild.member_count

                bot_counter = sum(bool(member.bot) for member in ctx.guild.members)
                member_counter = int(ctx.guild.member_count) - bot_counter

                query = (
                    "SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = 'counter' AND counter_name = $2"
                )
                row = await conn.fetchrow(query, ctx.guild.id, "category")
                counter_category_id = row[0] if row else None

                if name == "all":
                    count = count

                if name == "member":
                    count = member_counter

                elif name == "bot":
                    count = bot_counter

                elif name == "category":
                    if counter_category_id:
                        return await ctx.reply(
                            "This category already exists.",
                            mention_author=True,
                            ephemeral=True,
                        )

                    counter_channel = await ctx.guild.create_category("📊 Server Counters 📊", reason=None)
                    await counter_channel.edit(position=0)
                    await conn.execute(
                        "UPDATE server_data SET channel_id = $1 WHERE counter_name = $2 AND event_type = 'counter' AND guild_id = $3",
                        counter_channel.id,
                        name,
                        ctx.guild.id,
                    )
                    await ctx.reply(
                        f"The **{counter_channel.name}** is successfully created!",
                        mention_author=False,
                    )
                    return counter_channel

                query = "SELECT channel_id, deny_clicked FROM server_data WHERE guild_id = $1 AND event_type = 'counter' AND counter_name = $2"  # maybe create a category func after all
                row = await conn.fetchrow(query, ctx.guild.id, name)
                channel_id, deny_result = (row[0], row[1]) if row else (None, None)

                # should be checked in a channel_delete event
                """try:
                    counter_category = discord.utils.get(ctx.guild.categories, id = int(category_record))

                except TypeError:
                    counter_category = None"""

                if channel_id:
                    return await ctx.reply(
                        "This counter already exists! Please provide another type of counter if you need to, otherwise __**please don`t create a counter that already exists**__.",
                        user_mistake=True,
                    )  # return embed instead (?)

                if not deny_result and not counter_category_id:
                    embed: discord.Embed = discord.Embed(
                        description="**Do you want to create a category for your counters?**",
                        color=cs.RANDOM_COLOR,
                    ).set_footer(text=cs.FOOTER)
                    return await ctx.reply(
                        embed=embed,
                        view=Stats_View(self.bot, ctx, name),
                        user_mistake=True,
                    )

                # elif deny_result is None and counter_category is not None: # ?
                # await conn.execute("UPDATE server_data SET deny_clicked = $1 WHERE guild_id = $2", 1, ctx.guild.id)

                if not channel_id:
                    counter_category: discord.CategoryChannel = ctx.guild.get_channel(int(counter_category_id))
                    counter_channel = await ctx.guild.create_voice_channel(
                        f"📊 {name.capitalize()} counter: {count}",
                        reason=None,
                        category=counter_category,
                    )
                    await conn.execute(
                        "UPDATE server_data SET channel_id = $1 WHERE event_type = 'counter' AND counter_name = $2 AND guild_id = $3",
                        counter_channel.id,
                        name,
                        ctx.guild.id,
                    )

        await ctx.reply(
            embed=discord.Embed(
                description=f"**{counter_channel.name}** is successfully created!",
                color=cs.RANDOM_COLOR,
            ),
            permission_cmd=True,
        )  # DISPLAEYD IN DISCORD LOGS
        return counter_channel

    async def move_channel(self, ctx: Context, category: discord.CategoryChannel, *args: str) -> None:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                placeholders = ",".join([f"${i + 2}" for i in range(len(args))])
                query = f"SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = 'counter' AND counter_name IN ({placeholders})"

                rows = await conn.fetch(query, ctx.guild.id, *args)

                for row in rows:
                    channel = ctx.guild.get_channel(row[0])
                    async with HandleHTTPException(ctx, title=f"Failed to move {channel} into {category}"):
                        await channel.move(category=category, beginning=True)
        return


class Stats_View(View):
    def __init__(self, bot: Bot, ctx: Context, name: str, *, timeout: int = None):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.ctx = ctx
        self.name = name

        self.cf_: ChannelsFunctions = ChannelsFunctions(self.bot)

    # DO A MORE USER-FRIENDLY INTERACTION CHECK
    async def interaction_check(self, interaction: discord.Interaction) -> Optional[discord.Message]:
        if interaction.user.id == self.ctx.author.id:
            return True

        missing_permissions_embed = discord.Embed(
            title="Permission Denied.",
            description="You can't interact with someone else's buttons.",
            color=cs.RANDOM_COLOR,
        )
        missing_permissions_embed.set_footer(text=cs.FOOTER)
        return await interaction.response.send_message(embed=missing_permissions_embed, ephemeral=True)

    @button(
        style=discord.ButtonStyle.green,
        label="Approve",
        disabled=False,
        custom_id="approve_button",
    )
    async def approve(self, interaction: discord.interactions.Interaction, button: Button) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                counter_category = await self.cf_.counter_func(self.ctx, "category")
                await self.cf_.counter_func(self.ctx, self.name)
                return await interaction.response.edit_message(
                    embed=None,
                    content=f"The **{counter_category.name}** is successfully created by **{interaction.user}**!",
                    view=None,
                )

    @button(
        style=discord.ButtonStyle.red,
        label="Deny",
        disabled=False,
        custom_id="deny_button",
    )
    async def deny(self, interaction: discord.interactions.Interaction, button: Button) -> None:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                await conn.execute(
                    "UPDATE server_data SET deny_clicked = $1 WHERE guild_id = $2",
                    1,
                    interaction.guild.id,
                )
                await self.cf_.counter_func(self.ctx, self.name)
                return await interaction.response.edit_message(content=None, view=None)


class Channels(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
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
            embed: discord.Embed = discord.Embed(description="```$counter [counter type]```", color=cs.WARNING_COLOR)
            return await ctx.reply(embed=embed, user_mistake=True)

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
        return await self.cf.move_channel(ctx, category[1], "all", "member", "bot")

    @counter.command(name="list", help="Shows a list of counters you can create.")
    async def list(self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            embed: discord.Embed = discord.Embed(
                title=":bar_chart: AVAILABLE COUNTERS :bar_chart:",
                description=cs.server_statistics_list_help_embed_description,
                color=cs.WARNING_COLOR,
            ).set_footer(text=cs.FOOTER)
            return await ctx.reply(embed=embed, ephemeral=True, mention_author=False)
