from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, TypeVar, Literal, overload

import discord
from discord.ext.commands.context import Context as _Context
from discord.ui import View

from .embed import NewEmbed as Embed

if TYPE_CHECKING:
    from core import Context, Dwello
    from discord import Interaction, Member
    from discord import User as _User

NVT = TypeVar("NVT", bound="NewView")

INTERACTION_CHECK_GIF = "https://media.tenor.com/jTKDchcLtrcAAAAd/walter-white-walter-crying.gif"


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
        obj: Context | Interaction[Dwello] | None = None,
        *,
        timeout: float | None = 180,
        **kwargs,
    ) -> None:
        super().__init__(timeout=timeout)

        self.__send_kwargs__ = kwargs

        self.bot: Dwello | None = None
        self.ctx: Context | None = None
        self.author: Member | _User | Any | None = None
        self.interaction: Interaction = None

        if obj:
            if any(
                (issubclass(obj.__class__, _Context), isinstance(obj, _Context)),
            ):
                self.bot = obj.bot
                self.author = obj.author
                self.ctx = obj
            else:
                self.author = obj.user
                self.bot = obj.client
                self.interaction = obj

        self.message: discord.Message | None = None

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
            return await self.ctx.reply(view=self, **self.__send_kwargs__)
        else:
            return await self.interaction.response.send_message(view=self, **self.__send_kwargs__)

    async def interaction_check(self, interaction: Interaction[Dwello]) -> Literal[True] | discord.Message:
        if val := interaction.user.id == self.author.id:
            return val

        return await interaction.response.send_message(
            embed=(
                Embed(
                    title="Failed to interact with the view",
                    description="Hey there! Sorry, but you can't interact with someone else's view.\n",
                    timestamp=discord.utils.utcnow(),
                ).set_image(url=INTERACTION_CHECK_GIF)
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
        obj: Context | Interaction[Dwello] | None = None,
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
