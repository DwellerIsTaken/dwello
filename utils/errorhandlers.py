from __future__ import annotations

import asyncio
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from types import TracebackType

import discord

# copy Leos latest
# __all__: Tuple[str, ...] = ('HandleHTTPException')


# transfer to error.py
# get full code again from repo
class HandleHTTPException(AbstractAsyncContextManager, AbstractContextManager):

    """
    A context manager that handles HTTP exceptions for them to be
    delivered to a destination channel without needing to create
    an embed and send every time.
    This is useful for handling errors that are not critical, but
    still need to be reported to the user.
    Parameters
    ----------
    destination: :class:`discord.abc.Messageable`
        The destination channel to send the error to.
    title: Optional[:class:`str`]
        The title of the embed. Defaults to ``'An unexpected error occurred!'``.
    Attributes
    ----------
    destination: :class:`discord.abc.Messageable`
        The destination channel to send the error to.
    message: Optional[:class:`str`]
        The string to put the embed title in.
    Raises
    ------
    `SilentCommandError`
        Error raised if an HTTPException is encountered. This
        error is specifically ignored by the command error handler.
    """

    __slots__ = ("destination", "message")

    def __init__(self, destination: discord.abc.Messageable, *, title: str | None = None):
        self.destination = destination
        self.message = title

    def __enter__(self):
        return self

    async def __aenter__(self):
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> bool:
        # log.warning(
        #'Context manager HandleHTTPException was used with `with` statement.'
        #'\nThis can be somewhat unreliable as it uses create_task, '
        #'please use `async with` syntax instead.'
        # )

        if exc_val is not None and isinstance(exc_val, discord.HTTPException) and exc_type is not None:
            embed = discord.Embed(
                title=self.message or "An unexpected error occurred!",
                description=f"{exc_type.__name__}: {exc_val.text}",
                colour=discord.Colour.red(),
            )

            loop = asyncio.get_event_loop()
            loop.create_task(self.destination.send(embed=embed))
            # raise SilentCommandError
        return False

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> bool:
        if exc_val is not None and isinstance(exc_val, discord.HTTPException) and exc_type:
            embed = discord.Embed(
                title=self.message or "An unexpected error occurred!",
                description=f"{exc_type.__name__}: {exc_val.text}",
                colour=discord.Colour.red(),
            )

            await self.destination.send(embed=embed)
            # raise SilentCommandError

        return False
