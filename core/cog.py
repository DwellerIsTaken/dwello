from __future__ import annotations

from discord.ext import commands


class Cog(commands.Cog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ON_TESTING = False
