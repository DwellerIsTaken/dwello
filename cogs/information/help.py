from __future__ import annotations

import asyncio
import datetime
import difflib
import inspect
import itertools
import os
import time
import traceback
from typing import Any, Dict, List, Optional, Set, Tuple, Union  # noqa: F401

import discord
from discord import app_commands  # noqa: F401
from discord import Interaction
from discord.ext import commands
from discord.ui import Select, button, select
from typing_extensions import Self, override

import constants as cs
from core import Dwello, DwelloContext

from .news import NewsViewer

newline = "\n"


async def setup(bot: Dwello):
    await bot.add_cog(About(bot))


class HelpCentre(discord.ui.View):
    def __init__(
        self,
        ctx: DwelloContext,
        other_view: discord.ui.View,
    ):
        super().__init__()
        self.embed = None
        self.ctx = ctx
        self.bot: Dwello = self.ctx.bot
        self.other_view = other_view

    @discord.ui.button(emoji="🏠", label="Go Back", style=discord.ButtonStyle.blurple)
    async def go_back(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(embed=self.embed, view=self.other_view)
        self.stop()

    async def start(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Here is a guide on how to understand this help command",
            description="\n__**Do not not include these brackets when running a command!**__"
            "\n__**They are only there to indicate the argument type**__",
            color=cs.RANDOM_COLOR,
        )
        embed.add_field(
            name="`<argument>`",
            value="Means that this argument is __**required**__",
            inline=False,
        )
        embed.add_field(
            name="`[argument]`",
            value="Means that this argument is __**optional**__",
            inline=False,
        )
        embed.add_field(
            name="`[argument='default']`",
            value="Means that this argument is __**optional**__ and has a default value",
            inline=False,
        )
        embed.add_field(
            name="`[argument]...` or `[argument...]`",
            value="Means that this argument is __**optional**__ and can take __**multiple entries**__",
            inline=False,
        )
        embed.add_field(
            name="`<argument>...` or `<argument...>`",
            value="Means that this argument is __**required**__ and can take __**multiple entries**__",
            inline=False,
        )
        embed.add_field(
            name="`[X|Y|Z]`",
            value="Means that this argument can be __**either X, Y or Z**__",
            inline=False,
        )
        embed.set_footer(text="To continue browsing the help menu, press 🏠Go Back")
        embed.set_author(name="About this Help Command", icon_url=self.bot.user.display_avatar.url)
        self.embed = interaction.message.embeds[0]
        self.add_item(discord.ui.Button(label="Support Server", url="https://discord.gg/8FKNF8pC9u"))
        """self.add_item(
            discord.ui.Button(
                label="Invite Me",
                url=discord.utils.oauth_url(
                    self.bot.user.id,
                    permissions=discord.Permissions(294171045078),
                    scopes=("applications.commands", "bot"),
                ),
            )
        )"""  # Later
        await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user and interaction.user == self.ctx.author:
            return True
        await interaction.response.defer()
        return False


class HelpView(discord.ui.View):
    def __init__(
        self,
        ctx: DwelloContext,
        data: Dict[commands.Cog, List[Union[commands.Command, discord.app_commands.Command]]],
        help_command: commands.HelpCommand,
    ):
        super().__init__()
        self.ctx = ctx
        self.bot: Dwello = self.ctx.bot
        self.data = data
        self.current_page = 0
        self.help_command = help_command
        self.message: discord.Message = None
        self.main_embed = self.build_main_page()
        self.embeds: List[discord.Embed] = [self.main_embed]
        self.owner_cmds: List[commands.Command] = self.construct_owner_commands()

    @select(placeholder="Select a category", row=0)
    async def category_select(self, interaction: Interaction, select: Select):
        if select.values[0] == "index":
            self.current_page = 0
            self.embeds = [self.main_embed]
            self._update_buttons()
            return await interaction.response.edit_message(embed=self.main_embed, view=self)

        if cog := self.bot.get_cog(select.values[0]):
            self.embeds = self.build_embeds(cog)
            self.current_page = 0
            self._update_buttons()
            return await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            return await interaction.response.send_message("Somehow, that category was not found? 🤔", ephemeral=True)
    
    def construct_owner_commands(self) -> List[commands.Command]:
        owner_cmds: List[commands.Command] = []
        hidden_cmds: List[commands.Command] = []

        for cog, comm in self.data.items():
            for cmd in comm:
                if cog.qualified_name == "Owner":
                    owner_cmds.append(cmd)
                else:
                    if isinstance(cmd, app_commands.Command):
                        continue
                    if cmd.hidden:
                        hidden_cmds.append(cmd)

        return owner_cmds + hidden_cmds
    
    def clean_command_count(self, cog: commands.Cog, commands: List[commands.Command, app_commands.Command]) -> int:
        if cog.qualified_name == "Owner":
            return len(self.owner_cmds)
        
        count = 0
        for command in commands:
            if isinstance(command, app_commands.Command):
                count += 1
                continue
            if not command.hidden:
                count += 1

        return count

    def build_embeds(self, cog: commands.Cog) -> List[discord.Embed]:
        embeds = []

        for cog_, comm in self.data.items():
            if cog_ != cog:
                continue
            
            owner = False
            if cog_.qualified_name == "Owner":
                comm = self.owner_cmds
                owner = True

            description_clean: str = ' '.join(cog.description.splitlines()) if cog.description else "No description provided."  # noqa: E501
            embed: discord.Embed = discord.Embed(
                title=f"{cog.qualified_name} commands [{self.clean_command_count(cog_, comm)}]",
                color=cs.RANDOM_COLOR,
                description=description_clean,
            )
            embed.set_footer(text='For more info on a command run "help [command]"')
            # maybe another embed build for slash cause cant use that with owner cmds
            for cmd in comm:
                name = f"`{cmd.name}`"
                value = "See help for this command in an NSFW channel." if cmd.extras.get("nsfw", False) else None
                if isinstance(cmd, app_commands.Command):
                    if not value:
                        desc = cmd.description or "No help given..."
                else:
                    if cmd.hidden and not owner:
                        continue
                    if not value:
                        name = f"`{cmd.name}{f' {cmd.signature}`' if cmd.signature else '`'}"
                        desc = cmd.brief or cmd.help or "No help given..."
                if not value:
                    parent = f"\n> Parent: `{cmd.parent}`" if cmd.parent else ""
                    value = (f"> {desc} {parent}")[:1024]

                embed.add_field(name=name, value=value, inline=False)

                if len(embed.fields) == 5:
                    embeds.append(embed)
                    embed = discord.Embed(
                        title=f"{cog.qualified_name} commands [{len(comm)}]",
                        color=cs.RANDOM_COLOR,
                        description=description_clean,
                    )

            if len(embed.fields) > 0:
                embeds.append(embed)

            return embeds

    def build_select(self: Self) -> None:
        self.category_select.options = []
        self.category_select.add_option(label="Main Page", value="index", emoji="🏠")
        for cog, comm in self.data.items():
            if cog.qualified_name == "Owner":
                comm = self.owner_cmds
            if not comm:
                continue
            emoji = getattr(cog, "select_emoji", None)
            label = f"{cog.qualified_name} ({self.clean_command_count(cog, comm)})"
            brief = getattr(cog, "select_brief", None)
            self.category_select.add_option(label=label, value=cog.qualified_name, emoji=emoji, description=brief)

    def build_main_page(self: Self) -> discord.Embed:
        embed: discord.Embed = discord.Embed(
            color=cs.RANDOM_COLOR,
            title="Bot Help Menu",
            description="Hello, I'm Bot! I'm still in development, but you can use me.",
        )
        embed.add_field(
            name="Getting Help",
            inline=False,
            value="Use `$help <command>` for more info on a command."
            "\nThere is also `$help <command> [subcommand]`."
            "\nUse `$help <category>` for more info on a category."
            "\nYou can also use the menu below to view a category.",
        )
        embed.add_field(
            name="Getting Support",
            inline=False,
            value="To get help or __**suggest features**__, you can join my"
            "\nsupport server: **__<https://discord.gg/8FKNF8pC9u>__**"
            "\n📨 You can also DM me for help if you prefer to,"
            "\nbut please join the support server for suggestions.",
        )
        embed.add_field(
            name="Who Am I?",
            inline=False,
            value="I'm Bot, a multipurpose discordbot. You can use me to play games, moderate "
            "\nyour server, mess with some images and more! Check out "
            "\nall my features using the dropdown below.",
        )
        embed.add_field(
            name="Support DuckBot",
            value="Add patreon later.",
            inline=False,
        )
        embed.add_field(
            name="\t",
            value="Invaluable assistance: <:github:1100906448030011503> [LeoCx1000](https://github.com/leoCx1000).",
            inline=False,
        )
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url)
        return embed

    @button(emoji="❓", label="help", row=1, style=discord.ButtonStyle.green)
    async def help(self, interaction: Interaction, _):
        view = HelpCentre(self.ctx, self)
        await view.start(interaction)  # make better buttons later

    @button(label="<", row=1)
    async def previous(self, interaction: Interaction, _):
        self.current_page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @button(emoji="🗑", row=1, style=discord.ButtonStyle.red)
    async def _end(self, interaction: Interaction, _):
        await interaction.message.delete(delay=0)
        """if self.ctx.channel.permissions_for(self.ctx.me).add_reactions:
            await self.ctx.message.add_reaction(random.choice(constants.DONE))"""

    @button(label=">", row=1)  # emoji
    async def next(self, interaction: Interaction, _):
        self.current_page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(emoji="📰", label="news", row=1, style=discord.ButtonStyle.green)
    async def vote(self, interaction: Interaction, _):
        news = await self.bot.pool.fetch("SELECT * FROM news ORDER BY news_id DESC")
        await NewsViewer.from_interaction(interaction, news, embed=self.embeds[self.current_page], old_view=self)

    def _update_buttons(self: Self) -> None:
        styles = {True: discord.ButtonStyle.gray, False: discord.ButtonStyle.blurple}
        page = self.current_page
        total = len(self.embeds) - 1
        self.next.disabled = page == total
        self.previous.disabled = page == 0
        self.next.style = styles[page == total]
        self.previous.style = styles[page == 0]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user == self.ctx.author:
            return True
        await interaction.response.defer()
        return False

    async def on_timeout(self: Self) -> None:
        self.clear_items()
        await self.message.edit(view=self)

    async def start(self: Self) -> Optional[discord.Message]:
        self.build_select()
        self._update_buttons()
        self.message = await self.ctx.send(embed=self.main_embed, view=self)


class MyHelp(commands.HelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.context: DwelloContext

    @override
    def get_bot_mapping(self):
        """Retrieves the bot mapping passed to :meth:`send_bot_help`."""
        bot = self.context.bot
        ignored_cogs = [
            "CommandErrorHandler",
            "Other",
            "Jishaku",
        ]
        if not self.context.is_bot_owner:
            ignored_cogs.append("Owner")

        mapping = {}

        for cog in sorted(bot.cogs.values(), key=lambda c: len(c.get_commands()), reverse=True):
            if cog.qualified_name in ignored_cogs:
                continue

            commands_list: List[Union[commands.Command, discord.app_commands.Command]] = []
            for command in cog.walk_commands():
                if isinstance(command, commands.Group):
                    subcommands = command.commands
                    while (
                        isinstance(subcommands, list)
                        and len(subcommands) == 1
                        and isinstance(subcommands[0], commands.Group)
                    ):
                        subcommands = subcommands[0].commands

                    if isinstance(subcommands, list):
                        commands_list.extend(subcommands)
                    elif isinstance(subcommands, commands.Command):
                        commands_list.append(subcommands)
                else:
                    commands_list.append(command)

            for app_command in cog.walk_app_commands():
                allowed = 1
                for i in commands_list:
                    if app_command.name == i.name:
                        if not isinstance(i, commands.Group):
                            allowed = 0
                if allowed:
                    commands_list.append(app_command)
                
            mapping[cog] = commands_list

        return mapping

    def get_minimal_command_signature(self, command):
        if isinstance(command, commands.Group):
            return f"[G] {self.context.clean_prefix}{command.qualified_name} {command.signature}"
        return f"(c) {self.context.clean_prefix}{command.qualified_name} {command.signature}"

    async def send_bot_help(self, mapping):
        view = HelpView(self.context, data=mapping, help_command=self)
        await view.start()

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(
            title=f"`{self.context.clean_prefix}{command}`",
            description="**Description:**\n" + 
            (command.help or command.description or "No help given...").replace("%PRE%", self.context.clean_prefix),
        )
        embed.add_field(
            name="Command usage:",
            value=f"```css\n{self.get_minimal_command_signature(command)}\n```",
        )
        try:
            preview = command.__original_kwargs__["preview"]
            embed.set_image(url=preview) # 
        except KeyError:
            pass
        if command.aliases:
            embed.description = f'{embed.description}\n\n**Aliases:**\n`{"`, `".join(command.aliases)}`'
        try:
            await command.can_run(self.context)
        except BaseException as e:
            try:
                if isinstance(e, commands.CheckAnyFailure):
                    for e in e.errors:
                        if not isinstance(e, commands.NotOwner):
                            raise e
                raise e
            except commands.MissingPermissions as error:
                embed.add_field(
                    name="Permissions you're missing:",
                    value=", ".join(error.missing_permissions).replace("_", " ").replace("guild", "server").title(),
                    inline=False,
                )
            except commands.BotMissingPermissions as error:
                embed.add_field(
                    name="Permissions i'm missing:",
                    value=", ".join(error.missing_permissions).replace("_", " ").replace("guild", "server").title(),
                    inline=False,
                )
            except commands.NotOwner:
                embed.add_field(name="Rank you are missing:", value="Bot owner", inline=False)
            except commands.PrivateMessageOnly:
                embed.add_field(
                    name="Cant execute this here:",
                    value="Can only be executed in DMs.",
                    inline=False,
                )
            except commands.NoPrivateMessage:
                embed.add_field(
                    name="Cant execute this here:",
                    value="Can only be executed in a server.",
                    inline=False,
                )
            except commands.DisabledCommand:
                embed.add_field(
                    name="Cant execute this command:",
                    value="This command is currently disabled.",
                    inline=False,
                )
            except commands.NSFWChannelRequired:
                embed.add_field(
                    name="Cant execute this here:",
                    value="This command can only be used in an NSFW channel.",
                    inline=False,
                )
            except Exception as exc:
                embed.add_field(
                    name="Cant execute this command:",
                    value="Unknown/unhandled reason.",
                    inline=False,
                )
                print(f"{command} failed to execute: {exc}")
        finally:
            await self.context.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        if entries := cog.get_commands():
            data = [self.get_minimal_command_signature(entry) for entry in entries]
            description_clean: str = ' '.join(cog.description.splitlines()) if cog.description else "No description provided."   # noqa: E501
            embed = discord.Embed(
                title=f"`{cog.qualified_name}` category commands",
                description="**Description:**\n" + description_clean.replace("%PRE%", self.context.clean_prefix),
            )
            embed.description = (
                f"{embed.description}\n\n**Commands:**\n```css\n{newline.join(data)}\n```\n"
                f"`[G] - Group` These have sub-commands.\n`(C) - Command` These do not have sub-commands."
            )
            await self.context.send(embed=embed)
        else:
            await self.context.send(f"No commands found in {cog.qualified_name}")

    async def send_group_help(self, group: commands.Group):
        embed = discord.Embed(
            title=f"`{self.context.clean_prefix}{group}`",
            description="**Description:**\n"
            + (group.help or group.description or "No help given...").replace("%PRE%", self.context.clean_prefix),
        )
        embed.add_field(
            name="Group usage:",
            value=f"```css\n{self.get_minimal_command_signature(group)}\n```",
        )
        if group.aliases:
            embed.description = f'{embed.description}\n\n**Aliases:**\n`{"`, `".join(group.aliases)}`'
        if group.commands:
            subgroups: List[commands.Group] = []
            subcommands: List[commands.Command] = []
            for c in group.commands:
                if isinstance(c, commands.Group):
                    subgroups.append(c)
                else:
                    subcommands.append(c)
            
            if subcommands:
                c_formatted = "\n".join([self.get_minimal_command_signature(command) for command in subcommands])
                embed.add_field(
                    name="Sub-commands for this command:",
                    value=f"```css\n{c_formatted}\n```",
                    inline=False,
                )
            if subgroups:
                g_formatted = "\n".join([self.get_minimal_command_signature(group) for group in subgroups])
                embed.add_field(
                    name="Sub-groups for this command:",
                    value=f"```css\n{g_formatted}\n```\n**Do `{self.context.clean_prefix}help command subcommand` for more info on a sub-command**",  # noqa: E501
                    inline=False,
                )
        # noinspection PyBroadException
        try:
            await group.can_run(self.context)
        except commands.MissingPermissions as error:
            embed.add_field(
                name="Permissions you're missing:",
                value=", ".join(error.missing_permissions).replace("_", " ").replace("guild", "server").title(),
                inline=False,
            )
        except commands.BotMissingPermissions as error:
            embed.add_field(
                name="Permissions i'm missing:",
                value=", ".join(error.missing_permissions).replace("_", " ").replace("guild", "server").title(),
                inline=False,
            )

        except commands.NotOwner:
            embed.add_field(name="Rank you are missing:", value="Bot owner", inline=False)
        except commands.PrivateMessageOnly:
            embed.add_field(
                name="Cant execute this here:",
                value="Can only be executed in DMs.",
                inline=False,
            )
        except commands.NoPrivateMessage:
            embed.add_field(
                name="Cant execute this here:",
                value="Can only be executed in a server.",
                inline=False,
            )
        except commands.DisabledCommand:
            embed.add_field(
                name="Cant execute this command:",
                value="This command is restricted to slash commands.",
                inline=False,
            )
        except Exception as exc:
            embed.add_field(name="Cant execute this command:", value="Unknown error.", inline=False)
            print(f"{group} failed to execute: {exc}")
        finally:
            await self.context.send(embed=embed)

    @override
    def command_not_found(self, string):
        return string

    @override
    def subcommand_not_found(self, command, string):
        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            return command.qualified_name + string
        return command.qualified_name

    @override
    async def send_error_message(self, error):
        if matches := difflib.get_close_matches(error, self.context.bot.cogs.keys()):
            confirm = await self.context.confirm(  # look into this
                message=f"Sorry but i couldn't recognise {error} as one of my categories!"
                f"\n{f'**did you mean... `{matches[0]}`?**' if matches else ''}",
                delete_after_confirm=True,
                delete_after_timeout=True,
                delete_after_cancel=True,
                buttons=(
                    ("✅", f"See {matches[0]}"[:80], discord.ButtonStyle.blurple),
                    ("🗑", None, discord.ButtonStyle.red),
                ),
                timeout=15,
            )
            if confirm is True:
                return await self.send_cog_help(self.context.bot.cogs[matches[0]])
            return
        else:
            command_names = []
            for command in list(self.context.bot.commands):
                # noinspection PyBroadException
                try:
                    if await command.can_run(self.context):
                        command_names.append([command.name] + command.aliases)
                except Exception:
                    continue
            command_names = list(itertools.chain.from_iterable(command_names))
            if matches := difflib.get_close_matches(error, command_names):
                confirm = await self.context.confirm(
                    message=f"Sorry but i couldn't recognise {error} as one of my commands!"
                    f"\n{f'**did you mean... `{matches[0]}`?**' if matches else ''}",
                    delete_after_confirm=True,
                    delete_after_timeout=True,
                    delete_after_cancel=True,
                    buttons=(
                        (
                            "✅",
                            f"See {matches[0]}"[:80],
                            discord.ButtonStyle.blurple,
                        ),
                        ("🗑", None, discord.ButtonStyle.red),
                    ),
                    timeout=15,
                )
                if confirm is True:
                    return await self.send_command_help(self.context.bot.get_command(matches[0]))
                return

        await self.context.send(
            f'Sorry but i couldn\'t recognise "{discord.utils.remove_markdown(error)}" as one of my commands or categories!'
            f"\nDo `{self.context.clean_prefix}help` for a list of available commands! 💞"
        )

    @override
    async def on_help_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(
                embed=discord.Embed(
                    title=str(error.original),
                    description="".join(traceback.format_exception(error.__class__, error, error.__traceback__)),
                )
            )


class About(commands.Cog):
    """
    😮
    Commands related to the bot itself, that have the only purpose to show information.
    """

    def __init__(self, bot: Dwello) -> None:
        self.bot: Dwello = bot
        help_command = MyHelp()
        help_command.command_attrs = {
            "help": "Shows help about a command or category, it can also display other useful information, such as "
            "examples on how to use the command, or special syntax that can be used for a command, for example, "
            "in the `welcome message` command, it shows all available special tags.",
            "name": "help",
        }
        help_command.cog = self
        bot.help_command = help_command
        self.select_emoji = "<:info:895407958035431434>"
        self.select_brief = "Bot Information commands."

    def get_uptime(self: Self) -> Tuple[int, int, int, int]:
        """Return format: days, hours, minutes, seconds."""

        uptime = datetime.datetime.now(datetime.timezone.utc) - self.bot.uptime

        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        return days, hours, minutes, seconds

    def get_startup_timestamp(self, style: discord.utils.TimestampStyle = None) -> str:
        return discord.utils.format_dt(self.bot.uptime, style=style or "F")

    def get_average_latency(self, *latencies: float) -> Union[Any, float]:
        if not latencies:
            raise TypeError("Missing required argument: 'latencies'")

        pings = list(latencies)
        number = sum(pings)
        return number / len(pings)

    # make uptime: add here -> trigger on mention in on_message
    @commands.hybrid_command(name="hello", aliases=cs.HELLO_ALIASES, with_app_command=True)
    async def hello(self, ctx: DwelloContext) -> Optional[discord.Message]:
        # make variations for the response
        prefix: str = str(self.bot.DEFAULT_PREFIXES[0])
        content: str = f"Hello there! I'm {self.bot.user.name}. Use `{prefix}help` for more."  # {self.bot.help_command}?
        return await ctx.send(content=content)  # display more info about bot

    # uptime cmd
    # add some latency too or smth
    # get available bot info i guess
    @commands.hybrid_command(name="about", aliases=["botinfo", "info", "bi"], with_app_command=True)
    async def about(self, ctx: DwelloContext) -> Optional[discord.Message]:
        information: discord.AppInfo = await self.bot.application_info()
        print(information)

        embed: discord.Embed = discord.Embed(
            description=f"{cs.GITHUB_EMOJI} [Source]({cs.GITHUB})",
            color=cs.RANDOM_COLOR,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_author(
            name=f"Stolen by {information.owner}",
            icon_url=information.owner.display_avatar.url,
        )
        # description=f"{constants.GITHUB} [source]({self.bot.repo}) | "
        # f"{constants.INVITE} [invite me]({self.bot.invite_url}) | "
        # f"{constants.TOP_GG} [top.gg]({self.bot.vote_top_gg}) | "
        # f"{constants.BOTS_GG} [bots.gg]({self.bot.vote_bots_gg})"
        # f"\n_ _╰ Try also `{ctx.prefix}source [command]`"

        # embed.add_field(name="Latest updates:", value=get_latest_commits(limit=5), inline=False) maybe later

        # discord.ui.Button(label="Source", url="")

        return await ctx.send(embed=embed)

    @commands.hybrid_command(name="uptime", help="Returns bot's uptime.", with_app_command=True)
    async def uptime(self, ctx: DwelloContext) -> Optional[discord.Message]:
        days, hours, minutes, seconds = self.get_uptime()
        timestamp = self.get_startup_timestamp()

        embed: discord.Embed = discord.Embed(
            title="Current Uptime", 
            description=f"**{days} days, {hours} hours, {minutes} minutes, {seconds} seconds**",
            color=cs.RANDOM_COLOR,
        )
        embed.add_field(name="Startup Time", value=timestamp, inline=False)
        return await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="ping",
        aliases=["latency", "latencies"],
        help="Pong.",
        with_app_command=True,
    )
    async def ping(self, ctx: DwelloContext) -> Optional[discord.Message]:  # work on return design?
        typing_start = time.monotonic()
        await ctx.typing()
        typing_end = time.monotonic()
        typing_ms = (typing_end - typing_start) * 1000

        start = time.perf_counter()
        message = await ctx.send("🏓 pong!")
        end = time.perf_counter()
        message_ms = (end - start) * 1000

        latency_ms = self.bot.latency * 1000

        postgres_start = time.perf_counter()
        await self.bot.pool.fetch("SELECT 1")
        postgres_end = time.perf_counter()
        postgres_ms = (postgres_end - postgres_start) * 1000

        average = self.get_average_latency(typing_ms, message_ms, latency_ms, postgres_ms)

        await asyncio.sleep(0.7)

        return await message.edit(
            content=None,
            embed=discord.Embed(
                color=cs.RANDOM_COLOR,
                description=(
                    f"**`Websocket -> {round(latency_ms, 3)}ms{' ' * (9 - len(str(round(latency_ms, 3))))}`**\n"
                    f"**`Typing    -> {round(typing_ms, 3)}ms{' ' * (9 - len(str(round(typing_ms, 3))))}`**\n"
                    f"**`Message   -> {round(message_ms, 3)}ms{' ' * (9 - len(str(round(message_ms, 3))))}`**\n"
                    f"**`Database  -> {round(postgres_ms, 3)}ms{' ' * (9 - len(str(round(postgres_ms, 3))))}`**\n"
                    f"**`Average   -> {round(average, 3)}ms{' ' * (9 - len(str(round(average, 3))))}`**\n"
                ),
            ),
        )

    @commands.hybrid_command(name="stats", help="Returns some of the bot's stats", with_app_command=True)
    async def stats(self, ctx: DwelloContext) -> Optional[discord.Message]:
        typing_start = time.monotonic()
        await ctx.typing()
        typing_end = time.monotonic()
        typing_ms = (typing_end - typing_start) * 1000

        latency_ms = self.bot.latency * 1000

        postgres_start = time.perf_counter()
        await self.bot.pool.fetch("SELECT 1")
        postgres_end = time.perf_counter()
        postgres_ms = (postgres_end - postgres_start) * 1000

        average = self.get_average_latency(typing_ms, latency_ms, postgres_ms)

        embed: discord.Embed = discord.Embed(
            title="Bot Statistics since launch",
            color=cs.RANDOM_COLOR,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(name="Guilds", value=len(self.bot.guilds), inline=False)
        embed.add_field(
            name="Responses",
            value=self.bot.reply_count or 1,
            inline=False,
        )
        embed.add_field(name="Total Commands", value=len(self.bot.commands), inline=False)
        embed.add_field(
            name="Average Latency",
            value=f"**`{round(average, 3)}ms{' ' * (9 - len(str(round(average, 3))))}`**",
            inline=False,
        )
        embed.add_field(
            name="Websocket Latency",
            value=f"**`{round(latency_ms, 3)}ms{' ' * (9 - len(str(round(latency_ms, 3))))}`**",
            inline=False,
        )
        embed.add_field(
            name="Typing Latency",
            value=f"**`{round(typing_ms, 3)}ms{' ' * (9 - len(str(round(typing_ms, 3))))}`**",
            inline=False,
        )
        embed.add_field(
            name="Database Latency",
            value=f"**`{round(postgres_ms, 3)}ms{' ' * (9 - len(str(round(postgres_ms, 3))))}`**",
            inline=False,
        )

        return await ctx.reply(embed=embed)

    @commands.hybrid_command(name="source", help="Returns command's source.", with_app_command=True)
    async def source(self, ctx: DwelloContext, *, command_name: Optional[str]) -> Optional[discord.Message]:
        git = cs.GITHUB
        if not command_name:
            return await ctx.reply(git)

        bot_name: str = self.bot.user.name.lower()
        bot_guild_name: str = self.bot.user.display_name.lower()
        _bot_guild_name: List[str] = bot_guild_name.split()
        _bot_name: List[str] = bot_name.split()

        _base_words: List[str] = [
            "base",
            "bot",
            bot_name,
            _bot_name[0],
            f"{bot_name} base",
            f"{_bot_name[0]} base",
        ]
        _matches: List[str] = _base_words.copy()
        _command_name: str = command_name.lower()

        if bot_guild_name != bot_name:
            _matches.append(bot_guild_name)
            if _bot_guild_name[0] != _bot_name[0]:
                _matches.append(_bot_guild_name[0])

        for command in self.bot.walk_commands():
            _matches.append(command.qualified_name.lower())

        for cog in self.bot.cogs.values():
            if cog.qualified_name == "Jishaku":
                continue
            _matches.append(cog.qualified_name.lower())

        # ADD A CHECK FOR BOT.PY TO DISPLAY WHOLE FILE

        if _command_name == "help":
            target = type(self.bot.help_command)

        elif _command_name in ["context", "ctx"]:
            target = ctx.__class__

        elif _command_name in _base_words:
            target = self.bot.__class__.__base__

        else:
            command = self.bot.get_command(command_name)
            cog = self.bot.get_cog(command_name)

            if not command and not cog:
                matches = difflib.get_close_matches(command_name, _matches, 5)
                if not matches:
                    return await ctx.reply("That command doesn't exist!")

                description = "Perhaps you meant one of these:"
                for match in matches:
                    description += f"\n• `{match}`"

                embed: discord.Embed = discord.Embed(
                    title=f"Doesn't seem like command `{command_name}` exists",
                    description=f"\n{description}",
                    color=cs.WARNING_COLOR,
                )
                return await ctx.reply(embed=embed)
            if command:
                target = command.callback
            if cog:
                target = type(cog)

        source: str = inspect.getsource(target)
        file: str = inspect.getsourcefile(target)
        lines: Tuple[List[str], int] = inspect.getsourcelines(target)
        git_lines = f"#L{lines[1]}-L{len(lines[0])+lines[1]}"
        path = os.path.relpath(file)

        source_link = f"> [**Source**]({git}tree/main/{path}{git_lines}) {cs.GITHUB_EMOJI}\n> **{path}{git_lines}**\n"

        embed: discord.Embed = discord.Embed(
            title=f"Source for `{command_name}`",
            description=(source_link + await ctx.create_codeblock(source)),
        )
        try:
            return await ctx.reply(embed=embed)

        except discord.errors.HTTPException:
            embed.description = source_link
            return await ctx.reply(embed=embed)


# SOME USELESS PIECE OF SHIT
class ManualHelp:
    def __init__(self, bot: Dwello = None):
        self.bot = bot
        self.ignored_cogs = ["CommandErrorHandler", "Other", "Jishaku"]

    def get_bot_cog_structure_as_dict(
        self,
    ) -> Dict[str, Dict[str, Union[None, str, Dict[str, Union[None, str]]]]]:
        """Retrieves the bot cog-structure in a dictionary form."""

        structure = {}

        for name, cog in self.bot.cogs.items():
            if name in self.ignored_cogs:
                continue

            cog_structure = {}
            comm_list = cog.get_commands()

            for command in comm_list:
                if isinstance(command, commands.Group):
                    group_structure = {}

                    for group_command in command.commands:
                        if isinstance(group_command, commands.Group):
                            subgroup_structure = {
                                subgroup_command.name: subgroup_command.help for subgroup_command in group_command.commands
                            }
                            group_structure[group_command.name] = subgroup_structure

                        else:
                            group_structure[group_command.name] = group_command.help

                    cog_structure[command.name] = group_structure

                else:
                    cog_structure[command.name] = command.help

            structure[name] = cog_structure

        return structure

    def print_cog_structure(self, structure: dict) -> str:
        """Outdated. You can use it to print the full cog-structure returned by get_bot_cog_structure_as_dict()."""

        structure_text = "{"
        for cog_name, cog in structure.items():
            structure_text += f"\n\t'{cog_name}': {{"
            if isinstance(cog, dict):
                for command, substructure in cog.items():
                    if isinstance(substructure, dict):
                        structure_text += f"\n\t\t'{command} (group)': {{"
                        for group_name, subgroup in substructure.items():
                            if isinstance(subgroup, dict):
                                structure_text += f"\n\t\t\t'{group_name} (subgroup)': {{"
                                for subgroup_name, subgroup_help in subgroup.items():
                                    structure_text += f"\n\t\t\t\t'{subgroup_name} (command)': '{subgroup_help}',"
                                structure_text += "\n\t\t\t}"
                            else:
                                structure_text += f"\n\t\t\t'{group_name} (command)': '{subgroup}',"
                        structure_text += "\n\t\t}"
                    else:
                        structure_text += f"\n\t\t'{command} (command)': '{substructure}',"
            else:
                structure_text += f"\n\t'{cog_name}': '{cog}',"
            structure_text += "\n\t}"
        structure_text += "\n}"
        return structure_text

    def get_command_hierarchy(self, command: Union[commands.Group, commands.Command]) -> str:
        """Returns the hierarchical representation of a command or command group."""

        return (
            f"{command.name} {self.get_command_hierarchy(command.all_commands[list(command.all_commands.keys())[0]])}"
            if isinstance(command, commands.Group)
            else command.name
        )

    def leo_bot_mapping(self):
        bot = self.context.bot
        ignored_cogs = [
            "CommandErrorHandler",
            "Jishaku",
            "Other",
        ]
        return {
            cog: cog.get_commands()
            for cog in sorted(
                bot.cogs.values(),
                key=lambda c: len(c.get_commands()),
                reverse=True,
            )
            if cog.qualified_name not in ignored_cogs
        }

    def new_bot_mapping(self) -> Dict[commands.Cog, List[commands.Command]]:
        """Retrieves full bot mapping that includes every (user-) available command: all command/parent groups are unpacked."""  # noqa: E501

        bot = self.bot
        mapping = {}

        for cog in sorted(bot.cogs.values(), key=lambda c: len(c.get_commands()), reverse=True):
            if cog.qualified_name in self.ignored_cogs:
                continue

            commands_list: List[commands.Command] = []
            for command in cog.walk_commands():
                if isinstance(command, commands.Group):
                    subcommands = command.commands
                    while (
                        isinstance(subcommands, list)
                        and len(subcommands) == 1
                        and isinstance(subcommands[0], commands.Group)
                    ):
                        subcommands = subcommands[0].commands

                    if isinstance(subcommands, list):
                        commands_list.extend(subcommands)
                    elif isinstance(subcommands, commands.Command):
                        commands_list.append(subcommands)
                else:
                    commands_list.append(command)

            mapping[cog] = commands_list

        return mapping
