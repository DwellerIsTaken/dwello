from __future__ import annotations

import contextlib
import datetime
import re
from typing import (
    TYPE_CHECKING,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import asyncpg
import discord
from discord import ButtonStyle
from discord.ext import commands
from typing_extensions import Self

import constants as cs
from bot import Dwello, DwelloContext
from utils import BaseCog, get_unix_timestamp, is_discord_link

# from utils import DuckCog, group
# from ._news_viewer import NewsViewer
# from utils import DuckContext

# T = TypeVar('T')

NVT = TypeVar("NVT", bound="NewsViewer")

fm_ut = get_unix_timestamp
fm_dt = discord.utils.format_dt


class Page(NamedTuple):  # DO SMTH LIKE THIS FOR EVERY CMD IN SCRAPING YO UNPACK EASILY
    """Represents a page of news."""

    news_id: int
    title: str
    message_id: int
    channel_id: int


class NewsFeed:
    """
    Represents a news feed that the user can navigate through.

    Attributes
    ----------
    news: List[:class:`Page`]
        A list of news pages.
    max_pages: :class:`int`
        The maximum number of pages in the feed.
    """

    __slots__: Tuple[str, ...] = (  # see what __slots__ are used for
        "news",
        "max_pages",
        "_current_page",
    )

    def __init__(self, news: List[asyncpg.Record]) -> None:  # use this to unpack later
        self.news: List[Page] = [Page(**n) for n in news]  # type: ignore
        self.max_pages = len(news)
        self._current_page = 0

    def advance(self) -> None:
        """Advance to the next page."""
        self._current_page += 1
        if self._current_page >= self.max_pages:
            self._current_page = 0

    def go_back(self) -> None:
        """Go back to the previous page."""
        self._current_page -= 1
        if self._current_page < 0:
            self._current_page = self.max_pages - 1

    @property
    def previous(self) -> Page:
        """Get the previous page."""
        number = (
            self._current_page - 1 if self._current_page > 0 else self.max_pages - 1
        )
        return self.news[number]

    @property
    def current(self) -> Page:
        """Get the current page"""
        return self.news[self._current_page]

    @property
    def next(self) -> Page:
        """Get the next page"""
        number = (
            self._current_page + 1 if self._current_page + 1 < self.max_pages else 0
        )
        return self.news[number]

    @property
    def current_index(self):
        """Get the current index of the paginator."""
        return self._current_page


class NewsPreviousButton(discord.ui.Button["NewsViewer"]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: NewsViewer = self.view

        view.news.advance()
        page = view.news.current
        view.update_labels()

        embed: discord.Embed = await view.get_embed(page)

        await interaction.response.edit_message(embed=embed, view=view)


class NewsCurrentButton(discord.ui.Button["NewsViewer"]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: NewsViewer = self.view

        view.stop()
        await view.message.delete()

        if view.ctx and isinstance(view.ctx, commands.Context):
            with contextlib.suppress(discord.HTTPException):
                await view.ctx.message.add_reaction(":white_check_mark:")


class NewsNextButton(discord.ui.Button["NewsViewer"]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: NewsViewer = self.view

        view.news.go_back()
        page = view.news.current
        view.update_labels()

        embed: discord.Embed = await view.get_embed(page)

        await interaction.response.edit_message(embed=embed, view=view)


class NewsGoBackButton(discord.ui.Button["NewsViewer"]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: NewsViewer = self.view

        await interaction.response.edit_message(embed=view.embed, view=view.old_view)
        return view.stop()


class NewsViewer(discord.ui.View):
    """The news viewer View.

    This class implements the functionality of the news viewer,
    allowing the user to navigate through the news feed.

    Attributes
    ----------
    news: :class:`NewsFeed`
        The news feed.
    """

    if TYPE_CHECKING:
        message: discord.Message
        ctx: Optional[DwelloContext]

    def __init__(
        self: Self,
        obj: Union[DwelloContext, discord.Interaction[Dwello]],
        news: List[asyncpg.Record] = None,
        /,
        embed: discord.Embed = None,
        old_view: discord.ui.View = None,
    ):
        super().__init__()

        if isinstance(obj, DwelloContext):
            self.author = obj.author
            self.bot: Dwello = obj.bot
            self.ctx = obj
        else:
            self.ctx = None
            self.author = obj.user
            self.bot: Dwello = obj.client

        self.embed = embed
        self.old_view = old_view

        if news:
            self.news = NewsFeed(news)

            self.current = NewsCurrentButton(style=ButtonStyle.red)
            self.next = NewsNextButton(style=ButtonStyle.blurple, label="\u226b")
            self.previous = NewsPreviousButton(
                style=ButtonStyle.blurple, label="\u226a"
            )

            self.add_item(self.previous)
            self.add_item(self.current)
            self.add_item(self.next)
        else:
            self.news = news

        if self.old_view and self.embed:
            self.go_back = NewsGoBackButton(
                emoji="🏠", label="Go Back", style=discord.ButtonStyle.blurple
            )

            self.add_item(self.go_back)

    async def interaction_check(
        self: Self, interaction: discord.Interaction[Dwello]
    ) -> Optional[bool]:
        if val := interaction.user == self.author:
            return val
        else:
            return await interaction.response.send_message(
                content="Hey! You can't do that!", ephemeral=True
            )

    # @cachetools.cached(cachetools.LRUCache(maxsize=10))
    async def get_embed(self: Self, page: Page) -> discord.Embed:
        """:class:`discord.Embed`: Used to get the embed for the current page."""
        print(page)

        # chache message instead
        channel: discord.TextChannel = await self.bot.fetch_channel(page.channel_id)
        message: discord.Message = await channel.fetch_message(page.message_id)
        time: datetime.datetime = message.created_at

        embed = discord.Embed(
            title=f"\N{NEWSPAPER} {fm_dt(time)} ({fm_dt(time, 'R')})",
            colour=cs.RANDOM_COLOR,
        )
        embed.add_field(name=page.title, value=message.content)

        # author = self.bot.get_user(page.author_id)
        # if author:
        embed.set_footer(
            text=f"ID: {page.news_id} - Authored by {message.author.name}",
            icon_url=message.author.display_avatar.url,
        )

        return embed

    """@discord.ui.button(style=discord.ButtonStyle.blurple, label='\u226a')
    async def previous(self: Self, interaction: discord.Interaction[Dwello], button: discord.ui.Button) -> None:
        self.news.advance()
        page = self.news.current
        self.update_labels()
        embed: discord.Embed = await self.get_embed(page)
        return await interaction.response.edit_message(embed=embed, view=self)"""

    """@discord.ui.button(style=discord.ButtonStyle.red)
    async def current(self: Self, interaction: discord.Interaction[Dwello], button: discord.ui.Button) -> None:
        self.stop()
        await self.message.delete()

        if self.ctx and isinstance(self.ctx, commands.Context):
            with contextlib.suppress(discord.HTTPException):
                await self.ctx.message.add_reaction(":white_check_mark:")"""

    """@discord.ui.button(style=discord.ButtonStyle.blurple, label='\u226b')
    async def next(self: Self, interaction: discord.Interaction[Dwello], button: discord.ui.Button):
        self.news.go_back()
        page = self.news.current
        self.update_labels()
        embed: discord.Embed = await self.get_embed(page)
        await interaction.response.edit_message(embed=embed, view=self)"""

    """@discord.ui.button(emoji="🏠", label="Go Back", style=discord.ButtonStyle.blurple)
    async def go_back(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(embed=self.embed, view=self.old_view)
        self.stop()"""

    def update_labels(self: Self):
        """Used to update the internal cache of the view, it will update the labels of the buttons."""
        previous_page_num = self.news.max_pages - self.news.news.index(
            self.news.previous
        )
        self.next.disabled = previous_page_num == 1

        self.current.label = str(self.news.max_pages - self.news.current_index)

        next_page_num = self.news.max_pages - self.news.news.index(self.news.next)
        self.previous.disabled = next_page_num == self.news.max_pages

    @classmethod
    async def start(
        cls: Type[NVT],
        ctx: DwelloContext,
        news: List[asyncpg.Record] = None,
        /,
        embed: discord.Embed = None,
        old_view: discord.ui.View = None,
    ) -> NVT:
        new = cls(ctx, news, embed, old_view)
        if not new.news:
            _embed: discord.Embed = discord.Embed(
                title="News",
                description="Sorry, there are no news yet.",
                color=cs.RANDOM_COLOR,
            )
        else:
            new.update_labels()
            _embed: discord.Embed = await new.get_embed(new.news.current)

        new.message = await ctx.send(embed=_embed, view=new)
        # new.bot.views.add(new)
        await new.wait()
        return new

    @classmethod
    async def from_interaction(
        cls: Type[NVT],
        interaction: discord.Interaction[Dwello],
        news: List[asyncpg.Record] = None,
        /,
        embed: discord.Embed = None,
        old_view: discord.ui.View = None,
    ) -> NVT:
        new = cls(interaction, news, embed, old_view)
        if not new.news:
            _embed: discord.Embed = discord.Embed(
                title="News",
                description="Sorry, there are no news yet.",
                color=cs.RANDOM_COLOR,
            )
        else:
            new.update_labels()
            _embed: discord.Embed = await new.get_embed(new.news.current)

        if new.old_view and new.embed:
            await interaction.response.edit_message(embed=_embed, view=new)
        else:
            await interaction.response.send_message(embed=_embed, view=new)
        new.message = await interaction.original_response()
        # new.bot.views.add(new)
        await new.wait()
        return new

    async def on_timeout(self: Self) -> None:
        # self.bot.views.discard(self)
        if self.message:
            await self.message.edit(view=None)

    """def stop(self: Self) -> None:
        #self.bot.views.discard(self)
        super().stop()"""


class News(BaseCog):
    @commands.group(invoke_without_command=True)
    async def news(self: Self, ctx: DwelloContext) -> NewsViewer:
        news = await self.bot.pool.fetch("SELECT * FROM news ORDER BY news_id DESC")

        return await NewsViewer.start(ctx, news)

    @commands.is_owner()
    @news.command(hidden=True, aliases=["publish"])
    async def add(self: Self, ctx: DwelloContext, link: str, *, title: str):
        if not await ctx.bot.is_owner(ctx.author):
            return await self.news(ctx)

        if is_discord_link(link) is False:
            return await ctx.reply("Invalid link provided.", user_mistake=True)

        success = False
        if match := re.search(r"https://discord\.com/channels/(\d+)/(\d+)/(\d+)", link):
            channel_id: int = int(match[2])
            message_id: int = int(match[3])

        try:  # prbly remove entire check or redo
            channel: discord.TextChannel = await self.bot.fetch_channel(channel_id)
            await channel.fetch_message(message_id)

        except discord.NotFound:
            t = "Couldn't find the message."

        except discord.Forbidden:
            t = "Missing necessary permissions."

        except discord.HTTPException:
            t = "Retrieving the message failed."

        else:
            t = "Published successfully."
            success = True

        if success:
            async with self.bot.safe_connection() as conn:
                await conn.execute(
                    "INSERT INTO news(title, message_id, channel_id) VALUES($1, $2, $3)",
                    title,
                    message_id,
                    channel_id,
                )

        return await ctx.reply(t, mention_author=True)

    @commands.is_owner()
    @news.command(hidden=True)
    async def remove(self: Self, ctx: DwelloContext, news_id: int):
        if not await ctx.bot.is_owner(ctx.author):
            return await self.news(ctx)

        async with ctx.bot.safe_connection() as conn:
            query = """
            WITH deleted AS (
                DELETE FROM news WHERE news_id = $1 RETURNING *
            ) SELECT COUNT(*) FROM deleted
            """
            # removed = await conn.fetchval(query, news_id)
            await conn.execute(query, news_id)

        return await ctx.reply(
            embed=discord.Embed(
                description=f"Successfully removed a newspost with ID: {news_id}.",
                color=cs.RANDOM_COLOR,
            )
        )

    '''@news.command(hidden=True)
    async def remove(self, ctx: DuckContext, news_id: int):
        """|coro|

        Removes a news item from the news feed

        Parameters
        ----------
        news_id: :class:`int`
            The snowflake ID of the news item to remove
        """
        if not await ctx.bot.is_owner(ctx.author):
            return await self.news(ctx)

        async with ctx.bot.safe_connection() as conn:
            query = """
            WITH deleted AS (
                DELETE FROM news WHERE news_id = $1 RETURNING *
            ) SELECT COUNT(*) FROM deleted
            """
            removed = await conn.fetchval(query, news_id)

        try:
            await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}" if removed else "\N{WARNING SIGN}")
        except discord.HTTPException:
            with contextlib.suppress(discord.HTTPException):
                await ctx.send("\N{WHITE HEAVY CHECK MARK} deleted." if removed else "\N{WARNING SIGN} not found.")'''