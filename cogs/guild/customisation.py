from __future__ import annotations

from typing import Any, Literal, TypeVar

import discord
import contextlib

from discord import Interaction, ButtonStyle, TextStyle
from discord.app_commands import Choice
from discord.ext import commands

from constants import USER_CONFIG_DICT, OPTION_SELECT_VALUES, GUILD_CONFIG_DICT
from core import Context, Dwello, Embed
from utils import Prefix, DefaultPaginator, Guild, User

CPT = TypeVar("CPT", bound="ConfigPaginator")

Item = discord.ui.Item
Modal = discord.ui.Modal
Select = discord.ui.Select
Button = discord.ui.Button
TextInput = discord.ui.TextInput
_Interaction = Interaction[Dwello]


async def setup(bot: Dwello) -> None:
    await bot.add_cog(Customisation(bot))

async def _config(
        obj: Context | _Interaction, what_config_to_trigger: Literal["guild", "user", "both"] = "both",
) -> ConfigPaginator:
    guild, author = obj.guild, obj.author if isinstance(obj, Context) else obj.user

    match what_config_to_trigger: # ugly but meh
        case "guild":
            if (
                (owner_id := obj.guild.owner_id)
                and author.id == owner_id
            ) or author.guild_permissions.administrator:
                return await ConfigPaginator.start(obj)
            else:
                raise commands.MissingPermissions(['administrator'])
        case "both":
            if not guild:
                return await ConfigPaginator.start(obj, 2)
            else:
                if (
                    (owner_id := guild.owner_id)
                    and author.id == owner_id
                ) or author.guild_permissions.administrator:
                    return await ConfigPaginator.start(obj)
                else:
                    return await ConfigPaginator.start(obj, 2)
        case "user":
            return await ConfigPaginator.start(obj, 2)
        

class Customisation(commands.Cog):
    """
    🖌️
    Lots of amazing commands that can be used to customise your guild and the output of bot's commands and a lot more.
    """

    def __init__(self, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.db = bot.db

        self.select_emoji = "\N{ARTIST PALETTE}"
        self.select_brief = "Guild Customisation commands."

    async def _set_prefix(self, ctx: Context, _prefix: str) -> discord.Message | None:
        if not isinstance(prefix := await self.db.add_prefix(ctx.guild, _prefix, context=ctx), Prefix):
            return
        try:
            self.bot.guild_prefixes[ctx.guild.id].append(prefix)
        except KeyError:
            self.bot.guild_prefixes[ctx.guild.id] = [prefix]
        return await ctx.reply(embed=Embed(description=f"The prefix is set to `{prefix}`"), permission_cmd=True)

    async def _display_prefixes(self, ctx: Context) -> discord.Message | None:
        prefixes: list[str] = [f"<@!{self.bot.user.id}>"] + self.bot.DEFAULT_PREFIXES
        extra: list[Prefix] = await self.db.get_prefixes(ctx.guild)

        embed: Embed = Embed(
            title="Current prefixes",
            description="\n".join(str(prefix) for prefix in prefixes + extra),
        )
        return await ctx.reply(embed=embed, mention_author=False, ephemeral=False)

    async def _remove_prefix(self, ctx: Context, prefix: str | Literal["all"]) -> discord.Message | None:
        if not (await self.db.get_prefixes(ctx.guild)):
            return await ctx.reply(
                "Prefix isn't yet set. \n```/prefix add [prefix]```",
                user_mistake=True,
            )
        count = len(await self.db.remove_prefix(prefix, ctx.guild, all=prefix == "all"))
        self.bot.guild_prefixes[ctx.guild.id].remove(prefix)
        return await ctx.reply(
            embed=Embed(
                description=f"{'Prefix has' if count == 1 else f'{count} prefixes have'} been removed.",
            ),
            permission_cmd=True,
        )

    async def cog_check(self, ctx: Context) -> bool:
        if ctx.command.qualified_name != "config": # so that user config would work
            return ctx.guild is not None
        return True
    
    # also app that says: triggers a config of your choice
    # then have two options: guild and user/me
    # then have further handling and pass that onto _config
    @commands.command(name="config", aliases=["configure"], brief="Customise your guild.")
    async def config(self, ctx: Context) -> ConfigPaginator:
        """
        Introducing an incredible command that empowers you to tailor your bot experience
        and efficiently manage your cherished guild. This command offers a multitude of configuration options that you
        can toggle on or off, allowing you to select additional attributes for each option.
        For instance, you can activate the anti-spam feature, which automatically bans members for spamming messages
        in non-excluded channels, as well as for engaging in mention spam and raids. You'll also have the ability
        to specify the maximum number of different mentions a member can include in their message
        before they trigger the ban threshold.
        """
        return await _config(ctx)
    
    @discord.app_commands.command(name="config", description="Triggers configuration menu of your choice.")
    async def app_config(self, interaction: _Interaction, menu: Literal["guild", "user/me"]) -> ConfigPaginator:
        if menu == "guild" and not interaction.guild:
            return await interaction.response.send_message("Sorry, but you have to be in a guild in order to do that.")
        return await _config(interaction, "user" if menu == "user/me" else "guild")

    @commands.hybrid_group(aliases=["prefixes"], invoke_without_command=True, with_app_command=True)
    async def prefix(self, ctx: Context):
        """
        Returns a list of available prefixes if no arguments are provided.
        This group basically allows you to add and remove prefixes for your guild.
        Meaning that you can set a custom prefix that could be used when triggering a command
        instead of using bot's default prefixes.
        """
        async with ctx.typing():
            return await self._display_prefixes(ctx)

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True)) # do with all db stuff
    @prefix.command(
        name="add",
        brief="Adds bot prefix to the guild.",
        description="Adds bot prefix to the guild.",
    )
    async def add_prefix(self, ctx: Context, *, prefix: str):
        """Adds a prefix to this guild. Prefix musn't be longer than ten characters."""
        
        if len(prefix.split()) > 1:
            return await ctx.reply("Prefix musn't contain whitespaces.", user_mistake=True)

        return await self._set_prefix(ctx, prefix)

    @prefix.command(name="display", brief="Displays all prefixes.", description="Displays all prefixes.")
    async def display_prefix(self, ctx: Context):
        """Displays all the available prefixes, including the default ones."""

        return await self._display_prefixes(ctx)

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @prefix.command(name="remove", brief="Removes guild's prefix(es).", description="Removes guild's prefix(es).")
    async def delete_prefix(self, ctx: Context, prefix: str):
        """
        Remove a prefix by passing it as an argument to this prefix command or
        just choose it from a dropdown menu with this slash command.
        """
        return await self._remove_prefix(ctx, prefix)

    @delete_prefix.autocomplete("prefix")
    async def autocomplete_callback_prefix(self, interaction: _Interaction, current: str):
        item = len(current)
        prefixes: list[Prefix] = await self.bot.db.get_prefixes(interaction.guild)
        choices: list[Choice[str]] = [Choice(name="all", value="all")] + [
            Choice(name=prefix, value=prefix)
            for prefix in prefixes
            if current.startswith(str(prefix).lower()[:item])
        ]
        return choices[:10]
    

class OptionSelect(Select):
    def __init__(self, _option: str, _options: dict[str, Any] = None) -> None:
        if not _options:
            _options = OPTION_SELECT_VALUES.get(_option)
        super().__init__(options=[discord.SelectOption(label=a, value=b) for a, b in _options.items()])
        # passing the string now ^ cause idk how to get the 'current' label
        # don't think its the best solution:
        # if you keep the dict 'clean' of other types - it's easy
        # if you add some other types it may break, cause it's turned
        # into string when splitting, so you may pass incorrect value to the db
        # which is not what we want
        self.reversed_dict = {str(v): k for k, v in _options.items()} # also not the most optimized solution
        self.option = _option

    async def callback(self, interaction: _Interaction) -> None:
        assert self.view is not None
        view: ConfigPaginator = self.view
        value = self.values[0]
        _reversed = self.reversed_dict.get(value)
        value = None if value == "None" else value
        view.updated_config[self.option] = value
        self.placeholder = _reversed
        return await interaction.response.edit_message(view=self.view)
        
class InputModal(Modal, title="Input Contents"):
    def __init__(
        self,
        parent: InputButton,
        *,
        style: TextStyle = TextStyle.short,
        placeholder: str = None,
        default: str = None,
        max_length: int = None,
    ) -> None:
        super().__init__()
        self.button = parent

        self.content: TextInput = TextInput(
            label="Content",
            required=True,
            max_length=max_length,
            placeholder=placeholder,
            default=default,
            style=style,
        )
        self.add_item(self.content)

    async def on_submit(self, interaction: _Interaction) -> None:
        self.view = self.button.view
        self.view.updated_config[self.button.sub] = self.content.value
        # do some checks maybe based on the type of content that should be input
        # pass that type, dict or whatever to modal to execute checks
        # if the value is incorrect send an ephemeral followup or smh
        # and don't submit any values or submit the default one
        # that all should be also captured in options dictionary

        self.button.disabled = True
        return await interaction.response.edit_message(view=self.view)


class PageModal(Modal, title="Input Page"):
    def __init__(self, parent: PageButton, **kwargs) -> None:
        super().__init__()
        self.view: ConfigPaginator = parent.view

        self.content: TextInput = TextInput(
            label="Page",
            max_length=2,
            required=True,
            style=TextStyle.paragraph,
            **kwargs,
        )
        self.add_item(self.content)

    async def on_submit(self, interaction: _Interaction) -> None:
        try:
            if p:=int(self.content.value):
                self.view.current_page = p-1 if p != 0 else 0
            embed = self.view.current_embed

        except ValueError:
            return await interaction.response.send_message("Sorry, but the page number must be an integer.", ephemeral=True)
        
        except IndexError:
            #padding: int = len(str(len(self.view.embeds))) + 1
            #{'': >{padding - len(str(i))}}
            return await interaction.response.send_message(
                embed=Embed(
                    title="Wrong Page",
                    description=(
                        "Sorry, but this page doesn't exist. Let me help you.\n\n" +
                        "\n".join([ # poor formatting
                            f"**{i}.**".ljust(7) + f"{embed.title}"
                            for i, embed in enumerate(self.view.embeds, 1)
                        ])
                    )
                ), ephemeral=True,
            )
        return await interaction.response.edit_message(embed=embed, view=self.view.current_view())
    

class PreviousPageButton(Button["ConfigPaginator"]):
    def __init__(self, **kwargs) -> None:
        super().__init__(label="<", **kwargs)

    async def callback(self, interaction: _Interaction):
        assert self.view is not None
        view: ConfigPaginator = self.view

        view.current_page -= 1
        view._update_buttons()
        await interaction.response.edit_message(embed=view.current_embed, view=view.current_view())


class NextPageButton(Button["ConfigPaginator"]):
    def __init__(self, **kwargs) -> None:
        super().__init__(label=">", **kwargs)

    async def callback(self, interaction: _Interaction):
        assert self.view is not None
        view: ConfigPaginator = self.view

        view.current_page += 1
        view._update_buttons()
        await interaction.response.edit_message(embed=view.current_embed, view=view.current_view())


class PageButton(Button["ConfigPaginator"]):
    def __init__(self, **kwargs) -> None:
        super().__init__(label="Go To Page", style=ButtonStyle.blurple, **kwargs)

    async def callback(self, interaction: _Interaction):
        assert self.view is not None
        await interaction.response.send_modal(PageModal(self))


class SubmitAllOptionsButton(Button["ConfigPaginator"]):
    def __init__(self, **kwargs) -> None:
        super().__init__(label="Submit", style=ButtonStyle.blurple, **kwargs)

    async def callback(self, interaction: _Interaction):
        assert self.view is not None
        view: ConfigPaginator = self.view

        if view.updated_config:
            await view.update_config(view.updated_config)
        view.clear_items()
        if len(view.embeds) > 1:
            view.add_item(view.previous)
            view.add_item(view.next)
            view.add_item(view.to_page)
        view.add_item(view.submit)
        view.submit.disabled = True

        await interaction.response.edit_message(view=view)


class EnableButton(Button["ConfigPaginator"]):
    def __init__(self, **kwargs) -> None:
        super().__init__(label="Enable", style=ButtonStyle.green, **kwargs)

    async def callback(self, interaction: _Interaction):
        assert self.view is not None
        view: ConfigPaginator = self.view

        view.updated_config[view.option] = True
        self.disabled = True
        disable: DisableButton = view.get_item_by_type(DisableButton)
        with contextlib.suppress(AttributeError):
            disable.disabled = False

        await interaction.response.edit_message(view=view)


class DisableButton(Button["ConfigPaginator"]):
    def __init__(self, **kwargs) -> None:
        super().__init__(label="Disable", style=ButtonStyle.red, **kwargs)

    async def callback(self, interaction: _Interaction):
        assert self.view is not None
        view: ConfigPaginator = self.view

        view.updated_config[view.option] = False
        self.disabled = True
        enable: EnableButton = view.get_item_by_type(EnableButton)
        with contextlib.suppress(AttributeError):
            enable.disabled = False

        await interaction.response.edit_message(view=view)
        # btw, if the option is a "counter_category_denied"
        # then you should create or delete category once
        # updated_config is submitted


class InputButton(Button["ConfigPaginator"]):
    def __init__(self, sub_option: str, *, label: str = "Input", **kwargs) -> None:
        super().__init__(label=label, style=ButtonStyle.blurple, **kwargs)
        self.sub = sub_option

    async def callback(self, interaction: _Interaction):
        assert self.view is not None
        view: ConfigPaginator = self.view
        default = view.get_config_option_by_type(self.sub)
        await interaction.response.send_modal(InputModal(self, placeholder="Input here", default=default))

# THIS IS CONFIG AFTER ALL
# also add like go to default button
# that ll update to default settings
class ConfigPaginator(DefaultPaginator):
    def __init__(self, obj: Context | _Interaction, _guild_or_user_num: Literal[1, 2] = 1,) -> None:
        self._dict_num = _guild_or_user_num
        options, embeds = self._construct_embeds_and_options()

        super().__init__(obj, embeds, values=options)

        self.updated_config: dict[str, Any] = {}

        # set in start() classmethod
        # both ORMs must have the same names for methods that are used in this paginator
        self.guild_or_user: Guild | User | None = None

        # so, the structure is like: config option -> embed & view
        # thus everything revolves (should) around the config option

        # and below we activate all the items (classes) in order to add them when needed
        # these are permanent thus saved into attributes

        self.next = NextPageButton()
        self.previous = PreviousPageButton()
        self.to_page = PageButton()
        self.submit = SubmitAllOptionsButton()

        self.view_items: list[tuple[Item]] | None = None # constructed in classmethod

    @property
    def option(self) -> str:
        return self.options[self.current_page]
    
    @property
    def options(self) -> list[str]:
        return self.values
    
    @property
    def guild(self) -> Guild | None:
        return self.guild_or_user if isinstance(self.guild_or_user, Guild) else None
    
    @property
    def user(self) -> User | None:
        return self.guild_or_user if isinstance(self.guild_or_user, User) else None
    
    @property
    def _dict(self) -> dict[Any, Any]:
        return {
            1: GUILD_CONFIG_DICT,
            2: USER_CONFIG_DICT,
        }.get(self._dict_num)
    
    # might be too slow
    # TODO maybe make it faster
    def current_view(self) -> ConfigPaginator:
        self.clear_items()
        for i in self.view_items[self.current_page]:
            if isinstance(
                i, (NextPageButton, PreviousPageButton, PageButton, SubmitAllOptionsButton),
            ):
                i.row = 4
            else:
                i.row = 1
            while True:
                try: # meh
                    self.add_item(i)
                    break
                except ValueError:
                    i.row += 1
        return self

    def get_config_option_by_type(self, _type: str) -> Any | None:
        if self.guild:
            return self.guild.get_config_option_by_type(_type)
        else:
            return self.user.get_config_option_by_type(_type)
        
    def get_item_by_type(self, _type: type) -> Item | None:
        return next((item for item in self.view_items[self.current_page] if isinstance(item, _type)), None)
    
    async def update_config(self, _dict: dict[str, Any]) -> None:
        if self.guild:
            return await self.guild.update_config(_dict)
        else:
            return await self.user.update_config(_dict)
    
    def _construct_embeds_and_options(self) -> tuple[list[str], list[Embed]]:
        values: list[str] = []
        embeds: list[Embed] = []
        for name, option in self._dict.items():
            embed_dict = option["embed"]
            ed = embed_dict
            embed = Embed(
                url=ed["url"],
                title=ed["title"],
                description=ed["description"],
                color=ed["color"] or ed["colour"],
            )
            embed.set_thumbnail(url=ed["thumbnail_url"])
            embed.set_image(url=ed["image_url"])
            for field in ed["fields"]:
                embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])
            
            values.append(name)
            embeds.append(embed)
        return values, embeds

    def _construct_items(self) -> list[tuple[Item]]:
        return [self._get_merged_items(option) for option in self.options]

    def _get_view_items_by_option_name(self, _name: str) -> dict[str, str | list[str]]:
        try:
            v = self._dict.get(_name)
            view_items: dict[str, str | list[str]] = {} # to keep sub items first
            for name, bound in v["sub"].items():
                view_items[name] = bound["item"]
            view_items[_name] = v["view_items"]
        except KeyError as e:
            raise ValueError(f"Invalid config option name: {_name}") from e
        return view_items
    
    def _return_item_by_instance(self, _class_name: str, _option: str | None) -> Any:
        disabled_value = False if _option else None
        if _option:
            disabled_value = self.get_config_option_by_type(_option)

        match _class_name:
            case "DisableButton":
                return DisableButton(disabled=disabled_value is False)
            case "EnableButton":
                return EnableButton(disabled=disabled_value is True)
            case "OptionSelect":
                return OptionSelect(_option)
            case "InputButton":
                return InputButton(_option)

    def _get_merged_items(self, _name: str) -> tuple[Item]:
        items: list[Item] = []
        for name, list_or_string in (self._get_view_items_by_option_name(_name)).items():
            if isinstance(list_or_string, list):
                for subvalue in list_or_string:
                    items.append(self._return_item_by_instance(subvalue, name))
            else:
                items.append(self._return_item_by_instance(list_or_string, name))
                # items positioning may be fucked up tho
        if len(self.embeds) > 1:
            items.extend([self.previous, self.next, self.to_page])
        items.append(self.submit)
        return tuple(items)

    @classmethod
    async def start(
        cls: type[CPT],
        obj: Context | _Interaction,
        _guild_or_user_num: Literal[1, 2] = 1,
        /,
        **kwargs,
    ) -> CPT:
        self = cls(obj, _guild_or_user_num, **kwargs)

        if _guild_or_user_num == 1:
            self.guild_or_user = await Guild.get(obj.guild.id, self.bot)
        elif _guild_or_user_num == 2:
            self.guild_or_user = await User.get(self.author.id, self.bot)

        self.view_items = self._construct_items()

        self._update_buttons()
        embed = self.current_embed
        view = self.current_view()

        if self.ctx:
            self.message = await self.ctx.send(embed=embed, view=view)  # type: ignore  # message could be None
        else:
            obj = self.interaction
            await obj.response.send_message(embed=embed, view=view)
            self.message = await obj.original_response()
        await self.wait()
        return self
