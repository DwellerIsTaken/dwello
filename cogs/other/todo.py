from __future__ import annotations

import textwrap
from contextlib import suppress
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import dateparser
import discord
from discord import Interaction as DiscordInteraction
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, Modal, TextInput, View

from core import BaseCog

if TYPE_CHECKING:
    from asyncpg import Record

    from core import Context, Dwello

Interaction = DiscordInteraction["Dwello"]


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

        todo = await self.cog.add_todo(
            user_id=interaction.user.id, content=self.content.value or None, message=self.message, due_date=date
        )

        await interaction.response.send_message(embed=todo.embed)


class TodoItem:
    """Represents a todo item inserted and fetched from the database."""

    def __init__(self, cog: Todo, record: Record) -> None:
        self.cog = cog
        self.bot = cog.bot

        self.id: int = record["id"]
        self.user_id: int = record["user_id"]
        self.channel_id: Optional[int] = record.get("channel_id")
        self.message_id: Optional[int] = record.get("message_id")
        self.guild_id: Optional[int] = record.get("guild_id")
        self.content: Optional[str] = record.get("content")
        self.message_content: Optional[str] = record.get("message_content")
        self.due_at: Optional[datetime] = record.get("due_at")
        self.completed_at: Optional[datetime] = record.get("completed_at")
        self.cached_content: Optional[str] = record.get("cached_content")

        self.message: Optional[discord.Message] = None

    async def edit(
        self,
        *,
        message_id: Optional[int] = None,
        content: Optional[str] = None,
        due_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> None:
        columns: Dict[str, Any] = {}

        if message_id is not None:
            columns["message_id"] = message_id

        if content is not None:
            columns["content"] = content

        if due_at is not None:
            columns["due_at"] = due_at

        if completed_at is not None:
            columns["completed_at"] = completed_at

        query = f"UPDATE todo SET {', '.join(f'{k} = ${i}' for i, k in enumerate(columns, start=1))} WHERE id = ${len(columns) + 1}"
        await self.bot.pool.execute(query, *columns.values(), self.id)

    async def delete(self) -> None:
        query = "DELETE FROM todo WHERE id = $1"
        await self.bot.pool.execute(query, self.id)

    @property
    def jump_url(self) -> Optional[str]:
        if self.message_id:
            return f"https://discord.com/channels/{self.guild_id}/{self.channel_id}/{self.message_id}"

    @property
    def colour(self) -> discord.Colour:
        return discord.Colour.from_str("#2B2D31")

    @property
    def color(self) -> discord.Colour:
        return self.colour

    @property
    def embed(self) -> discord.Embed:
        embed = discord.Embed(title=f"Todo #{self.id}", color=self.color)
        if self.due_at is not None:
            embed.set_footer(text="Due").timestamp = self.due_at

        if self.message is not None:
            message = self.message
            message_content = textwrap.shorten(message.content, width=1024, placeholder="...")
            embed.add_field(name="Message", value=message_content, inline=False)
            embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)

        if self.content:
            content = textwrap.shorten(self.content, width=1024, placeholder="...")

        if self.content and self.message_id:
            embed.add_field(name="Content", value=content, inline=False)

        elif self.content and not self.message_id:
            embed.description = content

        return embed

    @property
    def channel(self) -> Optional[discord.abc.Messageable]:
        return self.bot.get_channel(self.channel_id)

    async def fetch_message(self) -> None:
        channel = self.channel
        if channel is not None and self.message_id is not None:
            self.message = await self.cog.get_message(channel, self.message_id)

            if self.message and self.message.content != self.cached_content:
                self.cached_content = self.message.content

                query = "UPDATE todo SET cached_content = $1 WHERE id = $2"
                await self.bot.pool.execute(query, self.cached_content, self.id)

    def to_select_option(self, value: Any) -> discord.SelectOption:
        description = (
            textwrap.shorten(self.cached_content, width=100, placeholder="...") if self.cached_content else "No Message"
        )
        label = (
            textwrap.shorten(f"{self.id}: {self.content}", width=100, placeholder="...")
            if self.content
            else f"{self.id}: No Content"
        )

        option = discord.SelectOption(label=label, value=str(value), description=description)
        return option


UserMember = Union[discord.User, discord.Member]


class TodoSelect(discord.ui.Select):
    """A select menu that allows a user to browse up to 25 chunked TodoItems at a time. Supports switching pages."""

    def __init__(self, cog: Todo, todos: List[TodoItem]) -> None:
        self.cog: Todo = cog
        self.todos: List[TodoItem] = todos

        self.view: TodoPaginator
        self.button: Button = None

        for i, todo in enumerate(todos, start=1):
            todo.index = i

        self.options_ = [todo.to_select_option(todo.id) for todo in self.todos]

        self._chunks: List[List[TodoItem]] = [todos[i : i + 25] for i in range(0, len(todos), 25)]
        self.current_chunk: int = 0

        super().__init__(placeholder=self.placeholder_, options=self.chunk_as_option, min_values=1, max_values=1, row=0)

    @property
    def placeholder_(self) -> str:
        """Returns the placeholder for the current chunk."""
        return f"Select a Todo (Showing {self.chunk[0].index}-{self.chunk[-1].index}) (Total: {len(self.todos)})"

    @property
    def content(self) -> str:
        """Returns the content for the current todo"""
        return f"Todo {self.todos.index(self.selected) + 1}/{len(self.todos)}"

    @property
    def selected(self) -> Optional[TodoItem]:
        """Returns the selected `TodoItem`."""
        try:
            return [todo for todo in self.todos if todo.id == int(self.values[0])][0]
        except IndexError:
            pass

    @property
    def chunks(self) -> List[List[TodoItem]]:
        """Returns all of the chunks."""
        return self._chunks

    @property
    def chunk(self) -> List[TodoItem]:
        """Returns the current chunk."""
        return self.chunks[self.current_chunk]

    @property
    def chunk_as_option(self) -> List[discord.SelectOption]:
        """Returns the current chunk as `SelectOption`s."""
        return [todo.to_select_option(todo.id) for todo in self.chunk]

    def change_page(self) -> None:
        """Changes the underlying options and placeholder to the current chunk's."""
        self._underlying.options = self.chunk_as_option  # I don't know if there's a better way to do this
        self._underlying.placeholder = self.placeholder_

    async def callback(self, interaction: Interaction):
        if self.selected.message_id:
            self.button = Button(label="Jump To Message", url=self.selected.jump_url)
            self.view.add_item(self.button)

        else:
            with suppress(ValueError):
                self.view._children.remove(self.button)

        await interaction.response.edit_message(content=self.content, embed=self.selected.embed, view=self.view)


class TodoPaginator(View):
    """A view that incorporates `TodoSelect` and lets users browse through all of their todos as well as manage them."""

    def __init__(self, cog: Todo, todos: List[TodoItem], author: UserMember) -> None:
        super().__init__()
        self.cog: Todo = cog
        self.todos: List[TodoItem] = todos
        self.select: Optional[TodoSelect] = None
        self.message: discord.Message
        self.author: UserMember = author

        if len(todos) <= 25:
            self._children.remove(self.prev_page)
            self._children.remove(self.next_page)

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return False
        return True

    def disable(self) -> None:
        select = self.select
        self.prev_page.disabled = False
        self.next_page.disabled = False

        if select.current_chunk == 0:
            self.prev_page.disabled = True

        elif select.current_chunk == len(select.chunks) - 1:
            self.next_page.disabled = True

        with suppress(ValueError):
            self._children.remove(select.button)

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.green, row=1)
    async def edit(self, interaction: Interaction, _):
        select = self.select
        if not select.selected:
            return await interaction.response.send_message("You need to select a Todo before editing it", ephemeral=True)
        await interaction.response.send_modal(EditTodoModal(select.selected))

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red, row=1)
    async def delete(self, interaction: Interaction, _):
        select = self.select
        if not select.selected:
            return await interaction.response.send_message("You need to select a Todo before editing it", ephemeral=True)
        await select.selected.delete()
        await interaction.response.send_message(f"Successfully deleted `Todo #{self.select.selected.id}`", ephemeral=True)

    @discord.ui.button(label="Previous Page", style=discord.ButtonStyle.green, disabled=True, row=2)
    async def prev_page(self, interaction: Interaction, _):
        select = self.select
        select.current_chunk -= 1
        select.change_page()
        self.disable()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Next Page", style=discord.ButtonStyle.green, row=2)
    async def next_page(self, interaction: Interaction, _):
        select = self.select
        select.current_chunk += 1
        select.change_page()
        self.disable()
        await interaction.response.edit_message(view=self)


class EditTodoModal(Modal, title="Edit Todo"):
    def __init__(self, todo: TodoItem) -> None:
        super().__init__()
        self.todo: TodoItem = todo

        self.message: TextInput = TextInput(
            label="Message (Optional)",
            required=False,
            max_length=100,
            placeholder="https://discord.com/channels/737266097715281922/1007355853361389568/1133131906221875240",
            default=todo.jump_url,
            style=discord.TextStyle.long,
        )

        self.content: TextInput = TextInput(
            label="Content (Optional)",
            required=False,
            placeholder="Touch grass.",
            default=todo.content,
            style=discord.TextStyle.long,
        )

        self.due_at: TextInput = TextInput(
            label="Due Date (Optional)",
            required=False,
            placeholder="10m, 6 hours, tomorrow, next week, etc.",
            default=todo.due_at and todo.due_at.strftime("%d/%m/%Y, %H:%M") or None,
        )

        self.add_item(self.message)
        self.add_item(self.content)
        self.add_item(self.due_at)

    async def on_submit(self, interaction: Interaction) -> None:
        message: Optional[discord.Message] = None
        if self.message.value:
            split = self.message.value.split("/")
            channel_id = split[-2]
            message_id = split[-1]
            channel = interaction.client.get_channel(int(channel_id))

            if channel is None:
                return await interaction.response.send_message(
                    "Couldn't find that channel, does it still exist?", ephemeral=True
                )

            message = await channel.fetch_message(int(message_id))

            if message is None:
                return await interaction.response.send_message(
                    "Couldn't find that message, does it still exist?", ephemeral=True
                )

        date: Optional[datetime] = None
        if value := self.due_at.value:
            date = dateparser.parse(value, settings={"PREFER_DATES_FROM": "future"})
            if date is None:
                return await interaction.response.send_message("Couldn't parse that time, please try again.", ephemeral=True)

        await self.todo.edit(message_id=message and message.id or None, content=self.content.value or None, due_at=date)
        await interaction.response.send_message(f"Successfully edited `Todo #{self.todo.id}`.", ephemeral=True)


class Todo(BaseCog):
    bot: Dwello
    message_cache: Dict[int, discord.Message]

    def cog_load(self) -> None:
        self.ctx_menu = app_commands.ContextMenu(name="Add Todo", callback=self.context_menu)
        self.bot.tree.add_command(self.ctx_menu)

    async def get_message(self, channel: discord.abc.Messageable, message_id: int) -> Optional[discord.Message]:
        try:
            return self.message_cache[message_id]
        except KeyError:
            try:
                msg = await channel.fetch_message(message_id)
            except discord.HTTPException:
                return None
            else:
                self.message_cache[message_id] = msg
                return msg

    async def add_todo(
        self,
        *,
        user_id: int,
        content: Optional[str] = None,
        message: Optional[discord.Message] = None,
        due_date: Optional[datetime] = None,
    ) -> TodoItem:
        """Adds a todo item to the database and returns it."""
        parameters: List[Any] = [user_id]
        query = """
            INSERT INTO todo (
                user_id,
                channel_id,
                message_id,
                guild_id,
                cached_content,
                content,
                due_at
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7
            ) RETURNING *
        """

        if message is not None:
            guild_id = message.channel.guild.id

            parameters.extend([message.channel.id, message.id, guild_id, message.content])

        else:
            parameters.extend([None] * 4)

        parameters.append(content)
        parameters.append(due_date)
        result = await self.bot.pool.fetchrow(query, *parameters)
        todo = TodoItem(self, result)
        todo.message = message
        return todo

    async def get_todo(self, id: int) -> Optional[TodoItem]:
        """Gets a todo item from the database"""
        query = "SELECT * FROM todo WHERE id = $1"
        result = await self.bot.pool.fetchrow(query, id)

        if result is None:
            return

        todo = TodoItem(self, result)
        return todo

    async def get_todos(self, user_id: int) -> List[Optional[TodoItem]]:
        """Gets all of a users todos"""
        query = "SELECT * FROM todo WHERE user_id = $1"
        result = await self.bot.pool.fetch(query, user_id)

        if not result:
            return []

        return [TodoItem(self, i) for i in result]

    async def context_menu(self, interaction: Interaction, message: discord.Message):
        modal = TodoAddModal(self, message)
        await interaction.response.send_modal(modal)

    @commands.group(description="Commands for dealing with Todos'")
    async def todo(self, ctx: Context):
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @todo.command(description="Adds a Todo")
    async def add(self, ctx: Context, *, content: str):
        todo = await self.add_todo(user_id=ctx.author.id, content=content)
        embed = discord.Embed(title="Added todo!", description=content, color=todo.color)
        embed.set_footer(text=f"ID: {todo.id}")
        view = View()
        view.add_item(EditDueDateButton(todo, self, label="Edit Due Date"))
        await ctx.send(embed=embed, view=view)

    @todo.command(description="Shows one of your Todos' by it's ID")
    async def show(self, ctx: Context, id: int):
        todo = await self.get_todo(id)
        if todo is None or todo.user_id != ctx.author.id:
            return await ctx.send("Couldn't find that todo...")

        view: Optional[View] = None
        if todo.message_id:
            await todo.fetch_message()
            view = View()
            button = Button(label="Jump To Message", url=todo.jump_url)
            view.add_item(button)

        embed = todo.embed
        await ctx.send(embed=embed, view=view)

    @todo.command()
    async def list(self, ctx: Context):
        todos = await self.get_todos(ctx.author.id)
        if not todos:
            return await ctx.send("You don't have any todos.")

        view = TodoPaginator(self, todos, ctx.author)
        select = TodoSelect(self, todos)
        view.select = select
        view.add_item(select)
        await ctx.send("Showing todos", view=view)
