from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

import discord
from discord.app_commands import Choice
from typing_extensions import Self

if TYPE_CHECKING:
    from bot import Dwello

else:
    from discord.ext.commands import Bot as Dwello


class AutoComplete:
    def __init__(self: Self, bot: Dwello):
        self.bot = bot

    async def choice_autocomplete(
        self: Self,
        interaction: discord.Interaction,
        current: str,
        table: str,
        name: str,
        value: Optional[str] = None,
        all: bool = False,
    ) -> List[Choice]:
        """
        :Actually yea. The data type of the value needs to match the annotation
        :Forgot about that
        :job_name: str, value (s) must be strings.
        """

        records = self.bot.db_data
        table_ = records[table]

        choices = []
        item = len(current)

        if not value:
            value = name

        if all:
            choices.append(Choice(name="all", value="all"))

        for record in table_:
            name_ = record[name]
            value_ = record[value]

            if value_ is None and name_ is None:
                continue

            if current.startswith(str(name_).lower()[:item]):
                choices.append(Choice(name=str(name_), value=str(value_)))
            elif current.startswith(str(value_)[:item]):
                choices.append(Choice(name=str(name_), value=str(value_)))
        return choices[:5] if len(choices) > 5 else choices
