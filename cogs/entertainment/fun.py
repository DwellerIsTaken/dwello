from __future__ import annotations

import datetime
import io
import random
from typing import Any, Dict, Optional, Union

import discord
from discord import app_commands
from discord.ext import commands

import constants as cs  # noqa: F401

from utils import ENV
from core import BaseCog, Dwello, Context, Embed


class Fun(BaseCog):
    def __init__(self, bot: Dwello) -> None:
        self.bot = bot

    # https://developer.spotify.com/dashboard

    async def retrieve_subreddit(
        self,
        ctx: Context,
        subreddit: str,
        /,
        listing: str = "hot",
        limit: int = 50,
    ) -> Union[Dict[str, Any], Any]:
        async with self.bot.http_session.get(
            f"https://www.reddit.com/r/{subreddit}/{listing}.json?limit={limit}",
            headers={"User-agent": "Discord Bot"},
        ) as response:
            data = await response.json()
        try:
            data["data"]
        except KeyError:
            return await ctx.reply("No subreddit found.", user_mistake=True)  # make an errorhandler for that

        try:
            _data: Dict[str, Any] = random.choice(data["data"]["children"])["data"]
        except IndexError:
            return await ctx.reply("No subreddit found.", user_mistake=True)

        return _data

    @commands.hybrid_command(
        name="gif",
        help="Returns a GIF. | Accepts multiple languages.",
        aliases=["tenor"],
        with_app_command=True,
    )
    async def gif(self, ctx: Context, *, gif: str = "dankmeme") -> Optional[discord.Message]:
        key: str = ENV["TENOR_KEY"]
        limit: int = 1
        ckey: str = self.bot.user.id

        # Docs: https://developers.google.com/tenor/guides/endpoints
        url = f"https://tenor.googleapis.com/v2/search?q={gif}&key={key}&client_key={ckey}&limit={limit}&media_filter=gif&contentfilter=low&random=True"
        async with self.bot.http_session.get(url=url) as response:
            data = await response.json()

        """match response.status:
            case 200:
                pass"""  # <- make a response handler
        if response.status != 200:
            return await ctx.reply("Couldn't connect to the API.", user_mistake=True)

        result = data["results"][0]
        gif_url = result["media_formats"]["gif"]["url"]
        title = result["content_description"]
        item_url = result["itemurl"]

        embed: Embed = Embed(
            title=title,
            type="gifv",
            url=item_url,
        )
        embed.set_image(url=gif_url)
        embed.set_footer(text=f"Powered by Tenor | Tags: {', '.join(result['tags'][:2])}")

        return await ctx.reply(embed=embed)

    @commands.hybrid_command(name="meme", help="Returns a subreddit meme.", with_app_command=True)
    async def meme(self, ctx: Context) -> Optional[discord.Message]:
        data = await self.retrieve_subreddit(ctx, "dankmeme")
        if isinstance(data, discord.Message):
            return

        dt: datetime.datetime = datetime.datetime.utcfromtimestamp(data["created_utc"])
        embed: Embed = Embed(
            title=data["title"],
            url=data["url"],
        )
        embed.add_field(name="Created at", value=discord.utils.format_dt(dt, style="D"))
        embed.add_field(name="Subscribers", value=data["subreddit_subscribers"])
        embed.set_image(url=data["url"])
        embed.set_footer(text=f"Author: {data['author']}")

        return await ctx.reply(embed=embed)

    @commands.hybrid_command(name="reddit", help="Returns a subreddit.", with_app_command=True)
    async def reddit(self, ctx: Context, subreddit: str) -> Optional[discord.Message]:
        data: Dict[str, Any] = await self.retrieve_subreddit(ctx, subreddit)
        if isinstance(data, discord.Message):
            return

        if data["over_18"] and not ctx.channel.is_nsfw() and not await self.bot.is_owner(ctx.author):
            return await ctx.reply(
                "This post is nsfw! I cannot send this in a regular channel!",
                user_mistake=True,
            )

        dt: datetime.datetime = datetime.datetime.utcfromtimestamp(data["created_utc"])
        embed: Embed = Embed(
            title=data["title"],
            url=data["url"],
        )
        embed.add_field(name="Created at", value=discord.utils.format_dt(dt, style="D"))
        embed.add_field(name="Subscribers", value=data["subreddit_subscribers"])
        embed.set_image(url=data["url"])
        embed.set_footer(text=f"Author: {data['author']}")

        return await ctx.reply(embed=embed)

    @commands.guild_only()
    @app_commands.guild_only()
    @app_commands.describe(member="The member of whom you want to see what they are listening too.")
    @commands.hybrid_command(
        name="spotify",
        help="Shows the song member is listening to.",
        with_app_command=True,
    )
    async def spotify(self, ctx: Context, *, member: discord.Member = commands.Author) -> Optional[discord.Message]:
        if ctx.interaction:
            member: discord.Member = ctx.guild.get_member(member.id)
            await ctx.defer()

        spotify: discord.Spotify = discord.utils.find(
            lambda activity: isinstance(activity, discord.Spotify),
            member.activities,
        )
        if not spotify:
            desc: str = f"{member.display_name} isn't listening to Spotify!"
            if ctx.interaction:
                return await ctx.interaction.followup.send(desc)
            return await ctx.reply(desc)

        params: dict[str, Any] = {
            "title": spotify.title,
            "cover_url": spotify.album_cover_url,
            "duration_seconds": spotify.duration.seconds,
            "start_timestamp": spotify.start.timestamp(),
            "artists": spotify.artists,
        }
        async with self.bot.http_session.get("https://api.jeyy.xyz/discord/spotify", params=params) as response:
            buffer = io.BytesIO(await response.read())

        file: discord.File = discord.File(buffer, "spotify.png")
        artists: str = ", ".join(spotify.artists)

        embed: Embed = Embed(description=f"**{spotify.title}** by **{artists}**")
        embed.set_author(
            name=f"{discord.utils.escape_markdown(member.display_name)}'s Spotify",
            url=spotify.track_url,
            icon_url=member.display_avatar.url,
        )
        embed.set_image(url="attachment://spotify.png")
        embed.set_footer(
            text="Powered by Jeyy"
        )  # icon_url="https://logospng.org/download/spotify/logo-spotify-icon-4096.png"

        if ctx.interaction:
            return await ctx.interaction.followup.send(embed=embed, file=file)
        return await ctx.reply(embed=embed, file=file)
