from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, TypeVar, overload

import discord
from discord import Interaction
from discord.ext.commands.context import Context as _Context
from discord.ui import View

from .embed import NewEmbed as Embed

if TYPE_CHECKING:
    from core import Context, Dwello

NVT = TypeVar("NVT", bound="NewView")


class NewView(View):
    """
    Custom view class inherrited from :class:`discord.ui.View`.

    Attributes
    -----------

    timeout: Optional[:class:`float`]
        Timeout in seconds from last interaction with the UI before no longer accepting input.
        If ``None`` then there is no timeout.

    kwargs: :class:`dict`
        A dictionary of transformed arguments that were passed into the command.
        These would be passed onto `Context.send()` for when you `start()` the view.
    """

    def __init__(
        self,
        obj: Context | Interaction[Dwello] | None,
        *,
        timeout: float | None = 180,
        **kwargs,
    ):
        super().__init__(timeout=timeout)

        self.kwargs = kwargs

        self.ctx = None
        self.interaction = None

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

        self.message: discord.Message = None

    async def from_context(self) -> Any:  # should be rewritten when creating new view
        return await self.send()

    async def from_interaction(self) -> Any:  # should be rewritten when creating new view
        return await self.send()

    @overload
    async def send(self) -> discord.Message:
        ...

    @overload
    async def send(self) -> None:
        ...

    async def send(self) -> discord.Message | None:
        if self.ctx:
            return await self.ctx.reply(view=self, **self.kwargs)
        else:
            return await self.interaction.response.send_message(view=self, **self.kwargs)

    async def interaction_check(self, interaction: Interaction[Dwello]) -> bool | None:
        if val := interaction.user == self.author:
            return val
        else:
            return await interaction.response.send_message(
                embed=(
                    Embed(
                        title="Failed to interact with the view",
                        description="Hey there! Sorry, but you can't interact with someone else's view.\n",
                        timestamp=discord.utils.utcnow(),
                    ).set_image(url="https://media.tenor.com/jTKDchcLtrcAAAAd/walter-white-walter-crying.gif")
                ),
                ephemeral=True,
            )

    async def on_timeout(self) -> discord.Message:
        self.clear_items()
        with contextlib.suppress(discord.errors.NotFound):
            await self.message.edit(view=self)

    def finish(self) -> None:
        self.clear_items()
        self.stop()

    @classmethod
    @overload
    async def start(
        cls: type[NVT],
        obj: None = None,
        *,
        timeout: None = 180,
        **kwargs,
    ) -> NVT:
        ...

    @classmethod
    @overload
    async def start(
        cls: type[NVT],
        obj: Context,
        *,
        timeout: float | None = 180,
        **kwargs,
    ) -> NVT:
        ...

    @classmethod
    @overload
    async def start(
        cls: type[NVT],
        obj: Interaction[Dwello],
        *,
        timeout: float | None = 180,
        **kwargs,
    ) -> NVT:
        ...

    @classmethod
    async def start(
        cls: type[NVT],
        obj: Context | Interaction[Dwello] | None,
        *,
        timeout: float | None = 180,
        **kwargs,
    ) -> NVT:
        new = cls(obj, timeout, **kwargs)
        if new.ctx:
            new.message = await new.from_context()
        elif new.interaction:
            await new.from_interaction()
            new.message = await obj.original_response()
        await new.wait()
        return new
