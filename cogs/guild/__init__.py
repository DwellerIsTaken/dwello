from __future__ import annotations

from typing import TYPE_CHECKING

from .config import Config
from .manage_channels import Channels
from .manage_messages import Messages

if TYPE_CHECKING:
    from core import Dwello


class Guild(Config, Channels, Messages, name="Guild Management"):
    """
    📝
    Includes commands and tools for managing guilds or communities, such as guild creation and configuration tools, role
    and permission management features, and tools for customizing the guild experience.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.select_emoji = "📝"
        self.select_brief = "Commands for guild customization, configuration, and management."


async def setup(bot: Dwello):
    await bot.add_cog(Guild(bot))
