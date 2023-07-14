from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Tuple, List, Union

import dateparser
import discord
from discord import Interaction as DiscordInteraction, app_commands
from discord.ext import commands
from discord.ui import Button, Modal, TextInput, View
from typing_extensions import Self

from core import BaseCog

if TYPE_CHECKING:
    from asyncpg import Record

    from core import Dwello, DwelloContext

    Interaction = DiscordInteraction[Dwello]


class EditDueDateButton(Button):
    def __init__(self, todo: TodoItem, cog: Todo, *, label: str = "Add Due Date"):
        super().__init__()
        self.todo: TodoItem = todo
        self.cog: Todo = cog
        self.label: str = label
        self.style: discord.ButtonStyle = discord.ButtonStyle.green

    async def callback(self, interaction: Interaction):
        if interaction.user.id != self.todo.user_id:
            return await interaction.response.send_message("This button is not for you.", ephemeral=True)

        modal = EditDueDateModal(self.todo, self.cog)
        await interaction.response.send_modal(modal)


class EditDueDateModal(Modal, title="Edit Due Date"):
    due_date: TextInput = TextInput(
        label="Due at",
        required=True,
        min_length=1,
        max_length=50,
        placeholder="10m, 6 hours, tomorrow, next week, etc.",
    )

    def __init__(self, todo: TodoItem, cog: Todo) -> None:
        super().__init__()
        self.todo: TodoItem = todo
        self.cog: Todo = cog

    async def on_submit(self, interaction: Interaction):
        date = dateparser.parse(self.due_date.value, settings={"PREFER_DATES_FROM": "future"})
        if date is None:
            return await interaction.response.send_message(
                "Something went wrong when trying to parse the time.", ephemeral=True
            )

        async with self.cog.bot.pool.acquire() as conn:
            query = """
                UPDATE todo
                SET due_at = $1
                WHERE id = $2
            """
            await conn.execute(query, date, self.todo.id)

        timestamp = discord.utils.format_dt(date, style="R")
        await interaction.response.send_message(f"Done, The new due date is {timestamp}.", ephemeral=True)


class TodoAddModal(Modal, title="Add A Todo!"):
    """This modal is only called when using the context manager to add a todo item."""

    content: TextInput = TextInput(
        label="Content (optional)",
        required=False,
        min_length=1,
        max_length=1000,
        style=discord.TextStyle.long,
    )

    due_date: TextInput = TextInput(
        label="Due at (optional)",
        required=False,
        min_length=1,
        max_length=50,
        placeholder="10m, 6 hours, tomorrow, next week, etc.",
    )

    def __init__(self, cog: Todo, message: discord.Message) -> None:
        super().__init__()

        self.cog: Todo = cog
        self.message: discord.Message = message

    async def on_submit(self, interaction: Interaction) -> None:
        date: Optional[datetime] = None
        if value := self.due_date.value:
            date = dateparser.parse(value, settings={"PREFER_DATES_FROM": "future"})

        todo = TodoItem(
            user_id=interaction.user.id,
            channel_id=interaction.channel.id,
            message_id=self.message.id,
            guild_id=interaction.guild_id,
            content=self.content.value or None,
            due_at=date,
        )
        todo = await self.cog.add_todo(todo)
        embed, view = await self.cog.get_embed(todo)

        await interaction.response.send_message(embed=embed, view=view)


@dataclass
class TodoItem:
    """Represents a todo item inserted and fetched from the database."""

    user_id: int
    id: int = 0
    channel_id: Optional[int] = None
    message_id: Optional[int] = None
    guild_id: Optional[int] = None
    content: Optional[str] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @classmethod
    def from_record(cls, record: Record) -> Self:
        """Converts a `Record` to a `TodoItem`"""
        return cls(
            record["user_id"],
            record["id"],
            record["channel_id"],
            record["message_id"],
            record["guild_id"],
            record["content"],
            record["due_at"],
            record["completed_at"],
        )

UserMember = Union[discord.User, discord.Member]

class TodoPaginator(View):
    def __init__(self, cog: Todo, todos: List[TodoItem], author: UserMember) -> None:
        super().__init__()
        self.cog: Todo = cog
        self.todos: List[TodoItem] = todos
        self.message: discord.Message
        self.author: UserMember = author

        self._current_page: int = 0

    @property
    def length(self) -> int:
        return len(self.todos)

    @property
    def current_page(self) -> int:
        return self._current_page

    @property
    def index(self) -> str:
        return f"Todo {self.current_page + 1}/{self.length}"
    
    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("This button is not for you", ephemeral=True)
            return False
        return True

    async def get_page(self, *, page: Optional[int] = None, next: Optional[bool] = None) -> Optional[discord.Embed]:
        if page is None and next is None or all((page, next)):
            raise ValueError("change_page: Only one of two values must be supplied.")

        next_or_previous: int = 0
        if page is None:
            if next is True:
                next_or_previous = 1
            else:
                next_or_previous = -1

        _page = page if page is not None else self.current_page + next_or_previous

        if _page < 0 or _page > self.length:
            return None

        self._current_page = _page

        self._next.disabled = False
        self._previous.disabled = False

        if _page + 1 == self.length:
            self._next.disabled = True

        elif _page == 0:
            self._previous.disabled = True

        self.add_message_jump_button()
        embed = await self.cog.get_embed(self.todos[_page])
        return embed[0]

    def add_message_jump_button(self) -> None:
        todo = self.todos[self.current_page]
        if todo.message_id:
            jump_url = f"https://discord.com/channels/{todo.guild_id}/{todo.channel_id}/{todo.message_id}"
            button = Button(label="Jump To Message", url=jump_url, row=0)
            return self._children.insert(2, button)
        
        if self.children[2].label == "Jump To Message":
            del self._children[2]

    @discord.ui.button(label="Previous", row=0, style=discord.ButtonStyle.green)
    async def _previous(self, interaction: Interaction, _):
        embed = await self.get_page(next=False)
        await interaction.response.edit_message(content=self.index, embed=embed, view=self)

    @discord.ui.button(label="Next", row=0, style=discord.ButtonStyle.green)
    async def _next(self, interaction: Interaction, _):
        embed = await self.get_page(next=True)
        await interaction.response.edit_message(content=self.index, embed=embed, view=self)

    @discord.ui.button(label="Go To Page", row=1, style=discord.ButtonStyle.green)
    async def _go_to_page(self, interaction: Interaction, _):
        await interaction.response.send_modal(GoToPageModal(self))

    @discord.ui.button(label="Go To Todo With ID", row=1, style=discord.ButtonStyle.green, disabled=True)
    async def _go_to_id(self, interaction: Interaction, _):
        await interaction.response.send_message("Not implemented :3", ephemeral=True)


class GoToPageModal(Modal, title="Go To Page"):
    def __init__(self, paginator: TodoPaginator) -> None:
        super().__init__()
        self.paginator: TodoPaginator = paginator

        self.page: TextInput = TextInput(label="Page", min_length=1, max_length=3, placeholder=f"1-{self.paginator.length}")
        self.add_item(self.page)

    async def on_submit(self, interaction: Interaction) -> None:
        async def error() -> None:
            msg = f"Couldn't find that todo, make sure it's a number between `1` and `{self.paginator.length}`"
            await interaction.response.send_message(msg, ephemeral=True)

        try:
            page = int(self.page.value)
        except ValueError:
            return await error()

        if page <= 0 or page > self.paginator.length:
            return await error()

        embed = await self.paginator.get_page(page=page - 1)
        await interaction.response.edit_message(content=self.paginator.index, embed=embed, view=self.paginator)


class Todo(BaseCog):
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot

    def cog_load(self) -> None:
        self.ctx_menu = app_commands.ContextMenu(name="Add Todo", callback=self.context_menu)
        self.bot.tree.add_command(self.ctx_menu)

    async def add_todo(self, todo: TodoItem) -> TodoItem:
        """Adds a todo item to the database and returns it."""
        query = """
            INSERT INTO todo (
                user_id,
                channel_id,
                message_id,
                guild_id,
                content,
                due_at,
                completed_at
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7
            ) RETURNING id
        """
        async with self.bot.pool.acquire() as conn:
            record: Record = await conn.fetchrow(
                query,
                todo.user_id,
                todo.channel_id,
                todo.message_id,
                todo.guild_id,
                todo.content,
                todo.due_at,
                todo.completed_at,
            )
        todo.id = record["id"]
        return todo

    async def get_todo(self, id: int) -> Optional[TodoItem]:
        """Gets a todo item from the database"""
        query = """
            SELECT * FROM todo WHERE id = $1
        """
        async with self.bot.pool.acquire() as conn:
            result = await conn.fetchrow(query, id)

        if result is None:
            return

        todo = TodoItem.from_record(result)
        return todo

    async def get_todos(self, user_id: int) -> List[Optional[TodoItem]]:
        """Gets all of a users todos"""
        query = """
            SELECT * FROM todo WHERE user_id = $1
        """
        async with self.bot.pool.acquire() as conn:
            result = await conn.fetch(query, user_id)

        if not result:
            return []

        return [TodoItem.from_record(i) for i in result]

    async def get_embed(self, todo: TodoItem) -> Tuple[discord.Embed, Optional[View]]:
        embed = discord.Embed(title=f"Todo #{todo.id}", color=0x2B2D31)
        if todo.due_at is not None:
            embed.timestamp = todo.due_at
            embed.set_footer(text="Due")

        view = None
        if todo.message_id is not None:
            # We expect the channel to exist
            channel = self.bot.get_channel(todo.channel_id or 0)
            try:
                message: Optional[discord.Message] = await self.bot.get_or_fetch_message(channel, todo.message_id)
            except discord.NotFound:
                message = None

            if message is not None:
                jump_url = message.jump_url
                embed.add_field(name="Message", value=message.content, inline=False)
                embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)

            else:
                jump_url = f"https://discord.com/channels/{todo.guild_id}/{todo.channel_id}/{todo.message_id}"

            view = View()
            button = Button(label="Jump to Message", url=jump_url)
            view.add_item(button)

        if todo.content and todo.message_id:
            embed.add_field(name="Content", value=todo.content, inline=False)

        elif todo.content and not todo.message_id:
            embed.description = todo.content

        return embed, view

    async def context_menu(self, interaction: Interaction, message: discord.Message):
        modal = TodoAddModal(self, message)
        await interaction.response.send_modal(modal)

    @commands.group(description="Commands for dealing with Todos'")
    async def todo(self, ctx: DwelloContext):
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @todo.command(description="Adds a Todo")
    async def add(self, ctx: DwelloContext, *, content: str):
        todo = TodoItem(
            user_id=ctx.author.id,
            channel_id=ctx.channel.id,
            guild_id=ctx.guild.id,
            content=content,
        )
        todo = await self.add_todo(todo)
        embed = discord.Embed(title="Added todo!", description=content, color=0x2B2D31)
        embed.set_footer(text=f"ID: {todo.id}")
        view = View()
        view.add_item(EditDueDateButton(todo, self, label="Edit Due Date"))
        await ctx.send(embed=embed, view=view)

    @todo.command(description="Shows one of your Todos' by it's ID")
    async def show(self, ctx: DwelloContext, id: int):
        todo = await self.get_todo(id)
        if todo is None or todo.user_id != ctx.author.id:
            return await ctx.send("Couldn't find that todo...")

        embed, view = await self.get_embed(todo)
        await ctx.send(embed=embed, view=view)

    @todo.command()
    async def list(self, ctx: DwelloContext):
        todos = await self.get_todos(ctx.author.id)
        if not todos:
            return await ctx.send("You don't have any todos.")

        view = TodoPaginator(self, todos, ctx.author)
        first_page = await view.get_page(page=0)
        view.message = await ctx.send(view.index, embed=first_page, view=view)
