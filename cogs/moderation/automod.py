from __future__ import annotations

import contextlib
from collections import defaultdict
from typing import Any

import discord
from discord.ext import commands

from core import BaseCog, Dwello
from utils import HandleHTTPException, SpamChecker, Guild


class AutoMod(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        self._spam_check: defaultdict[int, SpamChecker] = defaultdict(SpamChecker)

    # add events here?

    async def check_raid(self, guild_id: int, member: discord.Member, message: discord.Message) -> None:
        checker = self._spam_check[guild_id]
        if not checker.is_spamming(message):
            return

        if member.guild.owner.id == member.id or self.bot.user.id == member.id:
            return

        async with HandleHTTPException(message.channel, title=f"Failed to ban {member}"):
            await member.ban(reason="Auto-ban for spamming")

    async def ban_for_mention_spam(
        self,
        mention_count: int,
        message: discord.Message,
        member: discord.Member,
        multiple: bool = False,
    ) -> None:
        if multiple:
            reason = f"Spamming mentions over multiple messages ({mention_count} mentions)"
        else:
            reason = f"Spamming mentions ({mention_count} mentions)"

        async with HandleHTTPException(message.channel, title=f"Failed to ban {member}"):
            await member.ban(reason=reason)

    # parallel event running in events.py
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        try:
            guild_id = message.guild.id
        except AttributeError:
            return

        _guild = await Guild.get(message.guild.id, self.bot)
        
        if _guild.antispam:
            with contextlib.suppress(AttributeError):
                await self.check_raid(guild_id, message.author, message)

            checker = self._spam_check[guild_id]
            if checker.is_mention_spam(message):
                return await self.ban_for_mention_spam(
                    checker.mention_count,
                    message,
                    message.author,
                    multiple=True,
                )

            # auto-ban tracking for mention spams begin here
            if len(message.mentions) <= 3:
                return

            # check if it meets the thresholds required
            mention_count = sum(not m.bot and m.id != message.author.id for m in message.mentions)
            if mention_count < checker.mention_count:
                return

            await self.ban_for_mention_spam(mention_count, message, message.author)
