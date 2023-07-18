from __future__ import annotations

import contextlib
import datetime
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Tuple, Type, TypeVar, Union  # noqa: F401

import asyncpg
import discord
from discord import ButtonStyle, app_commands
from discord.ext import commands

import constants as cs  # noqa: F401
from core import BaseCog, Dwello, DwelloContext
from utils import get_unix_timestamp, is_discord_link

NVT = TypeVar("NVT", bound="NewsViewer")

fm_ut = get_unix_timestamp
fm_dt = discord.utils.format_dt


@dataclass
class Page:  # DO SMTH LIKE THIS FOR EVERY CMD IN SCRAPING YO UNPACK EASILY | MAYBE
    """Represents a page of news."""

    news_id: int
    title: str
    message_id: int
    channel_id: int
    cached_message: Optional[discord.Message] = None


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
        # self.news.reverse()

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
        number = self._current_page - 1 if self._current_page > 0 else self.max_pages - 1
        return self.news[number]

    @property
    def current(self) -> Page:
        """Get the current page"""
        return self.news[self._current_page]

    @property
    def next(self) -> Page:
        """Get the next page"""
        number = self._current_page + 1 if self._current_page + 1 < self.max_pages else 0
        return self.news[number]

    @property
    def current_index(self):
        """Get the current index of the paginator."""
        return self._current_page


class NewsPreviousButton(discord.ui.Button[NVT]):
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


class NewsCurrentButton(discord.ui.Button[NVT]):
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


class NewsNextButton(discord.ui.Button[NVT]):
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


class NewsGoBackButton(discord.ui.Button[NVT]):
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
        self,
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
            self.previous = NewsPreviousButton(style=ButtonStyle.blurple, label="\u226a")

            self.add_item(self.previous)
            self.add_item(self.current)
            self.add_item(self.next)
        else:
            self.news = news

        if self.old_view and self.embed:
            self.go_back = NewsGoBackButton(emoji="🏠", style=discord.ButtonStyle.blurple)

            self.add_item(self.go_back)

    async def get_embed(self, page: Page) -> discord.Embed:
        """:class:`discord.Embed`: Used to get the embed for the current page."""

        message: discord.Message | None = page.cached_message

        if not message:
            channel: discord.TextChannel = await self.bot.getch(
                self.bot.get_channel, self.bot.fetch_channel, page.channel_id
            )
            message: discord.Message | None = await self.bot.get_or_fetch_message(channel, page.message_id)
            page.cached_message = message

        time: datetime.datetime = message.created_at

        embed = discord.Embed(
            title=f"\N{NEWSPAPER} {fm_dt(time)} ({fm_dt(time, 'R')})",
        )
        embed.add_field(name=page.title, value=message.content)

        # author = self.bot.get_user(page.author_id)
        # if author:
        embed.set_footer(
            text=f"ID: {page.news_id} - Authored by {message.author.name}",
            icon_url=message.author.display_avatar.url,
        )

        return embed

    def update_labels(self):
        """Used to update the internal cache of the view, it will update the labels of the buttons."""

        previous_page_num = self.news.max_pages - self.news.news.index(self.news.previous)
        self.previous.disabled = previous_page_num == 1

        self.current.label = str(self.news.current_index + 1)

        next_page_num = self.news.max_pages - self.news.news.index(self.news.next)
        self.next.disabled = next_page_num == self.news.max_pages

    async def interaction_check(self, interaction: discord.Interaction[Dwello]) -> Optional[bool]:
        if val := interaction.user == self.author:
            return val
        else:
            return await interaction.response.send_message(content="Hey! You can't do that!", ephemeral=True)
        
    async def on_timeout(self) -> None:
        self.clear_items()
        with contextlib.suppress(discord.errors.NotFound):
            await self.message.edit(view=self)

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
            )
        else:
            new.update_labels()
            _embed: discord.Embed = await new.get_embed(new.news.news[new.news.current_index])

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


class News(BaseCog):
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot

    @app_commands.command(name="news", description="Displays latest news on the bot.")
    async def app_news(self, interaction: discord.Interaction) -> NewsViewer:
        news = await self.bot.pool.fetch("SELECT * FROM news ORDER BY news_id DESC")

        return await NewsViewer.from_interaction(interaction, news)

    @commands.group(invoke_without_command=True)
    async def news(self, ctx: DwelloContext) -> NewsViewer:
        news = await self.bot.pool.fetch("SELECT * FROM news ORDER BY news_id DESC")

        return await NewsViewer.start(ctx, news)

    @commands.is_owner()
    @news.command(hidden=True, aliases=["publish"])
    async def add(self, ctx: DwelloContext, link: str, *, title: str):
        if not await ctx.bot.is_owner(ctx.author):
            return await self.news(ctx)

        if is_discord_link(link) is False:
            return await ctx.reply("Invalid link provided.", user_mistake=True)

        success = False
        channel_id: int = 0  # possibly get unbound
        message_id: int = 0  # possibly get unbound
        if match := re.search(r"https://discord\.com/channels/(\d+)/(\d+)/(\d+)", link):
            channel_id: int = int(match[2])
            message_id: int = int(match[3])

        try:  # prbly remove entire check or redo
            channel: discord.TextChannel = await self.bot.getch(self.bot.get_channel, self.bot.fetch_channel, channel_id)
            await self.bot.get_or_fetch_message(channel, message_id, force_fetch=True)

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
    async def remove(self, ctx: DwelloContext, news_id: int):
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
