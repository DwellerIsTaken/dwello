from __future__ import annotations

import asyncio
import aiofiles
import datetime
import io
import re
import json
import random
import mimetypes
from typing import Any

import discord
from discord.ext import commands
from discord import app_commands, Interaction, Attachment

import constants as cs
from core import BaseCog, Context, Dwello, Embed
from utils import ENV, resize_discord_file, BlackJackView


Choice = app_commands.Choice

JEYY_KEY = ENV['JEYY_API_KEY']

# could use with app_commands.describe
'''SLASH_PARAM_DESCRIPTIONS = {
    "resize": {
        "attachment": "An image with one of the common image extensions.",
        "width": "Width of an image.",
        "height": "Height of an image.",
    },
    "member": "Any member within this guild."
}'''


class Fun(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)

    # https://developer.spotify.com/dashboard

    @property
    def jeyy_headers(self) -> dict[str, str]:
        return {"accept": "application/json", "Authorization": f"Bearer {JEYY_KEY}"}

    async def retrieve_subreddit(
        self,
        ctx: Context,
        subreddit: str,
        /,
        listing: str = "hot",
        limit: int = 50,
    ) -> dict[str, Any] | Any:
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
            _data: dict[str, Any] = random.choice(data["data"]["children"])["data"]
        except IndexError:
            return await ctx.reply("No subreddit found.", user_mistake=True)

        return _data
    
    @commands.hybrid_command(
        name="blackjack",
        brief="Play a game of blackjack.",
        description="Play a game of blackjack.",
        with_app_command=True,
    )
    async def blackjack(self, ctx: Context, bet: int = 100) -> None:
        """
        Not done yet. Should be a multiplayer. If no player found - play against the bot.
        Maybe put some global bot money at stake. Or put on the items you bought on the global market
        if you don't have enough money or smh.
        """
        view = BlackJackView(player=ctx.author, bet=bet)
        return await view.start(ctx) # multiplayer | and test it beforehand

    @commands.hybrid_command(
        name="gif",
        brief="Returns a requested GIF.",
        description="Returns a requested GIF.",
        aliases=["tenor"],
        with_app_command=True,
    )
    async def gif(self, ctx: Context, *, gif: str = "dankmeme") -> discord.Message | None:
        """
        Returns a GIF from the provided text input.
        If the command encounters an error, it likely originates from the API it relies on.
        This feature can handle various languages in the input text thanks to its integration with Tenor's API.
        """
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

    @commands.hybrid_command(
        name="meme",
        brief="Returns a subreddit meme.",
        description="Returns a subreddit meme.",
        with_app_command=True,
    )
    async def meme(self, ctx: Context) -> discord.Message | None:
        """
        Returns a subreddit (dank)meme.
        Originates from the `reddit` command.
        """
        data = await self.retrieve_subreddit(ctx, "dankmeme")
        if isinstance(data, discord.Message):
            return # could do the error hadling in here instead of that func

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

    @commands.hybrid_command(
        name="reddit",
        brief="Returns a subreddit.",
        description="Returns a subreddit.",
        with_app_command=True,
    )
    async def reddit(self, ctx: Context, subreddit: str) -> discord.Message | None:
        """
        Returns a subreddit of your choosing.
        Sometimes the subreddit can't be found, because it simply doesn't exist.
        But you can just provide a different input (subreddit name) and call it a day.
        If the command encounters an error, it likely originates from the API it relies on.
        This feature uses the original [Reddit API](<https://www.reddit.com/dev/api/>).
        This, free at the moment, API might become chargeable in the future.
        In which case this command might be removed permanently or disabled for a while.
        """
        data: dict[str, Any] = await self.retrieve_subreddit(ctx, subreddit)
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
    # add this everywhere probably ^ | globalize
    # check what it does first
    @commands.hybrid_command(
        name="spotify", # could set in bot.py
        brief="Shows the song member is listening to.",
        description="Shows the song member is listening to.",
        with_app_command=True,
    )
    async def spotify(self, ctx: Context, *, member: discord.Member = commands.Author) -> discord.Message | None:
        """
        This feature lets you see what a member is currently listening to, if that member connected their
        Spotify account to discord.
        If someone isn't listening to anything at the moment, it will let you know.
        But if they are, you'll get a cool preview of the song, complete with the artist's name, song title,
        and when they started listening.
        This cool preview is powered by the [JEYY API](<https://api.jeyy.xyz/dashboard/landing>),
        and I want to give a big shoutout to Jeyy for making this possible. Thanks, Jeyy!
        """
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
        url = "https://api.jeyy.xyz/v2/discord/spotify"
        async with self.bot.http_session.get(url=url, params=params, headers=self.jeyy_headers) as response:
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

    # maybe add difflib later to search based on query or just use some api
    @commands.hybrid_command(
        name="quote",
        brief="Returns a random quote.",
        description="Returns a random quote.",
        with_app_command=True,
    )
    async def quote(self, ctx: Context) -> discord.Message: # *, query: str | None
        """
        Provides a random quote for now, but there's a possibility of integrating an API in the future.
        With this enhancement, you'll be able to specify keywords to find quotes related to your input.
        """
        async with aiofiles.open("storage/datasets/quotes.json") as file:
            data: list = json.loads(await file.read())
        choice: dict = random.choice(data)
        text = choice["quoteText"]
        author = choice.get("quoteAuthor") or "Unknown"
        return await ctx.reply(f'*"{text}"* - **{author}**')
    
    @commands.hybrid_command(
        name="filter",
        brief="Gives chosen effect to member's avatar.",
        description="Gives chosen effect to member's avatar.",
    )
    async def filter(self, ctx: Context, member: discord.Member, option: str) -> discord.Message:
        """
        Applies a filter of your choice to an image. Currently only accepts member's avatar as that image.
        There are currently 83 filters you can apply. I would recommend only using this as a slash command
        since there are currently no complete docs on every option.
        """
        # em, basically store description of each filter in JEYY_DICT too, but display every option on the website instead
        # cause embed will exceed its length otherwise
        if option not in cs.JEY_API_DICT:
            return await ctx.reply(
                "Sorry, we don't have that option. Please use slash command for more optimal use.", user_mistake=True,
            )
        await ctx.defer()
        url = f"https://api.jeyy.xyz/v2/image/{option}?image_url={member.display_avatar.url}"
        async with self.bot.http_session.get(url=url, headers=self.jeyy_headers) as response:
            buffer = io.BytesIO(await response.read())
        return await ctx.reply(file=discord.File(buffer, "filter.gif"))

    @filter.autocomplete("option")
    async def autocomplete_callback_twitch_remove(self, _: discord.Interaction, current: str):
        return await self.bot.autocomplete(current, list(cs.JEY_API_DICT.items()), choice_length=25)
    
    async def _resize(
        self, attachments: list[discord.Attachment | discord.File], _width: int = 500, _height: int = 500,
    ) -> list[discord.File]:
        files: list[discord.File] = []
        for attachment in attachments:
            if isinstance(attachment, discord.File):
                file = attachment
            else:
                file = await attachment.to_file(filename=attachment.filename)
            extension = re.search(r'\.[^.]+$', file.filename) # might need to adjust
            if (extension:= extension.group(0)) not in cs.IMAGE_EXTENSIONS: # check which ones are supported by PIL
                raise ValueError(extension)
            files.append(await asyncio.to_thread(resize_discord_file, file, (_width, _height), extension))
        return files
    
    @app_commands.command(name="resize", description="Resizes an image.")
    #@app_commands.describe(**SPD.get("resize"))
    async def app_resize(self, interaction: Interaction, attachment: Attachment, width: int, height: int) -> discord.Message:
        await interaction.response.defer(thinking=True)
        try:
            files = await self._resize([attachment], width, height)
        except ValueError as ve:
            return await interaction.followup.send(f"Sorry, we currently don't support this file type: {ve}")
        return await interaction.followup.send(files=files)
    
    # maybe a context menu but hard cause you need to provide width and height etc
    @commands.command(name="resize", brief="Resizes an image.")
    async def resize(self, ctx: Context, width: int, height: int) -> discord.Message:
        """
        This command resizes images,
        accepting one attachment with the slash command or multiple (up to 10) images attached to the command prefix,
        including replies and embedded images in messages.
        It utilizes the [PIL](<https://pillow.readthedocs.io/en/stable/>) library
        and processing time may vary based on the number of attachments and bot load.
        """

        # option 1: provide attachments in the same message
        # option 2: reply to a message with attachments
        # option 3: reply to a message with embeds that contain images

        if not (attachments:=ctx.message.attachments):
            if not (reference:= ctx.message.reference):
                return await ctx.reply(
                    "Please reply to the message your image is in or attach images to the command.", user_mistake=True,
                )
            if not (_message:= reference.resolved) or isinstance(_message, discord.DeletedReferencedMessage):
                return await ctx.reply("Couldn't retrieve the message. Please try again with the different one.")
            if not (attachments:= _message.attachments.copy()) and (images:=[embed.image for embed in _message.embeds if embed.image]):  # noqa: E501
                attachments.extend([
                    discord.File(
                        io.BytesIO(
                            await (r:=await self.bot.http_session.get(url)).read()
                        ),
                        filename=f"attachment{i}{mimetypes.guess_extension(r.content_type)}",
                    ) for i, url in enumerate([image.url for image in images])
                ])
            elif not attachments:
                return await ctx.reply(
                    "Sorry, this message contains no attachments. And if it does, then please download it and give it to me."
                )
        await ctx.defer()
        try:
            files = await self._resize(attachments[:10], width, height)
        except ValueError as ve:
            return await ctx.reply(f"Sorry, we currently don't support this file type: {ve}", user_mistake=True)
        
        return await ctx.reply(files=files)