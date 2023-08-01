from __future__ import annotations

from typing import TYPE_CHECKING

from .news import News
from .scraping import Scraping
from .user_info import UserInfo

if TYPE_CHECKING:
    from core import Dwello


class Information(Scraping, UserInfo, News, name="Information"):
    """
    📚
    Includes commands and tools that provide information to users, such as server and user statistics, weather updates,
    news feeds, and other relevant information.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.select_emoji = "📚"
        self.select_brief = "Commands for providing information and data to users."


async def setup(bot: Dwello) -> None:
    await bot.add_cog(Information(bot))
