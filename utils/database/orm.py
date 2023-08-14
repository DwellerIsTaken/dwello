from __future__ import annotations

from typing import TYPE_CHECKING, List, TypeVar

from typing_extensions import Self

import discord

if TYPE_CHECKING:
    from datetime import datetime

    from asyncpg import Record

    from core import Dwello


GT = TypeVar("GT", bound="Guild")
IT = TypeVar("IT", bound="Idea")
UT = TypeVar("UT", bound="User")
WT = TypeVar("WT", bound="Warning")


class BasicORM:
    # improve
    @classmethod
    async def get(
        cls: type[Self],
        record: Record,
        bot: Dwello,
    ) -> Self:
        return cls(record, bot)


class Blacklist(BasicORM):
    __slots__ = ("bot", "user_id", "reason")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.user_id: int = record["user_id"]
        self.reason: str | None = record.get("reason")


class Guild(BasicORM):
    """
    Class representing an ORM (Object Relational Mapping) for a configured (by user) guild.
    Fetches information from different tables in one.

    Note: Use :function:`.get` to call the class, otherwise it wouldn't work properly.

    Parameters
    ----------
    For :function:`.get` classmethod.

    id: :class:`int`
        The ID of a(n) (existing) guild for which the data will be fetched and distributed.
    bot: :class:`Dwello`
        The bot instance mainly used, in this case, for working with the postgres database.
    
    Attributes
    ----------
    If activated with :function:`.get`.

    id: :class:`int`
        ID of the guild.
    counter_category_denied: :class:`Optional[bool]`
        Whether to suggest a counter category when creating a counter or no.
        .. note::
            # I think when category is created we set it to True.
            # But if counter category is deleted we should set it to NULL ig,
            # because if they create a counter in the future this option wouldn't be suggested.
    twitch_users: :class:`dict[int, TwitchUser]`
        Dictionary that uses twitch user's twitch ID as a key and :class:`TwitchUser` ORM as a value.
    all_counter_id: :class:`Optional[int]`
        Discord ID of an 'all' counter channel, that counts all the users, including bots, in the guild, if a user set one.
    bot_counter_id: :class:`Optional[int]`
        Discord ID of a 'bot' counter channel, that counts all the bots in the guild, if a user set one.
    member_counter_id: :class:`Optional[int]`
        Discord ID of a 'member' counter channel, that counts all the users in the guild, if a user set one.
    category_counter_id: :class:`Optional[int]`
        Discord ID of a counter category, in which all the counters should be located, if a user set one.
    welcome_channel_id: :class:`Optional[int]`
        Discord ID of a welcome channel if a user set one.
    leave_channel_id: :class:`Optional[int]`
        Discord ID of a leave channel if a user set one.
    twitch_channel_id: :class:`Optional[int]`
        Discord ID of a twitch channel if a user set one.
    welcome_text: :class:`Optional[str]`
        Contains a welcome message for a welcome channel. Displayed when member joins the guild. Can be :type:`None`.
    leave_text: :class:`Optional[str]`
        Contains a leave message for a leave channel. Displayed when member leaves the guild. Can be :type:`None`.
    twitch_text: :class:`Optional[str]`
        Contains a twitch message for a twitch channel. Displayed when a twitch user goes online. Can be :type:`None`.
    bot: :class:`Dwello`

    SQL Types
    ---------
    guilds:
        - id: :sql:`BIGINT PRIMARY KEY`
        - all_counter: :sql:`BIGINT`
        - bot_counter: :sql:`BIGINT`
        - member_counter: :sql:`BIGINT`
        - category_counter: :sql:`BIGINT`
        - welcome_channel: :sql:`BIGINT`
        - leave_channel: :sql:`BIGINT`
        - twitch_channel: :sql:`BIGINT`
        - welcome_text: :sql:`TEXT`
        - leave_text: :sql:`TEXT`
        - twitch_text: :sql:`TEXT`

    guild_config:
        - guild_id: :sql:`BIGINT PRIMARY KEY REFERENCES guilds(id)`
        - counter_category_denied: :sql:`BOOLEAN DEFAULT NULL`

    twitch_users:
        - username: :sql:`TEXT`
        - user_id: :sql:`BIGINT`
        - guild_id: :sql:`BIGINT REFERENCES guilds(id)`
        - PRIMARY KEYS: :sql:`username`, :sql:`user_id`, :sql:`guild_id`

    .. note::
        # maybe bind this with custom discord.Guild class
        # trouble with asyncio tho
        # also: if leave channel isn't set use welcome channel as leave channel too
        # but what if the user doesn't want to send either leave or welcome messages?
        # then a third option?
    """
    __slots__ = (
        "id",
        "bot",
        "leave_text",
        "twitch_text",
        "twitch_users",
        "welcome_text",
        "all_counter_id",
        "bot_counter_id",
        "leave_channel_id",
        "member_counter_id",
        "twitch_channel_id",
        "welcome_channel_id",
        "category_counter_id",
        "counter_category_denied",
    )

    # General
    bot: Dwello
    id: int
    all_counter_id: int | None
    bot_counter_id: int | None
    member_counter_id: int | None
    category_counter_id: int | None
    welcome_channel_id: int | None
    leave_channel_id: int | None
    twitch_channel_id: int | None
    welcome_text: str | None
    leave_text: str | None
    twitch_text: str | None

    # Config Table
    counter_category_denied: bool | None

    # Twitch Table
    twitch_users: dict[int, TwitchUser]

    @property
    def category_denied(self) -> bool:
        return self.counter_category_denied
    
    @property
    def welcome_message(self) -> str | None:
        return self.welcome_text
    
    @property
    def leave_message(self) -> str | None:
        return self.leave_text
    
    @property
    def twitch_message(self) -> str | None:
        return self.twitch_text
    
    @property
    def counters(self) -> list[int | None]:
        """Returns a list of filtered counters' IDs."""
        return [
            self.all_counter_id,
            self.bot_counter_id,
            self.member_counter_id,
            self.category_counter_id,
        ]
    
    @property
    def filtered_counters(self) -> list[int]:
        """Returns a list of filtered counters' IDs."""
        return list(filter(None, [
            self.all_counter_id,
            self.bot_counter_id,
            self.member_counter_id,
            self.category_counter_id,
        ]))
    
    @property
    def counters_dict(self) -> dict[int, str]:
        """Returns a dictionary of counters' sql names with their ID a the key."""
        return dict(
            (key, value) for key, value in [
                (self.all_counter_id, "all_counter"),
                (self.bot_counter_id, "bot_counter"),
                (self.member_counter_id, "member_counter"),
                (self.category_counter_id, "category_counter"),
            ] if key is not None
        )
    
    @classmethod
    async def get(
        cls: type[GT],
        id: int,
        bot: Dwello,
    ) -> GT:
        self = cls()
        async with bot.safe_connection() as conn:
            guild_config_record: Record = await conn.fetchrow(
                "SELECT * FROM guild_config WHERE guild_id = $1",
                id,
            )
            guild_record: Record = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1",
                id,
            )
            twitch_records: list[Record] = await conn.fetch(
                "SELECT * FROM twitch_users WHERE guild_id = $1",
                id,
            )
        if guild_config_record:
            self.counter_category_denied = guild_config_record.get("counter_category_denied")
        else:
            self.counter_category_denied = None

        self.all_counter_id = guild_record.get("all_counter")
        self.bot_counter_id = guild_record.get("bot_counter")
        self.member_counter_id = guild_record.get("member_counter")
        self.category_counter_id = guild_record.get("category_counter")
        self.welcome_channel_id = guild_record.get("welcome_channel")
        self.leave_channel_id = guild_record.get("leave_channel")
        self.twitch_channel_id = guild_record.get("twitch_channel")
        self.welcome_text = guild_record.get("welcome_text")
        self.leave_text = guild_record.get("leave_text")
        self.twitch_text = guild_record.get("twitch_text")

        self.twitch_users = {}
        for twitch_record in twitch_records:
            self.twitch_users[twitch_record["user_id"]] = await TwitchUser.get(twitch_record, bot)

        self.id = id
        self.bot = bot
        return self
    
    @classmethod
    async def create(
        cls: type[GT],
        id: int,
        bot: Dwello,
    ) -> GT:
        self = cls()

        async with bot.safe_connection() as conn:
            record: Record = await conn.fetchrow(
                """
                INSERT INTO guilds (id) VALUES ($1)
                ON CONFLICT (id) DO UPDATE SET id = excluded.id
                RETURNING *;
                """, id,
            )
            config_record: Record = await conn.fetchrow("SELECT * FROM guild_config WHERE guild_id = $1", id)
            twitch_records: list[Record] = await conn.fetch("SELECT * FROM twitch_users WHERE guild_id = $1", id)

        self.counter_category_denied = config_record.get("counter_category_denied") if config_record else None

        self.all_counter_id = record.get("all_counter")
        self.bot_counter_id = record.get("bot_counter")
        self.member_counter_id = record.get("member_counter")
        self.category_counter_id = record.get("category_counter")
        self.welcome_channel_id = record.get("welcome_channel")
        self.leave_channel_id = record.get("leave_channel")
        self.twitch_channel_id = record.get("twitch_channel")
        self.welcome_text = record.get("welcome_text")
        self.leave_text = record.get("leave_text")
        self.twitch_text = record.get("twitch_text")

        self.twitch_users = {}
        for twitch_record in twitch_records:
            self.twitch_users[twitch_record["user_id"]] = await TwitchUser.get(twitch_record, bot)

        self.id = id
        self.bot = bot
        return self
    
    def _get_channel(self, _id: int | None) -> discord.abc.GuildChannel | None:
        return self.bot.get_channel(_id) if _id else None
    
    @property
    def all_counter(self) -> discord.abc.GuildChannel | None:
        return self._get_channel(self.all_counter_id)
    
    @property
    def all_counter_channel(self) -> discord.abc.GuildChannel | None:
        return self.all_counter
    
    @property
    def bot_counter(self) -> discord.abc.GuildChannel | None:
        return self._get_channel(self.bot_counter_id)
    
    @property
    def bot_counter_channel(self) -> discord.abc.GuildChannel | None:
        return self.bot_counter
    
    @property
    def member_counter(self) -> discord.abc.GuildChannel | None:
        return self._get_channel(self.member_counter_id)
    
    @property
    def member_counter_channel(self) -> discord.abc.GuildChannel | None:
        return self.member_counter
    
    @property
    def category_counter(self) -> discord.abc.GuildChannel | None:
        return self._get_channel(self.category_counter_id)
    
    @property
    def category_counter_channel(self) -> discord.abc.GuildChannel | None:
        return self.category_counter
    
    @property
    def welcome_channel(self) -> discord.abc.GuildChannel | None:
        return self._get_channel(self.welcome_channel_id)
    
    @property
    def leave_channel(self) -> discord.abc.GuildChannel | None:
        return self._get_channel(self.leave_channel_id)
    
    @property
    def twitch_channel(self) -> discord.abc.GuildChannel | None:
        return self._get_channel(self.twitch_channel_id)


class Idea:
    """
    Class representing an ORM (Object Relational Mapping) for an idea suggested by bot users.
    These ideas are to be checked and implemented, or to be deleted.

    Note: Use :function:`.get` or :function:`.create` classmethods to get proper :class:`Idea` in return,
    otherwise :attribute:`.voters` and :attribute:`.votes` will be :type:`None`.

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
    def votes(self) -> int | None:
        try:
            _votes = len(self.voters)
        except TypeError:
            _votes = 0
        return _votes

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


class TwitchUser(BasicORM):
    __slots__ = ("bot", "username", "user_id", "guild_id")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.username: str = record["username"]
        self.user_id: int = record["user_id"]
        self.guild_id: int = record["guild_id"]


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
    worked: :class:`bool`
        Attribute representing whether the user already worked today (globally) or not.
    bot: :class:`Dwello`

    SQL Types
    ---------
    id: :sql:`BIGINT PRIMARY KEY`\n
    xp: :sql:`BIGINT DEFAULT 0`\n
    level: :sql:`BIGINT DEFAULT 1`\n
    messages: :sql:`BIGINT DEFAULT 0`\n
    total_xp: :sql:`BIGINT DEFAULT 0`\n
    money: :sql:`BIGINT DEFAULT 0`\n
    worked: :sql:`BOOLEAN NOT NULL DEFAULT FALSE`

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
        self.worked: bool = record["worked"]

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
        self.id: int = record["id"]
        self.user_id: int | None = record.get("user_id")
        self.reason: str | None = record.get("reason")
        self.guild_id: int | None = record.get("guild_id")
        self.warned_by: int | None = record.get("warned_by")
        self.created_at: datetime | None = record.get("created_at")

    async def remove(self) -> list[Record]:
        async with self.bot.safe_connection() as conn:
            return await conn.fetch(
                "DELETE FROM warnings WHERE (id, guild_id, user_id) IN (($1, $2, $3)) RETURNING *",
                self.id,
                self.guild_id,
                self.user_id,
            )
