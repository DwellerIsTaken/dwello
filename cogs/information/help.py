from __future__ import annotations

from discord.ext import commands
from discord import Interaction
from discord.ui import select, Select, button
import discord

from typing import Optional, Union, Any, List, Dict

from utils import BaseCog
import text_variables as tv

class HelpCentre(discord.ui.View):
    def __init__(
        self, 
        bot: commands.Bot,
        ctx: commands.Context, 
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
            value="Means that this argument is __**required**__ and can take __**multiple entries**__"
            "\nFor example: db.mass-mute @user1 @user2 @user3",
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
        self.add_item(discord.ui.Button(label="Support Server", url="https://discord.gg/TdRfGKg8Wh"))
        self.add_item(
            discord.ui.Button(
                label="Invite Me",
                url=discord.utils.oauth_url(
                    self.bot.user.id,
                    permissions=discord.Permissions(294171045078),
                    scopes=("applications.commands", "bot"),
                ),
            )
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user and interaction.user == self.ctx.author:
            return True
        await interaction.response.defer()
        return False

class HelpView(discord.ui.View): # Dict[str, Dict[str, Union[None, str, Dict[str, Union[None, str]]]]]

    def __init__(
        self,
        bot: commands.Bot,
        ctx: commands.Context,
        data: Dict[commands.Cog, List[commands.Command]], 
        help_command: commands.HelpCommand,
    ):
        super().__init__()
        self.ctx = ctx
        self.data = data
        self.current_page = 0
        self.bot: commands.Bot = bot
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
        comm = cog.get_commands()
        embed = discord.Embed(
            title=f"{cog.qualified_name} commands [{len(comm)}]",
            color=tv.color,
            description=cog.description or "No description provided",
        )
        for cog_, comm in self.data.items():
            if cog_ != cog:
                continue

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
            title="DuckBot Help Menu",
            description="Hello, I'm DuckBot! A multi-purpose bot with a lot of features.",
        )
        embed.add_field(
            name="Getting Help",
            inline=False,
            value="Use `db.help <command>` for more info on a command."
            "\nThere is also `db.help <command> [subcommand]`."
            "\nUse `db.help <category>` for more info on a category."
            "\nYou can also use the menu below to view a category.",
        )
        embed.add_field(
            name="Getting Support",
            inline=False,
            value="To get help or __**suggest features**__, you can join my"
            f"\nsupport server: **__<https://discord.gg/TdRfGKg8Wh>__**"
            "\n📨 You can also DM me for help if you prefer to,"
            "\nbut please join the support server for suggestions.",
        )
        embed.add_field(
            name="Who Am I?",
            inline=False,
            value=f"I'm DuckBot, a multipurpose bot created and maintained "
            f"leoCx1000). You can use me to play games, moderate "
            f"\nyour server, mess with some images and more! Check out "
            f"\nall my features using the dropdown below.",
        )
        embed.add_field(
            name="Support DuckBot",
            value="None",
            inline=False,
        )
        embed.set_footer(
            text="For more info on the help command press ❓help",
            icon_url="https://cdn.discordapp.com/emojis/895407958035431434.png",
        )
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url)
        return embed

    @button(emoji="❓", label="help", row=1, style=discord.ButtonStyle.green)
    async def help(self, interaction: Interaction, _):
        view = HelpCentre(self.ctx, self)
        await view.start(interaction)

    @button(label="<", row=1)
    async def previous(self, interaction: Interaction, _):
        self.current_page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @button(emoji="🗑", row=1, style=discord.ButtonStyle.red)
    async def _end(self, interaction: Interaction, _):
        await interaction.message.delete(delay=0)
        '''if self.ctx.channel.permissions_for(self.ctx.me).add_reactions:
            await self.ctx.message.add_reaction(random.choice(constants.DONE))'''

    @button(label=">", row=1) # emoji
    async def next(self, interaction: Interaction, _):
        self.current_page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    '''@discord.ui.button(emoji="📰", label="news", row=1, style=discord.ButtonStyle.green)
    async def vote(self, interaction: Interaction, _):
        view = NewsMenu(self.ctx, other_view=self)
        await view.start(interaction)'''

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

    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.bot: commands.Bot = bot
        self.ctx: commands.Context = None
        self.ignored_cogs = ['CommandErrorHandler', 'Other', 'Jishaku']

    def leo_bot_mapping(self):
        """Retrieves the bot mapping passed to :meth:`send_bot_help`."""

        bot = self.bot
        mapping = {
            cog: cog.get_commands()
            for cog in sorted(bot.cogs.values(), key=lambda c: len(c.get_commands()), reverse=True)
            if cog.qualified_name not in self.ignored_cogs
        }
        return mapping

    def get_command_hierarchy(self, command: Union[commands.Group, commands.Command]) -> str:
        """Returns the hierarchical representation of a command or command group."""

        if isinstance(command, commands.Group):
            hierarchy = f"{command.name} {self.get_command_hierarchy(command.all_commands[list(command.all_commands.keys())[0]])}"

        else:
            hierarchy = command.name

        return hierarchy

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
    
    async def send_bot_help(self, mapping):
        view: HelpView = HelpView(self.bot, self.context, data=mapping, help_command=self)
        await view.start()

class About(commands.Cog):
    """
    😮 Commands related to the bot itself, that have the only purpose to show information.
    """

    def __init__(self, bot):
        self.bot: commands.Bot = bot
        help_command = MyHelp(self.bot)
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

    @commands.hybrid_command(name='help', help='', with_app_command=True)
    async def help_cmd(self, ctx: commands.Context) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):

            embed = discord.Embed(title="Help Centere", description="Bruh")
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url)

            '''mapping = help_command.new_bot_mapping()
            for cog, comm in mapping.items():
                print(cog.qualified_name, len(comm), ":\n")
                for command in comm:
                    print("Command:", command, "Parent:", command.parent)
                print("\n")

            await commands.HelpCommand.send_bot_help(mapping)'''

async def setup(bot: commands.Bot):
    await bot.add_cog(About(bot))