from __future__ import annotations

from typing import Any, Optional, MutableMapping  # noqa: F401

import discord
import datetime
from discord.ext import commands

from .flags import flag_value, BaseFlags
from .cache import cache, ExpiringCache  # noqa: F401

class AutoModFlags(BaseFlags):
    @flag_value
    def joins(self) -> int:
        """Whether the server is broadcasting joins"""
        return 1

    @flag_value
    def raid(self) -> int:
        """Whether the server is autobanning spammers"""
        return 2


'''class AutoModConfig:
    __slots__ = (
        'automod_flags',
        'id',
        'bot',
        'broadcast_channel_id',
        'broadcast_webhook_url',
        'mention_count',
        'safe_automod_entity_ids',
        'mute_role_id',
        'muted_members',
        '_cs_broadcast_webhook',
    )

    bot: Dwello
    automod_flags: AutoModFlags
    id: int
    broadcast_channel_id: Optional[int]
    broadcast_webhook_url: Optional[str]
    mention_count: Optional[int]
    safe_automod_entity_ids: set[int]
    muted_members: set[int]
    mute_role_id: Optional[int]

    @classmethod
    def from_record(cls, record: Any, bot: Dwello):
        self = cls()

        self.bot = bot
        self.automod_flags = AutoModFlags(record['automod_flags'] or 0)
        self.id = record['id']
        self.broadcast_channel_id = record['broadcast_channel']
        self.broadcast_webhook_url = record['broadcast_webhook_url']
        self.mention_count = record['mention_count']
        self.safe_automod_entity_ids = set(record['safe_automod_entity_ids'] or [])
        self.muted_members = set(record['muted_members'] or [])
        self.mute_role_id = record['mute_role_id']
        return self

    @property
    def broadcast_channel(self) -> Optional[discord.TextChannel]:
        guild = self.bot.get_guild(self.id)
        return guild and guild.get_channel(self.broadcast_channel_id)  # type: ignore

    @property
    def requires_migration(self) -> bool:
        return self.broadcast_channel_id is not None and self.broadcast_webhook_url is None

    @discord.utils.cached_slot_property('_cs_broadcast_webhook')
    def broadcast_webhook(self) -> Optional[discord.Webhook]:
        if self.broadcast_webhook_url is None:
            return None
        return discord.Webhook.from_url(self.broadcast_webhook_url, session=self.bot.http_session)

    @property
    def mute_role(self) -> Optional[discord.Role]:
        guild = self.bot.get_guild(self.id)
        return guild and self.mute_role_id and guild.get_role(self.mute_role_id)  # type: ignore

    def is_muted(self, member: discord.abc.Snowflake) -> bool:
        return member.id in self.muted_members

    async def apply_mute(self, member: discord.Member, reason: Optional[str]):
        if self.mute_role_id:
            await member.add_roles(discord.Object(id=self.mute_role_id), reason=reason)'''


class CooldownByContent(commands.CooldownMapping):
    def _bucket_key(self, message: discord.Message) -> tuple[int, str]:
        return (message.channel.id, message.content)


class SpamChecker:
    """This spam checker does a few things.

    1) It checks if a user has spammed more than 10 times in 12 seconds
    2) It checks if the content has been spammed 15 times in 17 seconds.
    3) It checks if new users have spammed 30 times in 35 seconds.
    4) It checks if "fast joiners" have spammed 10 times in 12 seconds.
    5) It checks if a member spammed `config.mention_count * 2` mentions in 12 seconds.

    The second case is meant to catch alternating spam bots while the first one
    just catches regular singular spam bots.

    From experience these values aren't reached unless someone is actively spamming.
    """

    def __init__(self):
        self.by_content = CooldownByContent.from_cooldown(15, 17.0, commands.BucketType.member)
        self.by_user = commands.CooldownMapping.from_cooldown(10, 12.0, commands.BucketType.user)
        self.last_join: Optional[datetime.datetime] = None
        self.new_user = commands.CooldownMapping.from_cooldown(30, 35.0, commands.BucketType.channel)
        self._by_mentions: Optional[commands.CooldownMapping] = None
        self._by_mentions_rate: Optional[int] = None

        # user_id flag mapping (for about 30 minutes)
        self.fast_joiners: MutableMapping[int, bool] = ExpiringCache(seconds=1800.0)
        self.hit_and_run = commands.CooldownMapping.from_cooldown(10, 12, commands.BucketType.channel)

    '''def by_mentions(self, config: ModConfig) -> Optional[commands.CooldownMapping]:
        if not config.mention_count:
            return None

        mention_threshold = config.mention_count * 2
        if self._by_mentions_rate != mention_threshold:
            self._by_mentions = commands.CooldownMapping.from_cooldown(mention_threshold, 12, commands.BucketType.member)
            self._by_mentions_rate = mention_threshold
        return self._by_mentions'''

    def is_new(self, member: discord.Member) -> bool:
        now = discord.utils.utcnow()
        seven_days_ago = now - datetime.timedelta(days=7)
        ninety_days_ago = now - datetime.timedelta(days=90)
        return member.created_at > ninety_days_ago and member.joined_at is not None and member.joined_at > seven_days_ago

    def is_spamming(self, message: discord.Message) -> bool:
        if message.guild is None:
            return False

        current = message.created_at.timestamp()

        if message.author.id in self.fast_joiners:
            bucket = self.hit_and_run.get_bucket(message)
            if bucket and bucket.update_rate_limit(current):
                return True

        if self.is_new(message.author):  # type: ignore
            new_bucket = self.new_user.get_bucket(message)
            if new_bucket and new_bucket.update_rate_limit(current):
                return True

        user_bucket = self.by_user.get_bucket(message)
        if user_bucket and user_bucket.update_rate_limit(current):
            return True

        content_bucket = self.by_content.get_bucket(message)
        if content_bucket and content_bucket.update_rate_limit(current):
            return True

        return False

    def is_fast_join(self, member: discord.Member) -> bool:
        joined = member.joined_at or discord.utils.utcnow()
        if self.last_join is None:
            self.last_join = joined
            return False
        is_fast = (joined - self.last_join).total_seconds() <= 2.0
        self.last_join = joined
        if is_fast:
            self.fast_joiners[member.id] = True
        return is_fast

    '''def is_mention_spam(self, message: discord.Message, config: ModConfig) -> bool:
        mapping = self.by_mentions(config)
        if mapping is None:
            return False

        current = message.created_at.timestamp()
        mention_bucket = mapping.get_bucket(message, current)
        mention_count = sum(not m.bot and m.id != message.author.id for m in message.mentions)
        return mention_bucket is not None and mention_bucket.update_rate_limit(current, tokens=mention_count) is not None'''