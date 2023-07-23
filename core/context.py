from __future__ import annotations

import asyncio
import functools
import random
import re
from contextlib import suppress
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Callable, Iterable, Optional, Sequence, Tuple, TypeVar, Union

import discord
from discord.ext import commands
from typing_extensions import override

T = TypeVar("T")

if TYPE_CHECKING:
    from discord import ButtonStyle, Interaction


class ConfirmButton(discord.ui.Button):
    def __init__(self, label: str, emoji: str, button_style: ButtonStyle):
        super().__init__(
            style=button_style,
            label=label,
            emoji=emoji,
        )

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: Confirm = self.view
        view.value = True
        view.stop()


class CancelButton(discord.ui.Button):
    def __init__(self, label: str, emoji: str, button_style: ButtonStyle):
        super().__init__(style=button_style, label=label, emoji=emoji)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: Confirm = self.view
        view.value = False
        view.stop()


class Confirm(discord.ui.View):
    def __init__(self, buttons: Tuple[Tuple[str]], timeout: int = 30):
        super().__init__(timeout=timeout)
        self.message = None
        self.value = None
        self.ctx: NewContext = None
        self.add_item(
            ConfirmButton(
                emoji=buttons[0][0],
                label=buttons[0][1],
                button_style=(buttons[0][2] or discord.ButtonStyle.green),
            )
        )
        self.add_item(
            CancelButton(
                emoji=buttons[1][0],
                label=buttons[1][1],
                button_style=(buttons[1][2] or discord.ButtonStyle.red),
            )
        )

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user == self.ctx.author:
            return True
        messages = [  # should be defined someplace else in constants
            "Oh no you can't do that! This belongs to **{user}**",
            "This is **{user}**'s confirmation, sorry! 💢",
            "😒 Does this look yours? **No**. This is **{user}**'s confirmation button",
            "HEYYYY!!!!! this is **{user}**'s menu.",
            "Sorry but you can't mess with **{user}**' menu :(",
            "No. just no. This is **{user}**'s menu.",
            "You don't look like {user} do you...",
            "🤨 That's not yours! That's **{user}**'s menu",
            "🧐 Whomst! you're not **{user}**",
            "_out!_ 👋",
        ]
        await interaction.response.send_message(
            random.choice(messages).format(user=self.ctx.author.display_name),
            ephemeral=True,
        )

        return False


class NewContext(commands.Context):  # [commands.Bot], Generic[T]
    if TYPE_CHECKING:
        from .bot import Dwello

    bot: Dwello
    me: discord.Member
    guild: discord.Guild
    author: discord.Member

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def with_type(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapped(*args: Any, **kwargs: Any) -> discord.Message | None:
            context = args[0] if isinstance(args[0], commands.Context) else args[1]
            async with context.typing():
                return await func(*args, **kwargs)

        return wrapped

    @property
    def clean_prefix(self) -> str:
        """Prefix with escaped MarkDown"""
        return super().clean_prefix.replace("@", "(at)")

    @override
    async def send(
        self,
        content: Optional[str] = None,
        *,
        embed: Optional[discord.Embed] = None,
        embeds: Optional[Sequence[discord.Embed]] = None,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        **kwargs: Any,
    ) -> Optional[discord.Message]:
        assert isinstance(self.me, discord.Member)

        perms: discord.Permissions = self.channel.permissions_for(self.me)
        if not (perms.send_messages and perms.embed_links):
            with suppress(discord.Forbidden):
                await self.author.send(
                    (
                        "Bot don't have either Embed Links/Send Messages permission in that channel. "
                        "Please give sufficient permissions to the bot."
                    ),
                    view=self.send_view(),
                )
                return None

        if embed and embeds:
            raise commands.BadArgument("cannot pass both embed and embeds parameter to send()")

        if content or embed:
            test_string = re.sub(
                "[^A-Za-z0-9._-]+",
                "",
                (str(content) or "") + str((embed.to_dict() if embed else "")),
            )
            if self.bot.http.token in test_string.replace("\u200b", "").replace(" ", ""):
                raise commands.BadArgument("Could not send message as it contained the bot's token!")

        """if embed:
            colors = {embed.color} - {discord.Color.default(), None}
            embed.colour = next(iter(colors), self.color)"""

        embeds = [embed] if embed else (embeds or [])

        for embed_ in embeds:
            # guild custom embed color check
            if not embed_.color:
                embed_.color = self.bot.color

        if bold:
            content = f"**{content}**"
        if italic:
            content = f"*{content}*"
        if underline:
            content = f"__{content}__"

        content = str(content)[:1990] if content else None
        return await super().send(content=content, embeds=embeds, **kwargs)

    @override  # ritik check this and leave all the features but u can rewrite
    async def reply(  # add things and cleanup
        self,
        content: Optional[str] = None,
        *,
        ephemeral: Optional[bool] = None,
        user_mistake: Optional[bool] = None,
        mention_author: Optional[bool] = None,
        permission_cmd: Optional[bool] = None,
        mention_reference_author: Optional[bool] = True,
        **kwargs: Any,
    ) -> discord.Message:
        mention: bool = False
        message: discord.Message = self.message
        reference: discord.MessageReference = self.message.reference
        if reference and mention_reference_author:
            message = reference.resolved
            mention = message.author in self.message.mentions

        if mention_author:
            mention = mention_author

        if user_mistake:
            if any((mention_author, ephemeral, permission_cmd)):
                raise commands.BadArgument(
                    "Cannot pass mention_author, ephemeral, or permission_cmd when user_mistake = True."
                )  # noqa: E501
            mention, ephemeral = True, True

        elif permission_cmd:
            if any((mention_author, ephemeral, user_mistake)):
                raise commands.BadArgument(
                    "Cannot pass mention_author, ephemeral, or user_mistake when permission_cmd = True."
                )  # noqa: E501
            mention, ephemeral = False, True

        if not self.interaction:
            return await self.send(
                content,
                reference=message,
                mention_author=mention,
                ephemeral=ephemeral,
                **kwargs,
            )
        else:
            return await self.send(content, mention_author=mention, ephemeral=ephemeral, **kwargs)

    async def error(self, *args: Any, **kwargs: Any) -> Optional[discord.Message]:
        """Similar to send, but if the original message is deleted, it will delete the error message as well."""
        embed: Optional[discord.Embed] = kwargs.get("embed")
        if isinstance(embed, discord.Embed) and not embed.color:
            # if no color is set, set it to red
            embed.color = discord.Color.red()

        msg: Optional[discord.Message] = await self.reply(
            *args,
            **kwargs,
        )
        if isinstance(msg, discord.Message):
            try:
                await self.wait_for(
                    "message_delete",
                    check=lambda m: m.id == self.message.id,
                    timeout=30,
                )
            except asyncio.TimeoutError:
                return msg
            else:
                return await msg.delete(delay=0)
        return msg

    def outer_check(
        self,
        check: Callable[..., bool] | None = None,
        operator: Callable[[Iterable[object]], bool] = all,
        **kw: Any,
    ) -> Callable[..., bool]:
        """Check function for the event"""
        if check is not None:
            return check

        def __suppress_attr_error(func: Callable, *args: Any, **kwargs: Any) -> bool:
            """Suppress attribute error for the function."""
            try:
                func(*args, **kwargs)
                return True
            except AttributeError:
                return False

        def __internal_check(
            *args,
        ) -> bool:
            """Main check function"""
            convert_pred = [(attrgetter(k.replace("__", ".")), v) for k, v in kw.items()]
            return operator(
                all(pred(i) == val for i in args if __suppress_attr_error(pred, i)) for pred, val in convert_pred
            )

        return __internal_check

    async def wait_for(
        self,
        _event_name: str,
        *,
        timeout: float | None = None,
        check: Callable[..., bool] | None = None,
        suppress_error: bool = False,
        operator: Callable[[Iterable[object]], bool] = all,
        **kwargs: Any,
    ) -> Any:
        if _event_name.lower().startswith("on_"):
            _event_name = _event_name[3:].lower()

        try:
            return await self.bot.wait_for(
                _event_name,
                timeout=timeout,
                check=self.outer_check(check, operator, **kwargs),
            )
        except asyncio.TimeoutError:
            if suppress_error:
                await self.message.add_reaction("\N{ALARM CLOCK}")
                return None
            raise

    async def confirm(
        self,
        message: str = "Do you want to confirm?",
        buttons: Optional[Tuple[Union[discord.PartialEmoji, str], str, discord.ButtonStyle]] = None,
        timeout: int = 30,
        delete_after_confirm: bool = False,
        delete_after_timeout: bool = False,
        delete_after_cancel: Optional[bool] = None,
        return_message: bool = False,
    ) -> Union[bool, Tuple[bool, discord.Message]]:
        """A confirmation menu."""

        delete_after_cancel = delete_after_cancel if delete_after_cancel is not None else delete_after_confirm

        view = Confirm(
            buttons=buttons
            or (
                (None, "Confirm", discord.ButtonStyle.green),
                (None, "Cancel", discord.ButtonStyle.red),
            ),  # type: ignore
            timeout=timeout,
        )
        view.ctx = self
        message = await self.send(message, view=view)
        await view.wait()
        if False in (delete_after_cancel, delete_after_confirm, delete_after_timeout):
            view._children = [view.children[0]]
            for c in view.children:
                if isinstance(c, discord.ui.Button):
                    c.disabled = True
                    if view.value is False:
                        c.label = "Cancelled!"
                        c.emoji = None
                        c.style = discord.ButtonStyle.red
                    elif view.value is True:
                        c.label = "Confirmed!"
                        c.emoji = None
                        c.style = discord.ButtonStyle.green
                    else:
                        c.label = "Timed out!"
                        c.emoji = "⏰"
                        c.style = discord.ButtonStyle.gray
        view.stop()
        if view.value is None:
            try:
                if not return_message:
                    await message.delete() if delete_after_timeout else await message.edit(view=view)
            except (discord.Forbidden, discord.HTTPException):
                pass
            return (None, message) if not delete_after_timeout and return_message else None

        elif view.value:
            try:
                if not return_message:
                    await message.delete() if delete_after_confirm else await message.edit(view=view)
            except (discord.Forbidden, discord.HTTPException):
                pass
            return (True, message) if not delete_after_confirm and return_message else True

        else:
            try:
                if not return_message:
                    (await message.edit(view=view)) if delete_after_cancel is False else (await message.delete())
            except (discord.Forbidden, discord.HTTPException):
                pass

            return (False, message) if delete_after_cancel is False and return_message else False

    async def trigger_typing(self) -> None:
        with suppress(discord.Forbidden, discord.HTTPException):
            await super().typing()

    @property # maybe call bot.is_owner(), but its async so
    def is_bot_owner(self) -> bool:
        return self.author.id in self.bot.owner_ids

    @property
    def reference(self) -> Optional[discord.Message]:
        message = getattr(self.message.reference, "resolved", None)
        return isinstance(message, discord.Message) and message or None

    @property
    def referenced_user(self) -> Optional[discord.abc.User]:
        return getattr(self.reference, "author", None)

    def send_view(self):
        class View(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.add_item(
                    discord.ui.Button(label=f"Sent from {self.guild}", style=discord.ButtonStyle.blurple, disabled=True)
                )
        
        return View()