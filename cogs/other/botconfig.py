from __future__ import annotations

import asyncpg
import discord

from discord.ext import commands

from typing import Literal, Optional, Union, Any, List
from typing_extensions import Self

import constants as cs
from utils import BaseCog
from bot import Dwello, DwelloContext

class BotConfig(BaseCog):

    def __init__(self: Self, bot: Dwello, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        #self.prefixc: PrefixCommands = PrefixCommands(self.bot)