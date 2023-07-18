from __future__ import annotations

# HERE WE CAN CONSTRUCT EMBED BASED ON GUILD CONFIG

import discord
from discord import Embed

from typing import TYPE_CHECKING, Any, Callable, ClassVar, Iterable, LiteralString, Optional, Sequence, Tuple, TypeVar, Union  # noqa: F401, E501


class DwelloEmbed(Embed):
    bot_dominant_colour: ClassVar[Optional[Union[int, discord.Colour]]] = None

    def __init__(
        self,
        *,
        colour: Optional[Union[int, discord.Colour]] = None,
        color: Optional[Union[int, discord.Colour]] = None,
        **kwargs,
    ):
        if not any((colour, color)):
            self.colour = self.bot_dominant_colour
        else: # db guild config color check
            self.colour = colour if colour is not None else color

        super().__init__(colour=self.colour, **kwargs)