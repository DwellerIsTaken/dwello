from __future__ import annotations

from typing import List, Literal, Optional, Union

import asyncpg
import discord
from discord.ext import commands
from typing_extensions import Self

import constants as cs
from core import Bot, Cog, Context


class PrefixConfig:
    def __init__(self: Self, bot: Bot) -> None:
        self.bot = bot

    async def set_prefix(self: Self, ctx: Context, prefix: str) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                try:
                    await conn.execute(
                        "INSERT INTO prefixes(prefix, guild_id) VALUES($1, $2)",
                        prefix,
                        ctx.guild.id,
                    )

                except asyncpg.exceptions.StringDataRightTruncationError:
                    return await ctx.reply("This prefix is too long!", user_mistake=True)  # add allowed prefix length

                except asyncpg.exceptions.UniqueViolationError:
                    return await ctx.reply("This prefix is already added!", user_mistake=True)

        # await self.bot.db.fetch_table_data("prefixes")
        self.bot.guild_prefixes[ctx.guild.id].append(prefix)
        return await ctx.reply(
            embed=discord.Embed(description=f"The prefix is set to `{prefix}`", color=cs.RANDOM_COLOR),
            permission_cmd=True,
        )

    async def display_prefixes(self: Self, ctx: Context) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                prefixes = await conn.fetch("SELECT prefix FROM prefixes WHERE guild_id = $1", ctx.guild.id)
                default_prefixes: List[str] = self.bot.DEFAULT_PREFIXES + [f"<@!{self.bot.user.id}>"]

                embed: discord.Embed = discord.Embed(title="Prefixes", color=cs.RANDOM_COLOR)

                if ctx.guild:
                    embed.add_field(
                        name="Guild's prefix(es)",
                        value=(
                            ", ".join(f"`{p['prefix']}`" for p in prefixes) if prefixes else "`None` -> `dw.help prefix`"
                        ),
                        inline=False,
                    )
                embed.add_field(
                    name="Default prefixes",
                    value=", ".join(p if str(self.bot.user.id) in p else f"`{p}`" for p in default_prefixes),
                    inline=False,
                )
                embed.set_footer(text=None)

        return await ctx.reply(embed=embed, mention_author=False, ephemeral=False)

    async def remove_prefix(self: Self, ctx: Context, prefix: Union[str, Literal["all"]]) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                prefixes = await conn.fetch("SELECT prefix FROM prefixes WHERE guild_id = $1", ctx.guild.id)

                if not (prefixes[0] if prefixes else None):
                    return await ctx.reply(
                        "Prefix isn't yet set. \n```/prefix add [prefix]```",
                        user_mistake=True,
                    )

                count = len(prefixes)
                if prefix == "all":
                    await conn.execute("DELETE FROM prefixes WHERE guild_id = $1", ctx.guild.id)

                elif isinstance(prefix, str):
                    await conn.execute(
                        "DELETE FROM prefixes WHERE prefix = $1 AND guild_id = $2",
                        prefix,
                        ctx.guild.id,
                    )
                    count = 1

        # await self.bot.db.fetch_table_data("prefixes")
        self.bot.guild_prefixes[ctx.guild.id].remove(prefix)
        return await ctx.reply(
            embed=discord.Embed(
                description=f"{'Prefix has' if count == 1 else f'{count} prefixes have'} been removed.",
                color=cs.RANDOM_COLOR,
            ),
            permission_cmd=True,
        )


class ChannelConfig:
    def __init__(self: Self, bot: Bot) -> None:
        self.bot = bot

    async def add_message(self: Self, ctx: Context, name: str, text: str) -> Optional[discord.Message]:
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

                await conn.execute(
                    "UPDATE server_data SET message_text = $1, event_type = COALESCE(event_type, $2) WHERE guild_id = $3 AND COALESCE(event_type, $2) = $2",
                    text,
                    name,
                    ctx.guild.id,
                )
                string = f"{name.capitalize()} message has been {'updated' if result[0] else 'set'} to: ```{text}```"

        return await ctx.reply(
            embed=discord.Embed(description=string, color=cs.RANDOM_COLOR),
            permission_cmd=True,
        )

    async def add_channel(
        self: Self,
        ctx: Context,
        name: str,
        channel: Optional[discord.TextChannel] = commands.CurrentChannel,
    ) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                result = await conn.fetchrow(
                    "SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2",
                    ctx.guild.id,
                    name,
                )

                string = f"The channel has been {'updated' if result[0] and result else 'set'} to {channel.mention}"

                if (result[0] if result else None) == channel.id:
                    return await ctx.reply(
                        f"{name.capitalize()} channel has already been set to this channel!",
                        user_mistake=True,
                    )

                # await conn.execute("UPDATE server_data SET channel_id = $1, event_type = COALESCE(event_type, $2) WHERE guild_id = $3 AND COALESCE(event_type, $2) = $2", channel.id, name, ctx.guild.id)

                await conn.execute(
                    "UPDATE server_data SET channel_id = $1 WHERE guild_id = $2 AND event_type = $3",
                    channel.id,
                    ctx.guild.id,
                    name,
                )  # DB DOESNT WORK ?

        await channel.send(
            embed=discord.Embed(
                description=f"This channel has been set as a *{name}* channel.",
                color=cs.RANDOM_COLOR,
            )
        )
        return await ctx.reply(
            embed=discord.Embed(description=string, color=cs.RANDOM_COLOR),
            permission_cmd=True,
        )

    async def message_display(self: Self, ctx: Context, name: str) -> Optional[discord.Message]:
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
            embed=discord.Embed(
                title=f"{name.capitalize()} channel message",
                description=f"```{result[0]}```",
                color=cs.RANDOM_COLOR,
            ),
            permission_cmd=True,
        )

    async def channel_display(self: Self, ctx: Context, name: str) -> Optional[discord.Message]:
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
            embed=discord.Embed(
                description=f"{name.capitalize()} channel is currently set to {channel.mention}",
                color=cs.RANDOM_COLOR,
            ),
            permission_cmd=True,
        )

    async def remove(self, ctx: Context, name: str) -> Optional[discord.Message]:
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
            embed=discord.Embed(
                description=f"{name.capitalize()} channel has been removed.",
                color=cs.RANDOM_COLOR,
            ),
            permission_cmd=True,
        )


class Config(Cog):
    def __init__(self: Self, bot: Bot) -> None:
        self.bot: Bot = bot
        self._channel: ChannelConfig = ChannelConfig(self.bot)
        self._prefix: PrefixConfig = PrefixConfig(self.bot)

    # set perms per command instead
    @commands.hybrid_group(aliases=["prefixes"], invoke_without_command=True, with_app_command=False)
    @commands.guild_only()
    async def prefix(self: Self, ctx: Context):
        async with ctx.typing():
            return await self._prefix.display_prefixes(ctx)

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.guild_only()
    @prefix.command(name="add", help="Adds bot prefix to the guild.")
    async def add_prefix(self: Self, ctx: Context, *, prefix: str):
        _prefix: List[str] = prefix.split()
        if len(_prefix) > 1:
            return await ctx.reply("Prefix musn't contain whitespaces.", user_mistake=True)

        return await self._prefix.set_prefix(ctx, prefix)

    @prefix.command(name="display", help="Displays all prefixes.")
    async def display_prefix(self: Self, ctx: Context):
        return await self._prefix.display_prefixes(ctx)

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.guild_only()
    @prefix.command(name="remove", description="Removes guild's prefix(es).")
    async def delete_prefix(self: Self, ctx: Context, prefix: str):
        return await self._prefix.remove_prefix(ctx, prefix)

    @delete_prefix.autocomplete("prefix")
    async def autocomplete_callback_(self: Self, interaction: discord.Interaction, current: str):
        return await self.bot.autocomplete.choice_autocomplete(interaction, current, "prefixes", "prefix", None, True)

    @commands.hybrid_group(invoke_without_command=True, with_app_command=True)
    @commands.bot_has_permissions(manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True, manage_messages=True)
    @commands.guild_only()  # perms aren't active if invoke without cmd is active
    async def welcome(self: Self, ctx: Context) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            # welcome_help_embed = discord.Embed(title="✨ WELCOME HELP ✨", description = tv.on_member_join_help_welcome_embed_description, color = tv.color)
            # welcome_help_embed.set_footer(text=tv.footer) # help comm comprehensive group desc

            embed = discord.Embed(description="```$welcome [command name]```", color=cs.WARNING_COLOR)
            return await ctx.reply(embed=embed, user_mistake=True)

    @welcome.group(invoke_without_command=True, with_app_command=True, name="message")
    async def w_message(self: Self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            embed = discord.Embed(
                description="```$welcome message [command name]```",
                color=cs.WARNING_COLOR,
            )
            return await ctx.reply(embed=embed, user_mistake=True)

    @welcome.group(invoke_without_command=True, with_app_command=True, name="channel")
    async def w_channel(self: Self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            embed = discord.Embed(
                description="```$welcome channel [command name]```",
                color=cs.WARNING_COLOR,
            )
            return await ctx.reply(embed=embed, user_mistake=True)

    @w_channel.command(name="set", description="Sets chosen channel as a welcome channel.")
    async def welcome_channel_set(
        self: Self,
        ctx: Context,
        channel: Optional[discord.TextChannel] = commands.CurrentChannel,
    ):
        return await self._channel.add_channel(ctx, "welcome", channel)

    @w_message.command(name="set", description="You can use this command to set a welcome message.")
    async def welcome_message_set(self: Self, ctx: Context, *, text: str):  # ,* (?)
        return await self._channel.add_message(ctx, "welcome", text)

    @w_message.command(
        name="display",
        description="Displays the current welcome message if there is one.",
    )
    async def welcome_message_display(self: Self, ctx: Context):
        return await self._channel.message_display(ctx, "welcome")

    @w_channel.command(
        name="display",
        description="Displays the current welcome channel if there is one.",
    )
    async def welcome_channel_display(self: Self, ctx: Context):
        return await self._channel.channel_display(ctx, "welcome")

    @w_channel.command(name="remove", description="Removes the welcome channel.")
    async def welcome_channel_remove(self: Self, ctx: Context):
        return await self._channel.remove(ctx, "welcome")

    @welcome.command(name="help", description="Welcome help.")
    async def help(self: Self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            help_welcome_help_embed = discord.Embed(
                title="✨ COMPREHENSIVE WELCOME/LEAVE HELP ✨",
                description=cs.on_member_join_help_welcome_help_embed_description,
                color=cs.RANDOM_COLOR,
            )  # DEFINE THIS IN HELP CMD THEN MAKE USER CALL IT INSTEAD OR BOTH
            help_welcome_help_embed.set_image(
                url="\n https://cdn.discordapp.com/attachments/811285768549957662/989299841895108668/ggggg.png"
            )
            help_welcome_help_embed.set_footer(text=cs.FOOTER)

            return await ctx.reply(embed=help_welcome_help_embed)  # add to help cmd instead

    @commands.hybrid_group(invoke_without_command=True, with_app_command=True)
    @commands.bot_has_permissions(manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True, manage_messages=True)  # REDO PERMS
    @commands.guild_only()
    async def leave(self: Self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            # leave_help_embed = discord.Embed(title="✨ LEAVE HELP ✨", description = tv.on_member_leave_help_welcome_embed_description, color = tv.color)
            # leave_help_embed.set_footer(text=tv.footer) #help comm group descript

            embed = discord.Embed(description="```$leave [command name]```", color=cs.WARNING_COLOR)
            return await ctx.reply(embed=embed, user_mistake=True)

    @leave.group(invoke_without_command=True, with_app_command=True, name="message")
    async def l_message(self: Self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            embed = discord.Embed(
                description="```$leave message [command name]```",
                color=cs.WARNING_COLOR,
            )
            return await ctx.reply(embed=embed, user_mistake=True)

    @leave.group(invoke_without_command=True, with_app_command=True, name="channel")
    async def l_channel(self: Self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            embed = discord.Embed(
                description="```$leave channel [command name]```",
                color=cs.WARNING_COLOR,
            )
            return await ctx.reply(embed=embed, user_mistake=True)

    @l_channel.command(name="set", description="Sets chosen channel as a leave channel.")
    async def leave_channel_set(
        self: Self,
        ctx: Context,
        channel: Optional[discord.TextChannel] = commands.CurrentChannel,
    ):
        return await self._channel.add_channel(ctx, "leave", channel)

    @l_message.command(name="set", description="You can use this command to set a leave message.")
    async def leave_message_set(self: Self, ctx: Context, *, text: str):
        return await self._channel.add_message(ctx, "leave", text)

    @l_message.command(
        name="display",
        description="Displays the current leave message if there is one.",
    )
    async def leave_message_display(self: Self, ctx: Context):
        return await self._channel.message_display(ctx, "leave")

    @l_channel.command(
        name="display",
        description="Displays the current leave channel if there is one.",
    )
    async def leave_channel_display(self: Self, ctx: Context):
        return await self._channel.channel_display(ctx, "leave")

    @l_channel.command(name="remove", description="Removes the leave channel.")
    async def leave_channel_remove(self: Self, ctx: Context):
        return await self._channel.remove(ctx, "leave")

    @leave.command(name="help", description="Leave help.")
    async def l_help(self: Self, ctx: commands.Context):
        async with ctx.typing(ephemeral=True):
            help_leave_help_embed = discord.Embed(
                title="✨ COMPREHENSIVE WELCOME/LEAVE HELP ✨",
                description=cs.on_member_join_help_welcome_help_embed_description,
                color=cs.RANDOM_COLOR,
            )
            help_leave_help_embed.set_image(
                url="\n https://cdn.discordapp.com/attachments/811285768549957662/989299841895108668/ggggg.png"
            )
            help_leave_help_embed.set_footer(text=cs.FOOTER)

            return await ctx.reply(embed=help_leave_help_embed)

    @commands.hybrid_group(invoke_without_command=True, with_app_command=True)
    @commands.bot_has_permissions(manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True, manage_messages=True)  # change to admin maybe
    @commands.guild_only()
    async def twitch(self: Self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            embed = discord.Embed(description="```$twitch [command name]```", color=cs.WARNING_COLOR)
            return await ctx.reply(embed=embed, user_mistake=True)

    @twitch.group(invoke_without_command=True, with_app_command=True, name="message")
    async def t_message(self: Self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            embed = discord.Embed(
                description="```$twitch message [command_name]```",
                color=cs.WARNING_COLOR,
            )
            return await ctx.reply(embed=embed, user_mistake=True)

            # return await ConfigFunctions.add_message(ctx, "twitch", text)

    @twitch.group(invoke_without_command=True, with_app_command=True, name="channel")
    async def t_channel(self: Self, ctx: Context):
        async with ctx.typing(ephemeral=True):
            embed = discord.Embed(
                description="```$twitch channel [command_name]```",
                color=cs.WARNING_COLOR,
            )
            return await ctx.reply(embed=embed, user_mistake=True)

            # return await ConfigFunctions.add_channel(ctx, "twitch", channel) # SET CHANNEL WHEN ON invoke_without_command

    @t_channel.command(
        name="set",
        help="Sets a channel where your twitch notifications will be posted.",
    )
    async def twitch_channel_set(
        self: Self,
        ctx: Context,
        channel: Optional[discord.TextChannel] = commands.CurrentChannel,
    ):
        return await self._channel.add_channel(ctx, "twitch", channel)

    @t_message.command(name="set", help="Sets a notification message.")
    async def twitch_message_set(self: Self, ctx: Context, *, text: str):
        return await self._channel.add_message(ctx, "twitch", text)

    @t_message.command(
        name="display",
        description="Displays the current twitch message if there is one.",
    )
    async def twitch_message_display(self: Self, ctx: Context):
        return await self._channel.message_display(ctx, "twitch")

    @t_channel.command(
        name="display",
        description="Displays the current twitch channel if there is one.",
    )
    async def twitch_channel_display(self: Self, ctx: Context):
        return await self._channel.channel_display(ctx, "twitch")

    @t_channel.command(name="remove", description="Removes the twitch channel.")
    async def twitch_channel_remove(self: Self, ctx: Context):
        return await self._channel.remove(ctx, "twitch")  # MAYBE REMOVE CHANNEL_REMOVE COMMS

    @twitch.command(
        name="add",
        help="Sets a twitch streamer. The notification shall be posted when the streamer goes online.",
    )
    async def add_twitch_streamer(self: Self, ctx: commands.Context, twitch_streamer_name: str):
        return await self.bot.twitch.event_subscription(ctx, "stream.online", twitch_streamer_name)

    @twitch.command(name="list", help="Shows the list of streamers guild is subscribed to.")
    async def twitch_streamer_list(self: Self, ctx: Context):
        return await self.bot.twitch.guild_twitch_subscriptions(ctx)

    @twitch.command(name="remove", help="Removes a twitch subscription.")
    async def twitch_streamer_remove(self: Self, ctx: Context, username: str):  # add choice to delete all
        return await self.bot.twitch.twitch_unsubscribe_from_streamer(ctx, username)

    @twitch_streamer_remove.autocomplete("username")
    async def autocomplete_callback_(self: Self, interaction: discord.Interaction, current: str):  # MAKE IT A GLOBAL FUNC
        return await self.bot.autocomplete.choice_autocomplete(
            interaction, current, "twitch_users", "username", "user_id", True
        )


# RESTRUCTURE GROUP-SUBGROUP CONNECTIONS LIKE: welcome set channel/message | welcome display channel/message (?)
# GLOBAL CHANNEL/MESSAGE DISPLAY THAT WILL SHOW MESSAGE/CHANNEL FOR EACH EVENT_TYPE (?)
# CHANNEL/MESSAGE DISPLAY FOR ALL
# TWITCH (DB) SUBSCRIPTION TO USERS (USER LIST THAT GUILD IS SUBSCRIBED TO) DISPLAY
# twitch.py IN UTILS
# MAYBE A LIST OF EVENTSUBS PER TWITCH USER (LET PEOPLE SUBSCRIBE TO OTHER EVENTS INSTEAD OF JUST SUBSCRIBING TO ON_STREAM)
