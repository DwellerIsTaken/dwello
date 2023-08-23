from __future__ import annotations

import asyncio
import random

import discord

from core import Context

CHOICE = [
    "\N{BANKNOTE WITH DOLLAR SIGN}",
    "\N{FIRST PLACE MEDAL}",
    "\N{HUNDRED POINTS SYMBOL}",
    "\N{GEM STONE}",
]


class Slots:
    def __init__(self, *, player: discord.User | discord.Member, bet: int | None = None) -> None:
        self.player = player
        self.bet = bet
        self.emojis = random.choices(CHOICE, k=3)

        self._slot_emoji = discord.PartialEmoji.from_str("<a:SlotsEmoji:923478531873325076>")

    def _display(self, count: int = 3, *emojis: discord.PartialEmoji) -> str:
        return " ".join(str(emoji) for emoji in emojis) + f" {self._slot_emoji}" * count

    @property
    def win(self) -> bool:
        return len(set(self.emojis)) == 1


class SlotsView(discord.ui.View):
    def __init__(self, *, player: discord.User | discord.Member, bet: int | None = None) -> None:
        super().__init__(timeout=60)

        self.slots = Slots(player=player, bet=bet)

        """
        Example:
            view = SlotsView(player=ctx.author, bet=100)
            await view.start(ctx)
        """

    def embed(self, *args) -> discord.Embed:
        # TODO: Beautify this embed
        return discord.Embed(description=f"{self.slots._display(*args)}").set_footer(text=f"{self.slots.player}'s Slots")

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red, emoji="\N{OCTAGONAL SIGN}")
    async def _stop(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer()
        for i in range(3):
            embed = self.embed(3 - i - 1, *self.slots.emojis[:i])
            await interaction.edit_original_response(embed=embed)
            await asyncio.sleep(0.5)
        self.stop()
        self.disable_all()

        await interaction.edit_original_response(
            embed=self.embed(0, *self.slots.emojis),
            view=self,
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.slots.player:
            await interaction.response.send_message(
                "You can't use this button.",
                ephemeral=True,
            )
            return False
        return True

    async def start(self, ctx: Context) -> None:
        self.ctx = ctx
        self.message = await ctx.send(embed=self.embed(3), view=self)

    def disable_all(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

    async def on_timeout(self) -> None:
        self.disable_all()
        if hasattr(self, "message"):
            await self.message.edit(view=self)
