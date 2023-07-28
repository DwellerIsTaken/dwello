from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import discord

if TYPE_CHECKING:
    from core import Dwello
    from asyncpg import Record
    from datetime import datetime


class User:
    __slots__ = (
        'id',
        'guild_id',
        'xp',
        'level',
        'messages',
        'total_xp',
        'money',
        'worked',
        'event_type',
        'job_id',
    )

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record['user_id']
        self.guild_id: int = record['guild_id']
        self.xp: int = record['xp']
        self.level: int = record['level']
        self.messages: int = record['messages']
        self.total_xp: int = record['total_xp']
        self.money: int = record['money']
        self.worked: int = record['worked'] # BIT
        self.event_type: str = record['event_type']
        self.job_id: Optional[int] = record['job_id']


class TwitchUser:
    __slots__ = ('username', 'user_id', 'guild_id')

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.username: str = record['username']
        self.user_id: int = record['user_id']
        self.guild_id: int = record['guild_id']
        
        
class Warning:
    __slots__ = (
        'id',
        'bot',
        'reason',
        'user_id',
        'guild_id',
        'warned_by',
        'created_at',
    )
    
    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record['warn_id']
        self.user_id: Optional[int] = record['user_id']
        self.reason: Optional[str] = record['warn_text']
        self.guild_id: Optional[int] = record['guild_id']
        self.warned_by: Optional[int] = record['warned_by']
        self.created_at: Optional[datetime] = record['created_at']
        
    async def remove(self, guild: discord.Guild, member: discord.Member) -> None:
        async with self.bot.safe_connection() as conn:
            await conn.execute(
                "DELETE FROM warnings WHERE warn_text = $1 AND guild_id = $2 AND user_id = $3",
                self.reason, guild.id, member.id, # should be removed based on warn_id, not reason
            )                                     # do when member is fixed
        return
        
        
class ServerData:
    __slots__ = (
        'guild_id',
        'message_text',
        'channel_id',
        'event_type',
        'counter_name',
        'deny_clicked',
    )

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.guild_id: int = record['guild_id']
        self.event_type: str = record['event_type']
        self.counter_name: str = record['counter_name']
        self.message_text: Optional[str] = record['message_text']
        self.channel_id: Optional[int] = record['channel_id']
        self.deny_clicked: Optional[int] = record['deny_clicked'] # BIT
        
        
class Prefix:
    __slots__ = ('guild_id', 'prefix')

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.guild_id: int = record['guild_id']
        self.prefix: str = record['prefix'] # VARCHAR
        

class Job:
    __slots__ = ('guild_id', 'name', 'id', 'salary', 'description')

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record['id']
        self.guild_id: int = record['guild_id']
        self.name: Optional[str] = record['name']
        self.salary: Optional[int] = record['salary']
        self.description: Optional[str] = record['description']


class News:
    __slots__ = ('title', 'message_id', 'channel_id', 'id')

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record['news_id']
        self.title: Optional[str] = record['title']
        self.message_id: Optional[int] = record['message_id']
        self.channel_id: Optional[int] = record['channel_id']


class Blacklist:
    __slots__ = ('user_id', 'reason')

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.user_id: int = record['user_id']
        self.reason: Optional[str] = record['reason']
