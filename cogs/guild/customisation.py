from __future__ import annotations

from typing import Any, Literal, TypeVar
from typing_extensions import Self

import discord
import contextlib

from discord import Interaction, ButtonStyle
from discord.app_commands import Choice
from discord.ext import commands

from core import Context, Dwello, Embed
from utils import CONFIG_DICT, Prefix, DefaultPaginator, Guild

CPT = TypeVar("CPT", bound="CustomisationPaginator")

Item = discord.ui.Item
Button = discord.ui.Button


async def setup(bot: Dwello) -> None:
    await bot.add_cog(Customisation(bot))


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
            self.bot.guild_prefixes[ctx.guild.id].append(prefix.name)
        except KeyError:
            self.bot.guild_prefixes[ctx.guild.id] = [prefix.name]
        return await ctx.reply(embed=Embed(description=f"The prefix is set to `{prefix.name}`"), permission_cmd=True)

    async def _display_prefixes(self, ctx: Context) -> discord.Message | None:
        default_prefixes: list[str] = self.bot.DEFAULT_PREFIXES + [f"<@!{self.bot.user.id}>"]
        prefixes = await self.db.get_prefixes(ctx.guild)

        embed: Embed = Embed(title="Prefixes").set_footer(text=None)

        if ctx.guild:
            embed.add_field(
                name="Guild's prefix(es)",
                value=", ".join(f"`{p.prefix}`" for p in prefixes) if prefixes else "`None` -> `dw.help prefix`",
                inline=False,
            )
        embed.add_field(
            name="Default prefixes",
            value=", ".join(p if str(self.bot.user.id) in p else f"`{p}`" for p in default_prefixes),
            inline=False,
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
        return ctx.guild is not None
    
    # maybe make a part of `guild` hybrid group
    @commands.hybrid_command(name="customise", aliases=["customisation"], help="Customise your guild", with_app_command=True)
    async def customise(self, ctx: Context):
        values: list[str] = []
        embeds: list[Embed] = []
        for option in CONFIG_DICT.values():
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
            
            values.append(option["sql_name"])
            embeds.append(embed)
        return await CustomisationPaginator.start(ctx, embeds, values)

    @commands.hybrid_group(aliases=["prefixes"], invoke_without_command=True, with_app_command=True)
    async def prefix(self, ctx: Context):
        async with ctx.typing():
            return await self._display_prefixes(ctx)

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @prefix.command(name="add", help="Adds bot prefix to the guild.")
    async def add_prefix(self, ctx: Context, *, prefix: str):
        _prefix: list[str] = prefix.split()
        if len(_prefix) > 1:
            return await ctx.reply("Prefix musn't contain whitespaces.", user_mistake=True)

        return await self._set_prefix(ctx, prefix)

    @prefix.command(name="display", help="Displays all prefixes.")
    async def display_prefix(self, ctx: Context):
        return await self._display_prefixes(ctx)

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @prefix.command(name="remove", description="Removes guild's prefix(es).")
    async def delete_prefix(self, ctx: Context, prefix: str):
        return await self._remove_prefix(ctx, prefix)

    @delete_prefix.autocomplete("prefix")
    async def autocomplete_callback_prefix(self, interaction: discord.Interaction, current: str):
        item = len(current)
        prefixes: list[Prefix] = await self.bot.db.get_prefixes(interaction.guild)
        choices: list[Choice[str]] = [Choice(name="all", value="all")] + [
            Choice(name=prefix.name, value=prefix.name)
            for prefix in prefixes
            if current.startswith(prefix.name.lower()[:item])
        ]
        return choices[:10]


class PreviousPageButton(Button["CustomisationPaginator"]):
    def __init__(self, **kwargs) -> None:
        super().__init__(label="<", **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: CustomisationPaginator = self.view

        view.current_page -= 1
        view._update_buttons()
        await interaction.response.edit_message(embed=view.current_embed, view=view.current_view())


class NextPageButton(Button["CustomisationPaginator"]):
    def __init__(self, **kwargs) -> None:
        super().__init__(label=">", **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: CustomisationPaginator = self.view

        view.current_page += 1
        view._update_buttons()
        await interaction.response.edit_message(embed=view.current_embed, view=view.current_view())


class SubmitAllOptionsButton(Button["CustomisationPaginator"]):
    def __init__(self, **kwargs) -> None:
        super().__init__(label="Submit", style=ButtonStyle.blurple, **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: CustomisationPaginator = self.view

        if view.updated_config:
            await view.guild.update_config(view.updated_config)
        view.clear_items()
        if len(view.embeds) > 1:
            view.add_item(view.previous)
            view.add_item(view.next)
        view.add_item(view.submit)
        view.submit.disabled = True

        await interaction.response.edit_message(view=view)


class EnableButton(Button["CustomisationPaginator"]):
    def __init__(self, **kwargs) -> None:
        super().__init__(label="Enable", style=ButtonStyle.green, **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: CustomisationPaginator = self.view

        view.updated_config[view.option] = True
        self.disabled = True
        disable: DisableButton = view.get_item_by_type(DisableButton)
        with contextlib.suppress(AttributeError):
            disable.disabled = False

        await interaction.response.edit_message(view=view)


class DisableButton(Button["CustomisationPaginator"]):
    def __init__(self, **kwargs) -> None:
        super().__init__(label="Disable", style=ButtonStyle.red, **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: CustomisationPaginator = self.view

        view.updated_config[view.option] = False
        self.disabled = True
        enable: EnableButton = view.get_item_by_type(EnableButton)
        with contextlib.suppress(AttributeError):
            enable.disabled = False

        await interaction.response.edit_message(view=view)


CONFIG_VIEW_ITEMS = {
    "counter_category_denied": [EnableButton, DisableButton],
    "turn_link_into_message": [EnableButton],
}


class CustomisationPaginator(DefaultPaginator):
    def __init__(
        self,
        obj: Context | Interaction[Dwello],
        embeds: list[Embed],
        options: list[str],  # in this case it's the config parameter (sql) name
    ) -> None:
        super().__init__(obj, embeds, values=options)

        self.options = options # aslo: values

        self.updated_config: dict[str, Any] = {}
        self.guild: Guild | None = None # set in start() classmethod

        # so, the structure is like: config option -> embed & view
        # thus everything revolves (should) around the config option

        # and below we activate all the items (classes) in order to add them when needed
        # these are permanent thus saved into attributes

        self.next = NextPageButton()
        self.previous = PreviousPageButton()
        self.submit = SubmitAllOptionsButton()

        self.view_items: list[tuple[Item]] | None = None # constructed in classmethod

    @property
    def option(self) -> str:
        return self.options[self.current_page]
    
    # property is too slow
    def current_view(self) -> CustomisationPaginator:
        self.clear_items()
        for i in self.view_items[self.current_page]:
            self.add_item(i)
        return self
    
    def get_item_by_type(self, _type: type) -> Item | None:
        return next((item for item in self.view_items[self.current_page] if isinstance(item, _type)), None)

    def _get_view_items_by_option_name(self, _name: str) -> list[Any]:
        try:
            view_items = CONFIG_VIEW_ITEMS.get(_name)
        except KeyError as e:
            raise ValueError(f"Invalid config option name: {_name}") from e
        return view_items
    
    def _return_item_by_instance(self, _obj: object, _option: str | None) -> Self:
        disabled_value = False
        if _option:
            disabled_value = self.guild.get_config_option_by_type(_option) or False
        if isinstance(_obj, EnableButton):
            return EnableButton(disabled=disabled_value is True)
        if isinstance(_obj, DisableButton):
            return DisableButton(disabled=disabled_value is False)

    def _get_merged_items(self, _name: str) -> tuple[Item]:
        items: list[Item] = []
        for i in self._get_view_items_by_option_name(_name):
            items.append(self._return_item_by_instance(i(), _name))
        if len(self.embeds) > 1:
            items.extend([self.previous, self.next])
        items.append(self.submit)
        return tuple(items)
    
    def _construct_items(self):
        return [self._get_merged_items(option) for option in self.options]

    @classmethod
    async def start(
        cls: type[CPT],
        obj: Context | Interaction[Dwello],
        embeds: list[Embed],
        options: list[str],
        /,
        **kwargs,
    ) -> CPT:
        self = cls(obj, embeds, options, **kwargs)

        self.guild = await Guild.get(obj.guild.id, self.bot)
        self.view_items = self._construct_items()

        self._update_buttons()
        embed = self.current_embed
        view = self.current_view()

        if self.ctx:
            self.message = await self.ctx.send(embed=embed, view=view)  # type: ignore  # message could be None
        else:
            obj = self.interaction
            send = obj.response.send_message
            if any(self.kwargs):
                if obj.response.is_done():
                    await obj.response.edit_message(embed=embed, view=view)
                else:
                    await send(embed=embed, view=view)
            else:
                await send(embed=embed, view=view)
            self.message = await obj.original_response()
        await self.wait()
        return self
