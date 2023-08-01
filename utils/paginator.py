from __future__ import annotations

import discord
from discord import Interaction
from discord.emoji import Emoji
from discord.ui import Button, View
from discord.enums import ButtonStyle
from discord.partial_emoji import PartialEmoji
from discord.ext.commands.context import Context as _Context

from typing import (
    TYPE_CHECKING, Any, List, Optional, Type, TypeVar, Union,
)

import contextlib

if TYPE_CHECKING:
    from core import Context, Dwello, Embed

DPT = TypeVar("DPT", bound="DefaultPaginator")


class PreviousPageButton(Button["DefaultPaginator"]):
    def __init__(
        self,
        *,
        label: Optional[str] = "<",
        **kwargs,
    ):
        super().__init__(label=label, **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: DefaultPaginator = self.view

        view.current_page -= 1
        view._update_buttons()
        await interaction.response.edit_message(embed=view.embeds[view.current_page], view=view)


class StopViewButton(Button["DefaultPaginator"]):
    def __init__(
        self,
        *,
        style: ButtonStyle = ButtonStyle.red,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = "🗑",
        **kwargs,
    ):
        super().__init__(style=style, emoji=emoji, **kwargs)

    async def callback(self, interaction: Interaction[Dwello]):
        assert self.view is not None
        return await self._end(interaction)

    async def _end(self, interaction: Interaction):
        return await interaction.message.delete(delay=0)
    

class NextPageButton(Button["DefaultPaginator"]):
    def __init__(
        self,
        *,
        label: Optional[str] = ">", # use emoji instead
        **kwargs,
    ):
        super().__init__(label=label, **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: DefaultPaginator = self.view

        view.current_page += 1
        view._update_buttons()
        await interaction.response.edit_message(embed=view.embeds[view.current_page], view=view)
    

class GoBackButton(Button["DefaultPaginator"]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: DefaultPaginator = self.view

        await interaction.response.edit_message(**view.kwargs)
        return view.stop()


class DefaultPaginator(View):
    """
    A simple paginator that paginates through a list of embeds.

    kwargs:
        If you have another view or content you want to switch to you can pass that to the class and it'll be passed onto
        ``interaction.response.edit_message()``.
    """
    # embeds and values should be in the corresponding positions in their lists
    def __init__(
        self,
        obj: Union[Context, Interaction[Dwello]],
        embeds: List[Embed],
        /,
        values: Optional[List[Any]] = None,
        delete_button: Optional[bool] = False,
        **kwargs, # eh, redo?
    ):
        super().__init__()

        if any(
            (issubclass(obj.__class__, _Context), isinstance(obj, _Context)),
        ):
            self.bot: Dwello = obj.bot
            self.author = obj.author
            self.ctx: Context = obj
        else:
            self.author = obj.user
            self.bot: Dwello = obj.client
            self.interaction: Interaction = obj

        self.embeds = self._reconstruct_embeds(embeds)

        self.values = values
        self.delete_button = delete_button
        self.kwargs = kwargs

        self.next = NextPageButton()
        self.previous = PreviousPageButton()

        if len(self.embeds) > 1:
            self.add_item(self.previous)
            self.add_item(self.next)

        if self.delete_button:
            self.add_item(StopViewButton())

        if any(self.kwargs):
            self.add_item(GoBackButton(emoji="🏠", style=ButtonStyle.blurple))

        self.current_page = 0
        self.message: discord.Message = None

    def _reconstruct_embeds(self, embeds: List[Embed]) -> List[Embed]:
        _embeds: List[Embed] = []
        for i, embed in enumerate(embeds):
            if not embed.footer:
                embed.set_footer(text=f"Page: {i+1}")
            _embeds.append(embed)
        return _embeds

    def _update_buttons(self) -> None:
        styles = {True: ButtonStyle.gray, False: ButtonStyle.blurple}
        page = self.current_page
        total = len(self.embeds) - 1
        self.next.disabled = page == total
        self.previous.disabled = page == 0
        self.next.style = styles[page == total]
        self.previous.style = styles[page == 0]

    async def interaction_check(self, interaction: Interaction[Dwello]) -> Optional[bool]:
        if val := interaction.user == self.author:
            return val
        else:
            return await interaction.response.send_message(
                embed=(
                    Embed(
                        title="Failed to interact with the view",
                        description="Hey there! Sorry, but you can't interact with someone else's view.\n",
                        timestamp=discord.utils.utcnow(),
                    )
                    .set_image(url="https://media.tenor.com/jTKDchcLtrcAAAAd/walter-white-walter-crying.gif")
                ),
                ephemeral=True,
            )

    async def on_timeout(self) -> None:
        self.clear_items()
        with contextlib.suppress(discord.errors.NotFound):
            await self.message.edit(view=self)

    async def _start(self) -> DefaultPaginator:
        self._update_buttons()
        embed = self.embeds[0]
        if self.ctx:
            self.message = await self.ctx.send(embed=embed, view=self)
        else:
            obj = self.interaction
            send = obj.response.send_message
            if any(self.kwargs):
                if obj.response.is_done():
                    await obj.response.edit_message(embed=embed, view=self)
                else:
                    await send(embed=embed, view=self)
            else:
                await send(embed=embed, view=self)
            self.message = await obj.original_response()
        await self.wait()
        return self

    @classmethod
    async def start(
        cls: Type[DPT],
        obj: Union[Context, Interaction[Dwello]],
        embeds: List[Embed],
        /,
        delete_button: Optional[bool] = False,
        **kwargs,
    ) -> DPT:
        new = cls(obj, embeds, delete_button, **kwargs)
        return await new._start()
