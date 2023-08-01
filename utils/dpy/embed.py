from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, ClassVar

import discord

# HERE WE CAN CONSTRUCT EMBED BASED ON GUILD CONFIG


if TYPE_CHECKING:
    from discord.types.embed import Embed as EmbedData  # noqa: F401
    from discord.types.embed import EmbedType


class NewEmbed(discord.Embed):
    bot_dominant_colour: ClassVar[int | discord.Colour | None] = None

    # someone fix pls
    def __init__(
        self,
        *,
        colour: int | discord.Colour | None = None,
        color: int | discord.Colour | None = None,
        title: Any | None = None,
        type: EmbedType = "rich",
        url: Any | None = None,
        description: Any | None = None,
        timestamp: datetime.datetime | None = None,
    ) -> None:
        if not any((colour, color)):
            self.colour = self.bot_dominant_colour
        else:  # db guild config color check
            self.colour = colour if colour is not None else color

        super().__init__(
            colour=self.colour,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
