from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, TypeVar

import discord
import contextlib
from decimal import Decimal
from typing_extensions import Self

from constants import GUILD_CONFIG_DICT, USER_CONFIG_DICT

if TYPE_CHECKING:
    from datetime import datetime

    from asyncpg.protocol import Record

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


CONFIG_ALIASES = {
    "category_denied": "counter_category_denied",
    "counter_category_denied": "counter_category_denied",
    "turn_link_into_message": "turn_link_into_message",
    "link_to_message": "turn_link_into_message",
}


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
        "_all_counter",
        "_bot_counter",
        "_twitch_users",
        "_leave_channel",
        "_member_counter",
        "_twitch_channel",
        "_welcome_channel",
        "_category_counter",
        "_antispam",
        "_antispam_mention_count",
        "_cmd_preview",
        "_cmd_matches",
        "_counter_category_denied",
        "_turn_link_into_message",
        "_reactions_on_command",
        "_delete_button",
        "_delete_button_after",
        "_delete_reaction_after",
        "_delete_invoker_message_after",
        "_verification",
        "_personal_notifications",
        "_only_ephemeral",
        "_only_reply",
    )

    CHANNEL_DICT = { # this should get the correct sql column names from gives string
        "welcome_channel": {"text": "welcome_text", "channel": "welcome_channel", "label": "Welcome channel"},
        "leave_channel": {"text": "leave_text", "channel": "leave_channel", "label": "Leave channel"},
        "twitch_channel": {"text": "twitch_text", "channel": "twitch_channel", "label": "Twitch channel"},
        "welcome": {"text": "welcome_text", "channel": "welcome_channel", "label": "Welcome channel"},
        "leave": {"text": "leave_text", "channel": "leave_channel", "label": "Leave channel"},
        "twitch": {"text": "twitch_text", "channel": "twitch_channel", "label": "Twitch channel"},
    }

    COUNTER_DICT = {
        "all_counter": {"channel": "all_counter"},
        "bot_counter": {"channel": "bot_counter"},
        "member_counter": {"channel": "member_counter"},
        "category_counter": {"channel": "category_counter"},
        "all": {"channel": "all_counter"},
        "bot": {"channel": "bot_counter"},
        "member": {"channel": "member_counter"},
        "category": {"channel": "category_counter"},
    }

    # General
    bot: Dwello
    id: int

    _all_counter: GuildCounter
    _bot_counter: GuildCounter
    _member_counter: GuildCounter
    _category_counter: GuildCounter
    _welcome_channel: GuildChannel
    _leave_channel: GuildChannel
    _twitch_channel: GuildChannel

    # Config Table
    _antispam: bool
    _antispam_mention_count: int
    _cmd_preview: bool
    _cmd_matches: bool
    _counter_category_denied: bool | None
    _turn_link_into_message: bool
    _reactions_on_command: bool
    _delete_button: bool
    _delete_button_after: int
    _delete_reaction_after: int
    _delete_invoker_message_after: int | None
    _verification: bool
    _personal_notifications: bool
    _only_ephemeral: bool
    _only_reply: bool

    # Twitch Table
    _twitch_users: dict[int, TwitchUser]
    
    @property
    def all_counter(self) -> GuildCounter:
        return self._all_counter
    
    @property
    def bot_counter(self) -> GuildCounter:
        return self._bot_counter
    
    @property
    def member_counter(self) -> GuildCounter:
        return self._member_counter
    
    @property
    def category_counter(self) -> GuildCounter:
        return self._category_counter
    
    @property
    def welcome_channel(self) -> GuildChannel:
        return self._welcome_channel
    
    @property
    def leave_channel(self) -> GuildChannel:
        return self._leave_channel

    @property
    def twitch_channel(self) -> GuildChannel:
        return self._twitch_channel
    
    @property
    def antispam(self) -> bool:
        return self._antispam
    
    @property
    def antispam_mention_count(self) -> int:
        return self._antispam_mention_count
    
    @property
    def cmd_preview(self) -> bool:
        return self._cmd_preview
    
    @property
    def cmd_matches(self) -> bool:
        return self._cmd_matches
    
    @property
    def counter_category_denied(self) -> bool | None:
        return self._counter_category_denied
    
    @property
    def turn_link_into_message(self) -> bool:
        return self._turn_link_into_message
    
    @property
    def reactions_on_command(self) -> bool:
        return self._reactions_on_command
    
    @property
    def delete_button(self) -> bool:
        return self._delete_button
    
    @property
    def delete_button_after(self) -> int:
        return self._delete_button_after
    
    @property
    def delete_reaction_after(self) -> int:
        return self._delete_reaction_after
    
    @property
    def delete_invoker_message_after(self) -> int | None:
        return self._delete_invoker_message_after
    
    @property
    def verification(self) -> bool:
        return self._verification
    
    @property
    def personal_notifications(self) -> bool:
        return self._personal_notifications
    
    @property
    def only_ephemeral(self) -> bool:
        return self._only_ephemeral
    
    @property
    def only_reply(self) -> bool:
        return self._only_reply
    
    @property
    def twitch_users(self) -> dict[int, TwitchUser]:
        return self._twitch_users
    
    def __init__(self, _id: int, _bot: Dwello) -> None:
        # used to set attrs from the classmethods
        self.id = _id
        self.bot = _bot

    @property
    def category_denied(self) -> bool | None:
        return self.counter_category_denied
    
    @property
    def delete_invoker_message(self) -> bool:
        return self.delete_invoker_message_after is not None

    @property
    def counters(self) -> list[GuildCounter]:
        """Returns a list of ucounters."""
        return [
            self.all_counter,
            self.bot_counter,
            self.member_counter,
            self.category_counter,
        ]

    @property
    def counter_ids(self) -> list[int | None]:
        """Returns a list of un-filtered counters' IDs."""
        return [
            self.all_counter.id,
            self.bot_counter.id,
            self.member_counter.id,
            self.category_counter.id,
        ]

    @property
    def filtered_counter_ids(self) -> list[int]:
        """Returns a list of filtered counters' IDs."""
        return list(
            filter(
                None,
                [
                    self.all_counter.id,
                    self.bot_counter.id,
                    self.member_counter.id,
                    self.category_counter.id,
                ],
            )
        )

    @property
    def counters_dict(self) -> dict[int, str]:
        """Returns a dictionary of counters' sql names with their ID a the key."""
        return {
            key: value
            for key, value in [
                (self.all_counter.id, "all_counter"),
                (self.bot_counter.id, "bot_counter"),
                (self.member_counter.id, "member_counter"),
                (self.category_counter.id, "category_counter"),
            ]
            if key is not None
        }
    
    def _update_configuration(self, record: Record | None) -> None:
        """Updates attributes related to 'guild_config' sql table."""

        def get_default(name: str) -> Any:
            # the downside is that ur fucked if sub-options happen to have the same name
            if not record:
                try:
                    return GUILD_CONFIG_DICT.get(name)["default"]
                except KeyError:
                    for i in GUILD_CONFIG_DICT.values():
                        for sub_name, sub_value in i["sub"].items():
                            if sub_name == name:
                                return sub_value["default"]
            return record.get(name)
        
        # bruh idk if this is even needed..
        # all defaults already are stored in db
        self._antispam = get_default("antispam")
        self._antispam_mention_count = get_default("antispam_mention_count")
        self._cmd_preview = get_default("cmd_preview")
        self._cmd_matches = get_default("cmd_matches")
        self._counter_category_denied = get_default("counter_category_denied")
        self._turn_link_into_message = get_default("turn_link_into_message")
        self._reactions_on_command = get_default("reactions_on_command")
        self._delete_button = get_default("delete_button")
        self._delete_button_after = get_default("delete_button_after")
        self._delete_reaction_after = get_default("delete_reaction_after")
        self._delete_invoker_message_after = get_default("delete_invoker_message_after")
        self._verification = get_default("verification")
        self._personal_notifications = get_default("personal_notifications")
        self._only_ephemeral = get_default("only_ephemeral")
        self._only_reply = get_default("only_reply")
        return

    def _update_channels(self, record: Record) -> None:
        """
        Updates guild's channel attributes, such as :attr:`welcome_channel`.
        Channel attributes are updated to :class:`GuildChannel`; all its attributes are thus updated too.
        """

        self._welcome_channel = GuildChannel(
            "welcome_channel",
            self,
            id=record.get("welcome_channel"),
            text=record.get("welcome_text"),
        )
        self._leave_channel = GuildChannel(
            "leave_channel",
            self,
            id=record.get("leave_channel"),
            text=record.get("leave_text"),
        )
        self._twitch_channel = GuildChannel(
            "twitch_channel",
            self,
            id=record.get("twitch_channel"),
            text=record.get("twitch_text"),
        )
        return

    def _update_counters(self, record: Record) -> None:
        """Similiar to :func:`_update_channels`, but for guild counters."""

        self._all_counter = GuildCounter("all_counter", self, id=record.get("all_counter"))
        self._bot_counter = GuildCounter("bot_counter", self, id=record.get("bot_counter"))
        self._member_counter = GuildCounter("member_counter", self, id=record.get("member_counter"))
        self._category_counter = GuildCounter("category_counter", self, id=record.get("category_counter"))
        return
    
    def _get_config_option_name_from_alias(self, _name: str) -> str:
        _real_name = None
        with contextlib.suppress(KeyError):
            _real_name = CONFIG_ALIASES[_name]
        return _real_name or _name
    
    def _get_sql_name(self, _name: str) -> str:
        name = self._get_config_option_name_from_alias(_name)
        try:
            name = GUILD_CONFIG_DICT[name]['sql_name']
        except KeyError:
            name = name
        return name
    
    async def update_config(self, _dict: dict[str, Any]) -> None:
        # actually, some of the values won't be just bool soooo change it later ig
        updates = []
        for _type, value in _dict.items():
            param_name = self._get_sql_name(_type)
            # so, if _type is wrong then sql will just raise an error instead

            if isinstance(value, bool):
                updates.append(f"{param_name} = {'TRUE' if value else 'FALSE'}")
            elif value is None:
                updates.append(f"{param_name} = NULL")
            else:
                updates.append(f"{param_name} = {value}")
        
        if not updates:
            return

        query = f"UPDATE guild_config SET {', '.join(updates)} WHERE guild_id = $1 RETURNING *"
        async with self.bot.safe_connection() as conn:
            row: Record = await conn.fetchrow(query, self.id)

        self._update_configuration(row)
        return

    def get_channel_by_type(self, _type: str) -> GuildChannel | GuildCounter | None:
        _channels = ("welcome", "leave", "twitch")
        _counters = ("all", "bot", "member", "category")

        if _type.lower().startswith(_channels):
            _type = f"{_type.replace('_channel', '')}_channel"

        elif _type.lower().startswith(_counters):
            _type = f"{_type.replace('_counter', '')}_counter"

        return getattr(self, _type, None)  # type: ignore
    
    def get_config_option_by_type(self, _type: str) -> Any | None:
        return getattr(self, self._get_sql_name(_type), None)

    async def add_message(self, _type: str, text: str = None) -> None:
        if not text:
            return
        try:
            self.CHANNEL_DICT[_type]
        except KeyError as e:
            raise ValueError(f"Invalid (channel) type: {_type}") from e

        async with self.bot.safe_connection() as conn:  # store queries instead?
            query = f"UPDATE guilds SET {self.CHANNEL_DICT[_type]['text']} = $1 WHERE id = $2 RETURNING *"
            row: Record = await conn.fetchrow(query, text, self.id)

        self._update_channels(row)
        return
    
    async def add_channel(self, _type: str, channel_id: int) -> GuildChannel | None:
        try:
            self.CHANNEL_DICT[_type]
        except KeyError as e:
            raise ValueError(f"Invalid (channel) type: {_type}") from e
        
        async with self.bot.safe_connection() as conn:
            query = f"UPDATE guilds SET {self.CHANNEL_DICT[_type]['channel']} = $1 WHERE id = $2 RETURNING *"
            row: Record = await conn.fetchrow(query, channel_id, self.id)

        self._update_channels(row)
        return self.get_channel_by_type(_type)
    
    async def add_counter(self, _type: str, channel_id: int) -> GuildCounter | None:
        try:
            self.COUNTER_DICT[_type]
        except KeyError as e:
            raise ValueError(f"Invalid (channel) type: {_type}") from e
        
        async with self.bot.safe_connection() as conn:
            query = f"UPDATE guilds SET {self.COUNTER_DICT[_type]['channel']} = $1 WHERE id = $2 RETURNING *"
            row: Record = await conn.fetchrow(query, channel_id, self.id)

        self._update_counters(row)
        return self.get_channel_by_type(_type)

    async def _exe(self, option: str, value: Any) -> None:
        async with self.bot.safe_connection() as conn:
            await conn.execute(f"UPDATE guild_config SET {option} = $1 WHERE guild_id = $2", value, self.id)
        return

    @classmethod
    async def get(
        cls: type[GT],
        _id: int,
        bot: Dwello,
    ) -> GT:
        self = cls(_id, bot)

        async with self.bot.safe_connection() as conn:
            config_record: Record = await conn.fetchrow(
                "SELECT * FROM guild_config WHERE guild_id = $1",
                self.id,
            )
            record: Record = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1",
                self.id,
            )
            twitch_records: list[Record] = await conn.fetch(
                "SELECT * FROM twitch_users WHERE guild_id = $1",
                self.id,
            )
            
        if not record or not config_record:
            return await self.create(_id, bot)
        
        self._update_configuration(config_record)
        self._update_channels(record)
        self._update_counters(record)

        self._twitch_users = {}
        for twitch_record in twitch_records:
            self._twitch_users[twitch_record["user_id"]] = await TwitchUser.get(twitch_record, self.bot)
        return self

    @classmethod
    async def create(
        cls: type[GT],
        _id: int,
        bot: Dwello,
    ) -> GT:
        self = cls(_id, bot)

        async with self.bot.safe_connection() as conn:
            record: Record = await conn.fetchrow(
                """
                INSERT INTO guilds (id) VALUES ($1)
                ON CONFLICT (id) DO UPDATE SET id = excluded.id
                RETURNING *;
                """,
                self.id,
            )
            config_record: Record = await conn.fetchrow(
                """
                INSERT INTO guild_config (guild_id) VALUES ($1)
                ON CONFLICT (guild_id) DO UPDATE SET guild_id = excluded.guild_id
                RETURNING *;
                """,
                self.id,
            )
            twitch_records: list[Record] = await conn.fetch(
                "SELECT * FROM twitch_users WHERE guild_id = $1",
                self.id,
            )
        self._update_configuration(config_record)
        self._update_channels(record)
        self._update_counters(record)

        self._twitch_users = {}
        for twitch_record in twitch_records:
            self._twitch_users[twitch_record["user_id"]] = await TwitchUser.get(twitch_record, self.bot)

        return self


class _GuildChannel:
    """Class representing any db guild channel. Should be subclassed."""
    
    def __init__(self, _type: str, _id: int | None, guild: Guild) -> None:
        self.type: str = _type
        self.id: int | None = _id
        self.guild: Guild = guild

        self.bot: Dwello = guild.bot

    @property
    def name(self) -> str:
        return self.type.capitalize().replace('_', ' ')

    @property
    def instance(self) -> discord.abc.GuildChannel | None:
        return self.bot.get_channel(self.id) if self.id else None  # type: ignore
    
    async def remove(self) -> None:
        async with self.bot.safe_connection() as conn:
            query = f"UPDATE guilds SET {self.type} = NULL WHERE id = $1"
            await conn.execute(query, self.guild.id)
        return
    
    async def add_id(self, _id: int) -> None:
        await self.guild.add_channel(self.type, _id)
        self.id = _id
        return


class GuildChannel(_GuildChannel):
    """Class representing db guild channel that isn't a counter and is related to other db columns."""
    def __init__(self, _type: str, guild: Guild, /, id: int | None, text: str | None) -> None:
        super().__init__(_type, id, guild)

        self.text: str | None = text

    @property
    def message(self) -> str | None:
        return self.text

    @property
    def text_type(self) -> str | None:
        try:
            return Guild.CHANNEL_DICT[self.type]["text"]
        except KeyError:
            return None

    @property
    def message_type(self) -> str | None:
        return self.text_type
    
    async def add_message(self, _message: str | None) -> None:
        await self.guild.add_message(self.type, _message)
        self.text = _message
        return


class GuildCounter(_GuildChannel):
    """Class representing a db guild counter."""
    def __init__(self, _type: str, guild: Guild, /, id: int | None) -> None:
        super().__init__(_type, id, guild)


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

    __slots__ = ("bot", "_id", "_author_id", "_created_at", "_content", "_title", "voters")

    @property
    def id(self) -> int:
        return self._id
    
    @property
    def author_id(self) -> int:
        return self._author_id
    
    @property
    def created_at(self) -> datetime | None:
        return self._created_at
    
    @property
    def content(self) -> str | None:
        return self._content
    
    @property
    def title(self) -> str | None:
        return self._title

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self._id: int = record["id"]
        self._author_id: int = record["author_id"]
        self._created_at: datetime | None = record.get("created_at")
        self._content: str | None = record.get("content")
        self._title: str | None = record.get("title")

        self.voters: List[int] = []

    @property
    def name(self) -> str | None:
        return self.title

    @property
    def text(self) -> str | None:
        return self.content

    @property
    def votes(self) -> int:
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
        return [int(record["voter_id"]) for record in records]

    async def remove(self) -> None:
        async with self.bot.safe_connection() as conn:
            await conn.execute("DELETE FROM ideas WHERE id = $1", self.id)
            return

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


class Job(BasicORM): # not used currently
    __slots__ = ("bot", "guild_id", "name", "id", "salary", "description")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record["id"]
        self.guild_id: int = record["guild_id"]
        self.name: str | None = record.get("name")
        self.salary: int | None = record.get("salary")
        self.description: str | None = record.get("description")


class News(BasicORM): # not used currently
    __slots__ = ("bot", "title", "message_id", "channel_id", "id")

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self.id: int = record["news_id"]
        self.title: str | None = record.get("title")
        self.message_id: int | None = record.get("message_id")
        self.channel_id: int | None = record.get("channel_id")


class Prefix(BasicORM):
    __slots__ = ("bot", "_prefix", "_guild_id")

    @property
    def guild_id(self) -> int:
        return self._guild_id
    
    @property
    def prefix(self) -> str:
        return self._prefix

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self._prefix: str = record["prefix"]
        self._guild_id: int = record["guild_id"]

    def __str__(self) -> str:
        return self.prefix

    async def remove(self) -> list[Record]:
        async with self.bot.safe_connection() as conn:
            return await conn.fetch(
                "DELETE FROM prefixes WHERE (prefix, guild_id) IN (($1, $2)) RETURNING *",
                self.prefix,
                self.guild_id,
            )


class TwitchUser(BasicORM): # yet to be used in twitch.py
    __slots__ = ("bot", "_id", "_username", "_guild_id")

    @property
    def id(self) -> int:
        return self._id
    
    @property
    def username(self) -> str:
        return self._username
    
    @property
    def guild_id(self) -> int:
        return self._guild_id

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self._id: int = record["user_id"]
        self._username: str = record["username"]
        self._guild_id: int = record["guild_id"]

    @property
    def user_id(self) -> int:
        return self._id


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
        "_xp",
        "_level",
        "_messages",
        "_total_xp",
        "_money",
        "_worked",
        "_command_count",
        "_notify_user_on_levelup",
    )

    bot: Dwello
    id: int

    _xp: int
    _level: int
    _money: Decimal
    _messages: int
    _total_xp: int
    _worked: bool
    _command_count: int

    _notify_user_on_levelup: bool | None
    
    @property
    def xp(self) -> int:
        return self._xp
    0
    @property
    def level(self) -> int:
        return self._level
    
    @property
    def messages(self) -> int:
        return self._messages
    
    @property
    def total_xp(self) -> int:
        return self._total_xp
    
    @property
    def money(self) -> float:
        return float(self._money)
    
    @property
    def worked(self) -> bool:
        return self._worked
    
    @property
    def command_count(self) -> int:
        return self._command_count
    
    @property
    def notify_user_on_levelup(self) -> bool | None:
        return self._notify_user_on_levelup
    
    def __init__(self, _id: int, _bot: Dwello) -> None:
        # used to set attrs from the classmethods
        self.id = _id
        self.bot = _bot

    @property
    def balance(self) -> int | float:
        if (s:= str(self.money).split('.')[-1]) == "00" or s == "0":
            return int(self.money)
        return self.money
    
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
        return int(self.level**2 * 50)

    @property
    def xp_until_next_level(self) -> int:
        return self.xp_formula - self.xp
    
    def _attributes_from_record(self, record: Record) -> None:
        self._xp: int = record["xp"]
        self._level: int = record["level"]
        self._money: Decimal  = record["money"]
        self._messages: int = record["messages"]
        self._total_xp: int = record["total_xp"]
        self._worked: bool = record["worked"]
        self._command_count: int = record["command_count"]
        return
    
    def _get_sql_name(self, _name: str) -> str:
        try:
            name = USER_CONFIG_DICT[_name]['sql_name']
        except KeyError:
            name = _name
        return name
    
    def _update_configuration(self, record: Record | None) -> None:
        """Same logic as `:func:Guild._update_configuration`."""
        if record:
            self._notify_user_on_levelup = record.get("notify_user_on_levelup")
        else:
            self._notify_user_on_levelup = None
        return

    async def remove(self) -> None:
        async with self.bot.safe_connection() as conn:
            await conn.execute("DELETE FROM users WHERE id = $1", self.id)
        return
    
    def get_config_option_by_type(self, _type: str) -> Any | None:
        return getattr(self, self._get_sql_name(_type), None)
    
    def check_balance(self, amount: int | float) -> bool:
        return self.balance >= amount

    async def get_rank(self) -> int | None:
        """Gets user's global rank based on their total xp."""

        query = """
            SELECT (SELECT COUNT(*) + 1
            FROM users AS u2
            WHERE u2.total_xp > u1.total_xp) AS rank
            FROM users AS u1
            WHERE id = $1
            ON CONFLICT DO NOTHING
        """
        async with self.bot.safe_connection() as conn:
            return await conn.fetchval(query, self.id)
        
    async def increase_balance(self, message: discord.Message, balance: int | float, /, worked: bool = False) -> float:
        assert not message.author.bot

        _balance = float(balance)
        async with self.bot.safe_connection() as conn:
            q = "UPDATE users SET money = $1 WHERE id = $2"
            if worked:
                q = "UPDATE users SET money = $1, worked = TRUE WHERE id = $2"
            await conn.execute(q, _balance, self.id)

        self._money = Decimal(self.money + _balance)
        return self.balance

    async def increase_xp(self, message: discord.Message, rate: int = 5) -> int:
        if message.author.bot or not message.guild:
            return None

        xp = self.xp + rate
        level = self.level
        total = self.total_xp + rate
        messages = self.messages + 1

        if xp >= self.xp_formula:
            xp, level = 0, level + 1

        async with self.bot.safe_connection() as conn:
            await conn.execute(
                "UPDATE users SET xp = $1, total_xp = $2, level = $3, messages = $4 WHERE id = $5",
                xp,
                total,
                level,
                messages,
                self.id,
            )
        self._messages = messages
        self._total_xp = total
        self._level = level
        self._xp = xp

        return self.xp_until_next_level
    
    async def increase_command_count(self, amount: int = 1) -> None: # make a setter smh?
        async with self.bot.safe_connection() as conn:
            await conn.execute(
                "UPDATE users SET command_count = $1 WHERE id = $2",
                amount + self.command_count,
                self.id,
            )
        return
    
    async def update_config(self, _dict: dict[str, Any]) -> None:
        updates = []
        for _type, value in _dict.items():
            param_name = self._get_sql_name(_type)

            if isinstance(value, bool):
                updates.append(f"{param_name} = {'TRUE' if value else 'FALSE'}")
            elif value is None:
                updates.append(f"{param_name} = NULL")
            else:
                updates.append(f"{param_name} = {value}")
        
        if not updates:
            return

        query = f"UPDATE user_config SET {', '.join(updates)} WHERE user_id = $1 RETURNING *"
        async with self.bot.safe_connection() as conn:
            row: Record = await conn.fetchrow(query, self.id)

        self._update_configuration(row)
        return
    
    @classmethod
    async def get(
        cls: type[UT],
        user_id: int,
        bot: Dwello,
    ) -> UT:
        self = cls(user_id, bot)

        async with self.bot.safe_connection() as conn:
            config_record: Record = await conn.fetchrow(
                "SELECT * FROM user_config WHERE user_id = $1",
                self.id,
            )
            record: Record = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                self.id,
            )

        if not record or not config_record:
            return await self.create(user_id, bot)

        self._attributes_from_record(record)
        self._update_configuration(config_record)
        return self

    @classmethod
    async def create(
        cls: type[UT],
        user_id: int,
        bot: Dwello,
    ) -> UT:
        self = cls(user_id, bot)

        async with self.bot.safe_connection() as conn:
            record: Record = await conn.fetchrow(
                """
                    INSERT INTO users (id) VALUES ($1)
                    ON CONFLICT (id) DO UPDATE SET id = excluded.id
                    RETURNING *;
                """,
                self.id,
            )
            config_record: Record = await conn.fetchrow(
                """
                INSERT INTO user_config (user_id) VALUES ($1)
                ON CONFLICT (user_id) DO UPDATE SET user_id = excluded.user_id
                RETURNING *;
                """,
                self.id,
            )

        self._attributes_from_record(record)
        self._update_configuration(config_record)
        return self


class Warning(BasicORM):
    __slots__ = (
        "bot",
        "_id",
        "_reason",
        "_user_id",
        "_guild_id",
        "_warned_by",
        "_created_at",
    )

    @property
    def id(self) -> int:
        return self._id
    
    @property
    def user_id(self) -> int | None:
        return self._user_id
    
    @property
    def reason(self) -> str | None:
        return self._reason
    
    @property
    def guild_id(self) -> int | None:
        return self._guild_id
    
    @property
    def warned_by(self) -> int | None:
        return self._warned_by
    
    @property
    def created_at(self) -> datetime | None:
        return self._created_at

    def __init__(self, record: Record, bot: Dwello) -> None:
        self.bot: Dwello = bot
        self._id: int = record["id"]
        self._user_id: int | None = record.get("user_id")
        self._reason: str | None = record.get("reason")
        self._guild_id: int | None = record.get("guild_id")
        self._warned_by: int | None = record.get("warned_by")
        self._created_at: datetime | None = record.get("created_at")

    async def remove(self) -> list[Record]:
        async with self.bot.safe_connection() as conn:
            return await conn.fetch(
                "DELETE FROM warnings WHERE (id, guild_id, user_id) IN (($1, $2, $3)) RETURNING *",
                self.id,
                self.guild_id,
                self.user_id,
            )
