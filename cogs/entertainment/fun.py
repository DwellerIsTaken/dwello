from __future__ import annotations

import discord
import io

from discord.ext import commands

from typing import Any, Optional
from typing_extensions import Self

import constants as cs
from utils import BaseCog
from bot import Dwello, DwelloContext

class Fun(BaseCog):

    def __init__(self: Self, bot: Dwello, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        
    @commands.hybrid_command(name="spotify", help="Shows the song member is listening to.", with_app_command=True)
    async def spotify(self: Self, ctx: DwelloContext, *, member: discord.Member = commands.Author) -> Optional[discord.Message]:
        
        spotify: discord.Spotify | None = discord.utils.find(
            lambda activity: isinstance(activity, discord.Spotify), member.activities,
        )
        if not spotify:
            return await ctx.reply(f"{member.display_name} isn't listening to Spotify!")

        params: dict[str, Any] = {
            "title": spotify.title,
            "cover_url": spotify.album_cover_url,
            "duration_seconds": spotify.duration.seconds,
            "start_timestamp": spotify.start.timestamp(),
            "artists": spotify.artists,
        }
        async with self.bot.session.get("https://api.jeyy.xyz/discord/spotify", params=params) as response:
            bytes = io.BytesIO(await response.read())

        file: discord.File = discord.File(bytes, "spotify.png")
        artists: str = ", ".join(spotify.artists)

        embed: discord.Embed = discord.Embed(description=f"**{spotify.title}** by **{artists}**")
        embed.set_author(
            name=f"{discord.utils.escape_markdown(member.display_name)}'s Spotify",
            url=spotify.track_url,
            icon_url=member.display_avatar.url,
        )
        embed.set_image(url="attachment://spotify.png")
        #embed.set_thumbnail(url="https://logospng.org/download/spotify/logo-spotify-icon-4096.png")

        return await ctx.reply(embed=embed, file=file)