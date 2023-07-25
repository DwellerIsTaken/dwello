from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core import Dwello
    from asyncpg import Record
    from datetime import datetime


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
        self.bot: Dwello= bot
        self.id: int = record['warn_id']
        self.user_id: Optional[int] = record['user_id']
        self.reason: Optional[str] = record['warn_text']
        self.guild_id: Optional[int] = record['guild_id']
        self.warned_by: Optional[int] = record['warned_by']
        self.created_at: Optional[datetime] = record['created_at']