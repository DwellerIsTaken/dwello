from __future__ import annotations


from core import Bot, Cog


class BotConfig(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
