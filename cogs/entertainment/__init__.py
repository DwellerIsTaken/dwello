from __future__ import annotations

from core import Bot

from .fun import Fun


class Entertainment(Fun, name="Entertainment"):
    """
    🎲 Includes commands and tools for entertainment and recreation purposes, such as games, quizzes, memes, music streaming, and other fun features designed to engage and entertain users within the server.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.select_emoji = "🎲"
        self.select_brief = "Commands for providing entertainment and recreational features."


async def setup(bot: Bot):
    await bot.add_cog(Entertainment(bot))
