from __future__ import annotations

from typing import TYPE_CHECKING, List, TypeVar

from typing_extensions import Self

import discord

if TYPE_CHECKING:
    from datetime import datetime

    from asyncpg import Record, BitString

    from core import Dwello

UT = TypeVar("UT", bound="User")
WT = TypeVar("WT", bound="Warning")
IT = TypeVar("IT", bound="Idea")


class BasicORM:
    # improve
    @classmethod
    async def get(
        cls: type[Self],
        record: Record,
        bot: Dwello,
    ) -> Self:
        return cls(record, bot)


class User(BasicORM):
    """
    Class representing an ORM (Object Relational Mapping) for a global bot user.
    Contains such things as xp, level, money and message count.

    Parameters
    ----------
    record: :class:`asyncpg.Record`
        A record that is destributed across attributes.
    bot: :class:`Dwello`
        The bot instance mainly used, in this case, for working with the postgres database.
    
    Attributes
    ----------
    id: :class:`int`
        ID of the global user.
    xp: :class:`int`
        The amount of experience points on the current level.
    level: :class:`int`
        Current global level of the user.
    messages: :class:`int`
        The global message count for the user,
        representing only the count of messages successfully inserted into the database
        across all shared guilds where both the bot and the user are present.
    total_xp: :class:`int`
        Attribute representing the total experience points a user has ever gotten.
    money: :class:`int`
        User's money shared across guilds where both the bot and the user are present.
        Should be used in global economy or smh.
    _worked: :class:`asyncpg.BitString`
        Attribute representing whether the user already worked today (globally) or not.
        Use :property:`.worked` instead.
    bot: :class:`Dwello`

    SQL Types
    ---------
    id: :sql:`BIGINT PRIMARY KEY`\n
    xp: :sql:`BIGINT DEFAULT 0`\n
    level: :sql:`BIGINT DEFAULT 1`\n
    messages: :sql:`BIGINT DEFAULT 0`\n
    total_xp: :sql:`BIGINT DEFAULT 0`\n
    money: :sql:`BIGINT DEFAULT 0`\n
    worked: :sql:`BIT NOT NULL DEFAULT B'0'`

    .. note::
        # event_type - removed
        # job_id - removed
        # this should be a global User, thus no event_type
        # maybe Member orm later or smh like UserJob (smht within eco)
        # GuildUser actually is the correct name
        # so, a leaderboard will be a global leaderbord (try to get the user, if no you exclude him from the leaderboard)
        # and here below is a global member that will have a global rank
        # to make a local leaderboard you can check for every user in guild what their rank is or smh
    """

    __slots__ = (
        "bot",
        "id",
        "xp",
        "level",
        "messages",
        "total_xp",
        "money",
        "_worked",
    )

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record["id"]
        self.xp: int = record["xp"]
        self.level: int = record["level"]
        self.money: int = record["money"]
        self.messages: int = record["messages"]
        self.total_xp: int = record["total_xp"]

        self._worked: BitString = record["worked"]

    @property # probaly temporary
    def worked(self) -> bool:
        return bool(self._worked.to_int())

    @property
    def current_xp(self) -> int:
        return self.xp
    
    @property
    def experience(self) -> int:
        return self.xp
    
    @property
    def message_count(self) -> int:
        return self.messages
    
    @property
    def xp_formula(self) -> int:
        return int(self.level ** 2 * 50)
    
    @property
    def xp_until_next_level(self) -> int:
        return self.xp_formula - self.xp

    @classmethod
    async def create(
        cls: type[UT],
        user_id: int,
        bot: Dwello,
    ) -> UT:
        async with bot.safe_connection() as conn:
            record: Record = await conn.fetchrow(
                """
                    INSERT INTO users (id) VALUES ($1)
                    ON CONFLICT (id) DO UPDATE SET id = excluded.id
                    RETURNING *;
                """,
                user_id,
            )
        return cls(record, bot)
    
    async def remove(self) -> None:
        async with self.bot.safe_connection() as conn:
            await conn.execute("DELETE FROM users WHERE id = $1", self.id)
        return

    async def get_rank(self) -> int | None:
        async with self.bot.safe_connection() as conn:
            #records: list[Record] = await conn.fetch("SELECT * FROM users ORDER BY total_xp DESC")
            query = """
                SELECT (SELECT COUNT(*) + 1
                        FROM users AS u2
                        WHERE u2.total_xp > u1.total_xp) AS rank
                FROM users AS u1
                WHERE id = $1
                ON CONFLICT DO NOTHING
            """
            rank: int | None = await conn.fetchval(query, self.id)
        return rank
    
    async def increase_xp(self, message: discord.Message, rate: int = 5) -> int:
        if message.author.bot or not message.guild:
            return
        xp = self.xp+rate
        level = self.level
        total = self.total_xp+rate
        messages = self.messages+1

        if xp >= self.xp_formula:
            xp, level = 0, level+1

        async with self.bot.safe_connection() as conn:
            await conn.execute(
                "UPDATE users SET xp = $1, total_xp = $2, level = $3, messages = $4 WHERE id = $5",
                xp,
                total,
                level,
                messages,
                message.author.id,
            )
        self.messages = messages
        self.total_xp = total
        self.level = level
        self.xp = xp

        return self.xp_until_next_level


class TwitchUser(BasicORM):
    __slots__ = ("bot", "username", "user_id", "guild_id")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.username: str = record["username"]
        self.user_id: int = record["user_id"]
        self.guild_id: int = record["guild_id"]


class Warning(BasicORM):
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
                "DELETE FROM warnings WHERE (warn_id, guild_id, user_id) IN (($1, $2, $3)) RETURNING *",
                self.id,
                self.guild_id,
                self.user_id,
            )

# different table for counters?
class ServerData(BasicORM):
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


class Prefix(BasicORM):
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
                "DELETE FROM prefixes WHERE (prefix, guild_id) IN (($1, $2)) RETURNING *",
                self.prefix,
                self.guild_id,
            )


class Job(BasicORM):
    __slots__ = ("bot", "guild_id", "name", "id", "salary", "description")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record["id"]
        self.guild_id: int = record["guild_id"]
        self.name: str | None = record.get("name")
        self.salary: int | None = record.get("salary")
        self.description: str | None = record.get("description")


class News(BasicORM):
    __slots__ = ("bot", "title", "message_id", "channel_id", "id")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record["news_id"]
        self.title: str | None = record.get("title")
        self.message_id: int | None = record.get("message_id")
        self.channel_id: int | None = record.get("channel_id")


class Blacklist(BasicORM):
    __slots__ = ("bot", "user_id", "reason")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.user_id: int = record["user_id"]
        self.reason: str | None = record.get("reason")


class Idea:
    """
    Class representing an ORM (Object Relational Mapping) for an idea suggested by bot users.
    These ideas are to be checked and implemented, or to be deleted.

    Parameters
    ----------
    record: :class:`asyncpg.Record`
        A record that is destributed across attributes.
    bot: :class:`Dwello`
        The bot instance mainly used, in this case, for working with the postgres database.
    
    Attributes
    ----------
    id: :class:`int`
        ID of the idea.
    author_id: :class:`int`
        ID of the idea's author.
    created_at: :class:`Optional[datetime.datetime]`
        The datetime object for when the idea was suggested, excluding tzinfo.
    content: :class:`Optional[str]`
        The content of the idea, or, rather, the idea itself.
    title: :class:`Optional[str]`
        Title of the given idea.
    bot: :class:`Dwello`

    SQL Types
    ---------
    id: :sql:`SERIAL PRIMARY KEY`\n
    author_id: :sql:`BIGINT NOT NULL`\n
    created_at: :sql:`TIMESTAMP`\n
    content: :sql:`TEXT`\n
    title: :sql:`TEXT`

    .. note::
        # somehow check whether ideas are similair (?)
        # check for bad words etc and dont suggest if found (?)
        # maybe allow everything tho
    """
    __slots__ = ("bot", "id", "author_id", "created_at", "content", "title", "voters")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record["id"]
        self.author_id: int = record["author_id"]
        self.created_at: datetime | None = record.get("created_at")
        self.content: str | None = record.get("content")
        self.title: str | None = record.get("title")

        self.voters: List[str] | None = None

    @property
    def name(self) -> str:
        return self.title

    @property
    def text(self) -> str:
        return self.content
    
    @property
    def votes(self) -> int:
        return len(self.voters)

    async def _get_voters(self) -> List[int]:
        async with self.bot.safe_connection() as conn:
            records: List[Record] = await conn.fetch(
                "SELECT * FROM idea_voters WHERE id = $1",
                self.id,
            )
        return [int(record['voter_id']) for record in records]

    async def remove(self) -> None:
        async with self.bot.safe_connection() as conn:
            return await conn.execute(
                "DELETE FROM ideas WHERE id = $1",
                self.id,
            )
        
    def voted(self, voter_id: int) -> bool:
        return voter_id in self.voters

    async def upvote(self, voter_id: int) -> None:
        async with self.bot.safe_connection() as conn:
            await conn.execute(
                "INSERT INTO idea_voters(id, voter_id) VALUES($1, $2)",
                self.id,
                voter_id,
            )
        self.voters.append(voter_id)
        return
    
    @classmethod
    async def get(
        cls: type[IT],
        record: Record,
        bot: Dwello,
    ) -> IT:
        self = cls(record, bot)
        self.voters = await self._get_voters()
        return self

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
                "INSERT INTO ideas(created_at, author_id, content, title) VALUES($1, $2, $3, $4) RETURNING *",
                discord.utils.utcnow().replace(tzinfo=None),
                author_id,
                content,
                title,
            )
        self = cls(record, bot)
        self.voters = await self._get_voters()
        return self
