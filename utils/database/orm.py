from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import discord

if TYPE_CHECKING:
    from datetime import datetime

    from asyncpg import Record

    from core import Dwello

WT = TypeVar("WT", bound="Warning")
IT = TypeVar("IT", bound="Idea")


class User:
    __slots__ = (
        "bot",
        "id",
        "guild_id",
        "xp",
        "level",
        "messages",
        "total_xp",
        "money",
        "worked",
        "event_type",
        "job_id",
    )

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record["user_id"]
        self.guild_id: int = record["guild_id"]
        self.xp: int = record["xp"]
        self.level: int = record["level"]
        self.messages: int = record["messages"]
        self.total_xp: int = record["total_xp"]
        self.money: int = record["money"]
        self.worked: int = record["worked"]  # BIT
        self.event_type: str = record["event_type"]
        self.job_id: int | None = record.get("job_id")


class TwitchUser:
    __slots__ = ("bot", "username", "user_id", "guild_id")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.username: str = record["username"]
        self.user_id: int = record["user_id"]
        self.guild_id: int = record["guild_id"]


class Warning:
    __slots__ = (
        "id",
        "bot",
        "reason",
        "user_id",
        "guild_id",
        "warned_by",
        "created_at",
    )

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record["warn_id"]
        self.user_id: int | None = record.get("user_id")
        self.reason: str | None = record.get("warn_text")
        self.guild_id: int | None = record.get("guild_id")
        self.warned_by: int | None = record.get("warned_by")
        self.created_at: datetime | None = record.get("created_at")

    async def remove(self) -> list[Record]:
        async with self.bot.safe_connection() as conn:
            return await conn.fetch(
                "DELETE FROM warnings " "WHERE (warn_id, guild_id, user_id) IN (($1, $2, $3)) " "RETURNING *",
                self.id,
                self.guild_id,
                self.user_id,
            )


class ServerData:
    __slots__ = (
        "bot",
        "guild_id",
        "message_text",
        "channel_id",
        "event_type",
        "counter_name",
        "deny_clicked",
    )

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.guild_id: int = record["guild_id"]
        self.event_type: str = record["event_type"]
        self.counter_name: str = record["counter_name"]
        self.message_text: str | None = record.get("message_text")
        self.channel_id: int | None = record.get("channel_id")
        self.deny_clicked: int | None = record.get("deny_clicked")  # BIT


class Prefix:
    __slots__ = ("bot", "guild_id", "prefix")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.guild_id: int = record["guild_id"]
        self.prefix: str = record["prefix"]  # VARCHAR

    @property
    def name(self) -> str:
        return self.prefix

    async def remove(self) -> list[Record]:
        async with self.bot.safe_connection() as conn:
            return await conn.fetch(
                "DELETE FROM prefixes " "WHERE (prefix, guild_id) IN (($1, $2)) " "RETURNING *",
                self.prefix,
                self.guild_id,
            )


class Job:
    __slots__ = ("bot", "guild_id", "name", "id", "salary", "description")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record["id"]
        self.guild_id: int = record["guild_id"]
        self.name: str | None = record.get("name")
        self.salary: int | None = record.get("salary")
        self.description: str | None = record.get("description")


class News:
    __slots__ = ("bot", "title", "message_id", "channel_id", "id")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record["news_id"]
        self.title: str | None = record.get("title")
        self.message_id: int | None = record.get("message_id")
        self.channel_id: int | None = record.get("channel_id")


class Blacklist:
    __slots__ = ("bot", "user_id", "reason")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.user_id: int = record["user_id"]
        self.reason: str | None = record.get("reason")


class Idea:
    __slots__ = ("bot", "id", "author_id", "votes", "created_at", "content", "title")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record["id"]
        self.author_id: int = record["author_id"]
        self.votes: int = record["votes"]
        self.created_at: datetime | None = record.get("created_at")
        self.content: str | None = record.get("content")
        self.title: str | None = record.get("title")

    @property
    def name(self) -> str:
        return self.title

    @property
    def text(self) -> str:
        return self.content

    async def remove(self) -> None:
        async with self.bot.safe_connection() as conn:
            return await conn.execute(
                "DELETE FROM ideas " "WHERE id = $1",
                self.id,
            )

    async def upvote(self) -> None:
        async with self.bot.safe_connection() as conn:
            await conn.execute(
                "UPDATE ideas SET votes = $1 WHERE id = $2",
                self.votes + 1,
                self.id,
            )
        self.votes += 1
        return

    @classmethod
    async def suggest(
        cls: type[IT],
        bot: Dwello,
        title: str,
        content: str,
        author_id: int,
    ) -> IT:
        async with bot.safe_connection() as conn:
            record: Record = await conn.fetchrow(
                "INSERT INTO ideas(created_at, author_id, content, title) " "VALUES($1, $2, $3, $4) " "RETURNING *",
                discord.utils.utcnow().replace(tzinfo=None),
                author_id,
                content,
                title,
            )
        return cls(record, bot)
