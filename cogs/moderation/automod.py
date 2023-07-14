from __future__ import annotations

from typing import Any, Optional, MutableMapping  # noqa: F401

import discord
from discord.ext import commands  # noqa: F401
from collections import defaultdict

from utils import SpamChecker, HandleHTTPException
from core import BaseCog, Dwello, DwelloContext  # noqa: F401


class AutoMod(BaseCog):

    def __init__(self, bot: Dwello):
        self.bot = bot
        self._spam_check: defaultdict[int, SpamChecker] = defaultdict(SpamChecker)

    async def check_raid(self, guild_id: int, member: discord.Member, message: discord.Message) -> None:
        checker = self._spam_check[guild_id]
        if not checker.is_spamming(message):
            return
        
        if member.guild.owner.id == member.id or self.bot.user.id == member.id:
            return
        
        async with HandleHTTPException(message.channel, title=f"Failed to ban {member}"):
            await member.ban(reason='Auto-ban for spamming')
            