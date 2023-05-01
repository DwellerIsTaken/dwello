from __future__ import annotations

import difflib
import itertools
import traceback

from discord.ext import commands
from discord import Interaction
from discord.ui import select, Select, button
import discord

from typing import (Optional, 
                    Union, 
                    Any, 
                    List, 
                    Dict
                )

from utils import BaseCog, CustomContext
import text_variables as tv

newline = "\n"

'''async def setup(bot: commands.Bot):
    await bot.add_cog(About(bot))'''

class HelpCentre(discord.ui.View):
    def __init__(
        self, 
        bot: commands.Bot,
        ctx: CustomContext, 
        other_view: discord.ui.View
    ):
        super().__init__()
        self.embed = None
        self.ctx = ctx
        self.bot: commands.Bot = bot
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
            color=tv.color,
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
        '''self.add_item(
            discord.ui.Button(
                label="Invite Me",
                url=discord.utils.oauth_url(
                    self.bot.user.id,
                    permissions=discord.Permissions(294171045078),
                    scopes=("applications.commands", "bot"),
                ),
            )
        )''' # Later
        await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user and interaction.user == self.ctx.author:
            return True
        await interaction.response.defer()
        return False

class HelpView(discord.ui.View):

    def __init__(
        self,
        ctx: CustomContext,
        data: Dict[commands.Cog, List[commands.Command]], 
        help_command: commands.HelpCommand,
    ):
        super().__init__()
        self.ctx = ctx
        self.bot: commands.Bot = self.ctx.bot
        self.data = data
        self.current_page = 0
        self.help_command = help_command
        self.message: discord.Message = None
        self.main_embed = self.build_main_page()
        self.embeds: List[discord.Embed] = [self.main_embed]

    @select(placeholder="Select a category", row=0)
    async def category_select(self, interaction: Interaction, select: Select):
        if select.values[0] == "index":
            self.current_page = 0
            self.embeds = [self.main_embed]
            self._update_buttons()
            return await interaction.response.edit_message(embed=self.main_embed, view=self)
        
        cog = self.bot.get_cog(select.values[0])
        if not cog:
            return await interaction.response.send_message("Somehow, that category was not found? 🤔", ephemeral=True)
        
        else:
            self.embeds = self.build_embeds(cog)
            self.current_page = 0
            self._update_buttons()
            return await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    def build_embeds(self, cog: commands.Cog) -> List[discord.Embed]:
        embeds = []
        #comm = cog.get_commands()

        for cog_, comm in self.data.items():
            if cog_ != cog:
                continue

            embed = discord.Embed(
                title=f"{cog.qualified_name} commands [{len(comm)}]",
                color=tv.color,
                description=cog.description or "No description provided",
            )

            for cmd in comm:     
                if cmd.extras.get("nsfw", False):
                    embed.add_field(
                        name=f"{cmd.name}",
                        value="See help for this command in an NSFW channel.",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name=f"`{cmd.name}{f' {cmd.signature}`' if cmd.signature else '`'}",
                        value=(("> " + (cmd.brief or cmd.help or "No help given...")) + (f"\n> Parent: `{cmd.parent}`" if cmd.parent else ""))[0:1024], # .replace("%PRE%", self.ctx.clean_prefix)
                        inline=False,
                    )
                embed.set_footer(text='For more info on a command run "help [command]"')
                if len(embed.fields) == 5:
                    embeds.append(embed)
                    embed = discord.Embed(
                        title=f"{cog.qualified_name} commands [{len(comm)}]",
                        color=tv.color,
                        description= (cog.description or "No description provided"),
                    )
            if len(embed.fields) > 0:
                embeds.append(embed)

            return embeds

    def build_select(self) -> None:
        self.category_select.options = []
        self.category_select.add_option(label="Main Page", value="index", emoji="🏠")
        for cog, comm in self.data.items():
            if not comm:
                continue
            emoji = getattr(cog, "select_emoji", None)
            label = cog.qualified_name + f" ({len(comm)})"
            brief = getattr(cog, "select_brief", None)
            self.category_select.add_option(label=label, value=cog.qualified_name, emoji=emoji, description=brief)

    def build_main_page(self) -> discord.Embed:
        embed = discord.Embed(
            color=tv.color,
            title="Dwello Help Menu",
            description="Hello, I'm Dwello! I'm still in development, but you can use me.",
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
            f"\nsupport server: **__<https://discord.gg/8FKNF8pC9u>__**"
            "\n📨 You can also DM me for help if you prefer to,"
            "\nbut please join the support server for suggestions.",
        )
        embed.add_field(
            name="Who Am I?",
            inline=False,
            value=f"I'm Dwello, a multipurpose discordbot. You can use me to play games, moderate "
            f"\nyour server, mess with some images and more! Check out "
            f"\nall my features using the dropdown below.",
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
        view = HelpCentre(self.bot, self.ctx, self)
        await view.start(interaction)

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

    @button(label=">", row=1) # emoji
    async def next(self, interaction: Interaction, _):
        self.current_page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    """@discord.ui.button(emoji="📰", label="news", row=1, style=discord.ButtonStyle.green)
    async def vote(self, interaction: Interaction, _):
        view = NewsMenu(self.ctx, other_view=self)
        await view.start(interaction)"""

    def _update_buttons(self) -> None:
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

    async def on_timeout(self) -> None:
        self.clear_items()
        await self.message.edit(view=self)

    async def start(self) -> Optional[discord.Message]:
        self.build_select()
        self._update_buttons()
        self.message = await self.ctx.send(embed=self.main_embed, view=self)

class MyHelp(commands.HelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.context: CustomContext = None

    def get_bot_mapping(self):
        """Retrieves the bot mapping passed to :meth:`send_bot_help`."""
        bot = self.context.bot
        ignored_cogs = [
            "CommandErrorHandler", 
            "Other", "Jishaku",
        ]
        
        mapping = {}
            
        for cog in sorted(bot.cogs.values(), key=lambda c: len(c.get_commands()), reverse=True):
            if cog.qualified_name in ignored_cogs:
                continue
            
            commands_list: List[commands.Command] = []
            for command in cog.walk_commands():
                if isinstance(command, commands.Group):
                    subcommands = command.commands
                    while isinstance(subcommands, list) and len(subcommands) == 1 and isinstance(subcommands[0], commands.Group):
                        subcommands = subcommands[0].commands
                    
                    if isinstance(subcommands, list):
                        commands_list.extend(subcommands)
                    elif isinstance(subcommands, commands.Command):
                        commands_list.append(subcommands)
                else:
                    commands_list.append(command)
            
            mapping[cog] = commands_list
        
        return mapping

    def get_minimal_command_signature(self, command):
        if isinstance(command, commands.Group):
            return "[G] %s%s %s" % (
                self.context.clean_prefix,
                command.qualified_name,
                command.signature,
            )
        return "(c) %s%s %s" % (
            self.context.clean_prefix,
            command.qualified_name,
            command.signature,
        )

    # !help
    async def send_bot_help(self, mapping):
        view = HelpView(self.context, data=mapping, help_command=self)
        await view.start()

    # !help <command>
    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(
            title=f"information about: `{self.context.clean_prefix}{command}`",
            description="**Description:**\n"
            + (command.help or "No help given...").replace("%PRE%", self.context.clean_prefix),
        )
        embed.add_field(
            name="Command usage:",
            value=f"```css\n{self.get_minimal_command_signature(command)}\n```",
        )
        try:
            preview = command.__original_kwargs__["preview"]
            embed.set_image(url=preview)
        except KeyError:
            pass
        if command.aliases:
            embed.description = embed.description + f'\n\n**Aliases:**\n`{"`, `".join(command.aliases)}`'
        try:
            await command.can_run(self.context)
        except BaseException as e:
            try:
                if isinstance(e, discord.ext.commands.CheckAnyFailure):
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

    async def send_cog_help(self, cog):
        entries = cog.get_commands()
        if entries:
            data = [self.get_minimal_command_signature(entry) for entry in entries]
            embed = discord.Embed(
                title=f"{getattr(cog, 'select_emoji', '')} `{cog.qualified_name}` category commands",
                description="**Description:**\n" + cog.description.replace("%PRE%", self.context.clean_prefix),
            )
            embed.description = (
                embed.description + f"\n\n**Commands:**\n```css\n{newline.join(data)}\n```"
                f"\n`[G]` means group, these have sub-commands."
                f"\n`(C)` means command, these do not have sub-commands."
            )
            await self.context.send(embed=embed)
        else:
            await self.context.send(f"No commands found in {cog.qualified_name}")

    async def send_group_help(self, group):
        embed = discord.Embed(
            title=f"information about: `{self.context.clean_prefix}{group}`",
            description="**Description:**\n"
            + (group.help or "No help given...").replace("%PRE%", self.context.clean_prefix),
        )
        embed.add_field(
            name="Command usage:",
            value=f"```css\n{self.get_minimal_command_signature(group)}\n```",
        )
        if group.aliases:
            embed.description = embed.description + f'\n\n**Aliases:**\n`{"`, `".join(group.aliases)}`'
        if group.commands:
            formatted = "\n".join([self.get_minimal_command_signature(c) for c in group.commands])
            embed.add_field(
                name="Sub-commands for this command:",
                value=f"```css\n{formatted}\n```\n**Do `{self.context.clean_prefix}help command subcommand` for more info on a sub-command**",
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

    def command_not_found(self, string):
        return string

    def subcommand_not_found(self, command, string):
        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            return command.qualified_name + string
        return command.qualified_name

    async def send_error_message(self, error):
        matches = difflib.get_close_matches(error, self.context.bot.cogs.keys())
        if matches:
            confirm = await self.context.confirm(
                message=f"Sorry but i couldn't recognise {error} as one of my categories!"
                f"\n{f'**did you mean... `{matches[0]}`?**' if matches else ''}",
                delete_after_confirm=True,
                delete_after_timeout=True,
                delete_after_cancel=True,
                buttons=(
                    ("✅", f"See {matches[0]}"[0:80], discord.ButtonStyle.blurple),
                    ("🗑", None, discord.ButtonStyle.red),
                ),
                timeout=15,
            )
            if confirm is True:
                return await self.send_cog_help(self.context.bot.cogs[matches[0]])
            return
        else:
            command_names = []
            for command in [c for c in self.context.bot.commands]:
                # noinspection PyBroadException
                try:
                    if await command.can_run(self.context):
                        command_names.append([command.name] + command.aliases)
                except:
                    continue
            command_names = list(itertools.chain.from_iterable(command_names))
            matches = difflib.get_close_matches(error, command_names)
            if matches:
                confirm = await self.context.confirm(
                    message=f"Sorry but i couldn't recognise {error} as one of my commands!"
                    f"\n{f'**did you mean... `{matches[0]}`?**' if matches else ''}",
                    delete_after_confirm=True,
                    delete_after_timeout=True,
                    delete_after_cancel=True,
                    buttons=(
                        ("✅", f"See {matches[0]}"[0:80], discord.ButtonStyle.blurple),
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

    async def on_help_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(embed=discord.Embed(title=str(error.original),description=''.join(traceback.format_exception(error.__class__, error, error.__traceback__))))

class About(BaseCog):

    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        
        help_command = MyHelp()
        help_command.command_attrs = {
            "help": "Shows help about a command or category, it can also display other useful information, such as "
            "examples on how to use the command, or special syntax that can be used for a command, for example, "
            "in the `welcome message` command, it shows all available special tags.",
            "name": "help",
        }
        help_command.cog = self
        bot.help_command = help_command
        self.select_emoji = '<:info:895407958035431434>'
        self.select_brief = "Bot Information commands."

'''class About(commands.Cog):
    """
    😮 Commands related to the bot itself, that have the only purpose to show information.
    """

    def __init__(self, bot):
        #self.bot: commands.Bot = bot
        
        help_command = MyHelp()
        help_command.command_attrs = {
            "help": "Shows help about a command or category, it can also display other useful information, such as "
            "examples on how to use the command, or special syntax that can be used for a command, for example, "
            "in the `welcome message` command, it shows all available special tags.",
            "name": "help",
        }
        help_command.cog = self
        bot.help_command = help_command
        self.select_emoji = '<:info:895407958035431434>'
        self.select_brief = "Bot Information commands."'''

class ManualHelp:

    def __init__(self, bot: commands.Bot = None):
        self.bot: commands.Bot = bot
        self.ignored_cogs = ['CommandErrorHandler', 'Other', 'Jishaku']

    def get_bot_cog_structure_as_dict(self) -> Dict[str, Dict[str, Union[None, str, Dict[str, Union[None, str]]]]]:
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
                            subgroup_structure = {}

                            for subgroup_command in group_command.commands:
                                subgroup_structure[subgroup_command.name] = subgroup_command.help

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

        if isinstance(command, commands.Group):
            hierarchy = f"{command.name} {self.get_command_hierarchy(command.all_commands[list(command.all_commands.keys())[0]])}"

        else:
            hierarchy = command.name

        return hierarchy
    
    def leo_bot_mapping(self):

        bot = self.context.bot
        ignored_cogs = [
            "CommandErrorHandler", 
            "Jishaku",
            "Other", 
        ]
        mapping = {
            cog: cog.get_commands()
            for cog in sorted(bot.cogs.values(), key=lambda c: len(c.get_commands()), reverse=True)
            if cog.qualified_name not in ignored_cogs
        }
        return mapping

    def new_bot_mapping(self) -> Dict[commands.Cog, List[commands.Command]]:
        """Retrieves full bot mapping that includes every (user-) available command: all command/parent groups are unpacked."""

        bot = self.bot
        mapping = {}
            
        for cog in sorted(bot.cogs.values(), key=lambda c: len(c.get_commands()), reverse=True):
            if cog.qualified_name in self.ignored_cogs:
                continue
            
            commands_list: List[commands.Command] = []
            for command in cog.walk_commands():
                if isinstance(command, commands.Group):
                    subcommands = command.commands
                    while isinstance(subcommands, list) and len(subcommands) == 1 and isinstance(subcommands[0], commands.Group):
                        subcommands = subcommands[0].commands
                    
                    if isinstance(subcommands, list):
                        commands_list.extend(subcommands)
                    elif isinstance(subcommands, commands.Command):
                        commands_list.append(subcommands)
                else:
                    commands_list.append(command)
            
            mapping[cog] = commands_list
        
        return mapping