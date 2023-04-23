from __future__ import annotations

from discord.ext import commands
import discord

from typing import Optional, Any, List, Dict

from utils import BaseCog
import text_variables as tv

class HelpView(discord.ui.View):

    def __init__(
        self,
        bot: commands.Bot,
        data,
        ctx: commands.Context,
    ):
        super().__init__()
        self.ctx = ctx
        self.data = data
        self.current_page = 0
        self.bot: commands.Bot = bot
        self.main_embed = self.build_main_page()
        self.category_select.add_option(label="Main Page", value="index", emoji="🏠")
        '''self.data = data
        self.help_command = help_command
        self.message: discord.Message = None
        self.embeds: List[discord.Embed] = [self.main_embed]'''

    @discord.ui.select(placeholder="Select a category", row=0)
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "index":
            '''self.current_page = 0
            self.embeds = [self.main_embed]
            self._update_buttons()'''
            return await interaction.response.edit_message(embed=self.main_embed, view=self)
        
        '''elif select.values[0] == "old_help_command":
            await self.old_help(self.data)
            self.stop()
            return
        cog = self.bot.get_cog(select.values[0])
        if not cog:
            return await interaction.response.send_message("Somehow, that category was not found? 🤔", ephemeral=True)
        else:
            self.embeds = self.build_embeds(cog)
            self.current_page = 0
            self._update_buttons()
            return await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)'''

    '''def build_embeds(self, cog: commands.Cog) -> List[discord.Embed]:
        embeds = []
        comm = cog.get_commands()
        embed = discord.Embed(
            title=f"{cog.qualified_name} commands [{len(comm)}]",
            color=self.ctx.color,
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
                    name=f"{constants.ARROW}`{cmd.name}{f' {cmd.signature}`' if cmd.signature else '`'}",
                    value=(cmd.brief or cmd.help or "No help given...").replace("%PRE%", self.ctx.clean_prefix)[0:1024],
                    inline=False,
                )
            embed.set_footer(text='For more info on a command run "help [command]"')
            if len(embed.fields) == 5:
                embeds.append(embed)
                embed = discord.Embed(
                    title=f"{cog.qualified_name} commands [{len(comm)}]",
                    color=self.ctx.color,
                    description=cog.description or "No description provided",
                )
        if len(embed.fields) > 0:
            embeds.append(embed)
        return embeds'''

    '''def build_select(self) -> None:
        self.category_select.options = []
        self.category_select.add_option(label="Main Page", value="index", emoji="🏠")
        for cog, comm in self.data.items():
            if not comm:
                continue
            emoji = getattr(cog, "select_emoji", None)
            label = cog.qualified_name + f" ({len(comm)})"
            brief = getattr(cog, "select_brief", None)
            self.category_select.add_option(label=label, value=cog.qualified_name, emoji=emoji, description=brief)
        self.category_select.add_option(
            label="Browse Old Help Command",
            value="old_help_command",
            emoji="💀",
            description="Not recommended, but still available.",
        )'''

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

    async def start(self):
        self.message = await self.ctx.send(embed=self.main_embed, view=self)

    '''@discord.ui.button(emoji="❓", label="help", row=1, style=discord.ButtonStyle.green)
    async def help(self, interaction: Interaction, _):
        view = HelpCentre(self.ctx, self)
        await view.start(interaction)

    @discord.ui.button(emoji=constants.ARROWBACKZ, row=1)
    async def previous(self, interaction: Interaction, _):
        self.current_page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(emoji="🗑", row=1, style=discord.ButtonStyle.red)
    async def _end(self, interaction: Interaction, _):
        await interaction.message.delete(delay=0)
        if self.ctx.channel.permissions_for(self.ctx.me).add_reactions:
            await self.ctx.message.add_reaction(random.choice(constants.DONE))

    @discord.ui.button(emoji=constants.ARROWFWDZ, row=1)
    async def next(self, interaction: Interaction, _):
        self.current_page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(emoji="📰", label="news", row=1, style=discord.ButtonStyle.green)
    async def vote(self, interaction: Interaction, _):
        view = NewsMenu(self.ctx, other_view=self)
        await view.start(interaction)

    def _update_buttons(self):
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

    async def start(self):
        self.build_select()
        self._update_buttons()
        self.message = await self.ctx.send(embed=self.main_embed, view=self, footer=False)'''

class MyHelp(BaseCog):

    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)

    @commands.hybrid_command(name='help', help='', with_app_command=True)
    async def help_command(self, ctx: commands.Context) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):

            embed = discord.Embed(title="Help Centere", description="Bruh")
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url)

            structure = {}
            forbidden = ['CommandErrorHandler', 'Other', 'Jishaku']

            for name, cog in self.bot.cogs.items():
                if name in forbidden:
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
                #await ctx.send(embed=discord.Embed(description=f"```{cog_structure}```"))

            view: HelpView = HelpView(bot=self.bot, data=structure, ctx=ctx)
            await view.start()
            self.print_cog_structure(structure)

    def print_cog_structure(self, structure: dict) -> str:
        structure_text = ""
        for cog_name, cog in structure.items():
            structure_text += f"{cog_name}:\n"
            for command, substructure in cog.items():
                structure_text += f"|  {command}:\n"
                if isinstance(substructure, dict):
                    for group_name, subgroup in substructure.items():
                        structure_text += f"|  |  {group_name}:\n"
                        if isinstance(subgroup, dict):
                            for subgroup_name, subgroup_help in subgroup.items():
                                structure_text += f"|  |  |  {subgroup_name} - {subgroup_help}\n"
                        else:
                            structure_text += f"|  |  |  {subgroup}\n"
                else:
                    structure_text += f"|  |  {substructure}\n"

        print(structure_text)