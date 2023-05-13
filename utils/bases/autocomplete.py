from __future__ import annotations

from discord.app_commands import Choice
from discord.ext import commands
import discord

from typing import List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Dwello 
    
else:
    from discord.ext.commands import Bot as Dwello

class AutoComplete:

    def __init__(self, bot: Dwello):
        self.bot = bot

    async def choice_autocomplete(self, interaction: discord.Interaction, current: str, table: str, name: str, value: Optional[str] = None, all: bool = False) -> List[Choice]: 

        '''
            :Actually yea. The data type of the value needs to match the annotation
            :Forgot about that
            :job_name: str, value (s) must be strings.
        '''

        records = self.bot.db_data
        table_ = records[table]

        choices = []
        item = len(current)

        if not value:
            value = name

        if all is True:
            choices.append(Choice(name = "all", value = "all"))

        for record in table_:
            name_ = record[name]
            value_ = record[value]

            if value_ is None:
                if name_ is None:
                    continue

            if current:
                pass

            if current.startswith(str(name_).lower()[:int(item)]):
                choices.append(Choice(name = str(name_), value = str(value_)))
                pass
                
            elif current.startswith(str(value_)[:int(item)]):
                choices.append(Choice(name = str(name_), value = str(value_)))
                pass

        if len(choices) > 5:
            return choices[:5]

        return choices

