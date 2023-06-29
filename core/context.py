from __future__ import annotations

import asyncio
import functools
from contextlib import suppress
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Callable, Generic, Iterable, TypeVar

import discord
from discord.ext import commands

T = TypeVar("T")


class DwelloContext(commands.Context[commands.Bot], Generic[T]):
    if TYPE_CHECKING:
        from .bot import Dwello

    bot: Dwello

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

    async def send(
        self,
        content: str | None = None,
        *,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        **kwargs: Any,
    ) -> discord.Message | None:
        assert isinstance(self.me, discord.Member)

        perms: discord.Permissions = self.channel.permissions_for(self.me)
        if not (perms.send_messages and perms.embed_links):
            with suppress(discord.Forbidden):
                await self.author.send(
                    (
                        "Bot don't have either Embed Links/Send Messages permission in that channel. "
                        "Please give sufficient permissions to the bot."
                    ),
                    view=self.send_view(), # create that (?)
                )
                return None
        if bold:
            content = f"**{content}**"
        if italic:
            content = f"*{content}*"
        if underline:
            content = f"__{content}__"

        return await super().send(str(content)[:1990] if content else None, **kwargs)

    async def reply(self, content: str | None = None, **kwargs: Any) -> discord.Message | None:
        try: # reply to reference author if there is reference
            return await self.send(content, reference=kwargs.get("reference") or self.message, **kwargs)
        except discord.HTTPException:  # message deleted
            return await self.send(content, **kwargs)

    async def error(self, *args: Any, **kwargs: Any) -> discord.Message | None:
        """Similar to send, but if the original message is deleted, it will delete the error message as well."""
        embed: discord.Embed | None = kwargs.get("embed")
        if isinstance(embed, discord.Embed) and not embed.color:
            # if no color is set, set it to red
            embed.color = discord.Color.red()

        msg: discord.Message | None = await self.reply(
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
