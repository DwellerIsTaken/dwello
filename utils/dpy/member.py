from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

import discord
from discord import Member
from discord.ext import commands

from ..database.orm.warning import Warning

if TYPE_CHECKING:
    from core import Context
    

class NewMember(Member):
        
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)
        
    async def warn(self, ctx: Context, reason: Optional[str] = "Not specified") -> Warning:
        async with ctx.bot.safe_connection() as conn:
            record = await conn.fetchrow(
                "INSERT INTO warnings(guild_id, user_id, warn_text, created_at, warned_by) "
                "VALUES($1, $2, $3, $4, $5) "
                "RETURNING *",
                self.guild.id,
                self.id,
                reason,
                discord.utils.utcnow().replace(tzinfo=None),
                ctx.author.id,
            )
        return Warning(record, ctx.bot)
    
    async def unwarn(self) -> None:
        ...
    
    async def get_warnings(self, ctx: Context) -> List[Warning]:
        async with ctx.bot.safe_connection() as conn:
            records = await conn.fetch(
                "SELECT * FROM warnings WHERE guild_id = $1 AND user_id = $2",
                self.guild.id,
                self.id,
            )
        return [Warning(record, ctx.bot) for record in records]
    
    @classmethod
    async def convert(cls, ctx, argument): # fix asap
        member = await commands.MemberConverter().convert(ctx, argument)
        data = {
            'user': {
                'username': member.name,
                'public_flags': member.public_flags,
                'id': str(member.id),
                'global_name': member.global_name,
                'display_name': member.nick,
                'discriminator': member.discriminator,
                'bot': member.bot,
                'avatar_decoration': None,
                'avatar': str(member.avatar),
            },
            'roles': [str(role) for role in member._roles],
            'premium_since': member.premium_since,
            'pending': member.pending,
            'nick': member.nick,
            'mute': member.is_timed_out(),  # i assume this is correct
            'joined_at': member.joined_at,
            'flags': member._flags,
            'deaf': False,  # Replace this with appropriate deaf value if available
            'communication_disabled_until': member.timed_out_until,
            'avatar': member._avatar,
        }
        return cls(data=data, guild=member.guild, state=member._state)

    # self.warnings will then be len(self._get_warnings()) or smh
    # different for now
    # and how do we put connector in here?