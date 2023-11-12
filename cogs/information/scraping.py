from __future__ import annotations

import contextlib
import difflib
import json
import re
from typing import TYPE_CHECKING, Any

import aiofiles
import discord
import wikipediaapi
from aiospotify import Artist, Image, ObjectType, PartialAlbum, SearchResult, SpotifyClient, Track, http
from datetime import datetime
from discord import app_commands
from discord.ext import commands
from typing_extensions import Self
from yarl import URL

import constants as cs
from core import BaseCog, Context, Dwello, Embed
from utils import ENV, DefaultPaginator, capitalize_greek_numbers, get_unix_timestamp

if TYPE_CHECKING:
    from discord import Interaction

mk = discord.utils.escape_markdown

TMDB_KEY = ENV["TMDB_API_TOKEN"]
STEAM_KEY = ENV["STEAM_API_KEY"]
WEATHER_KEY = ENV["OPENWEATHERMAP_KEY"]
SPOTIFY_CLIENT_ID = ENV["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = ENV["SPOTIFY_CLIENT_SECRET"]
UNSPLASH_DEMO_ACCESS_KEY = ENV["UNSPLASH_DEMO_ACCESS_KEY"]

# create simple response handler class


# not sure what this is
class OptionSelectView(discord.ui.View):
    def __init__(
        self,
        ctx: Context,
        options: list[tuple[str, Embed]],
    ) -> None:
        super().__init__()
        self.ctx = ctx
        self.options = options
        self.embeds: list[Embed] = [embed[1] for embed in options]

        self.main_embed = self.embeds[0]

    @discord.ui.select(placeholder="Select a category", row=0)
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        print(select.values)
        return await interaction.response.edit_message(embed=select.values[0], view=self)

    def build_select(self: Self) -> None:
        self.category_select.options = []

        for label, embed in self.options:
            self.category_select.add_option(label=label, value=embed, emoji="\N{HOUSE BUILDING}")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user == self.ctx.author:
            return True
        await interaction.response.defer()
        return False

    async def on_timeout(self: Self) -> None:
        self.clear_items()
        await self.message.edit(view=self)

    async def start(self: Self) -> discord.Message | None:
        self.build_select()
        self.message = await self.ctx.send(embed=self.main_embed, view=self)


class Scraping(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)

        self.spotify_client: SpotifyClient = SpotifyClient(
            SPOTIFY_CLIENT_ID,
            SPOTIFY_CLIENT_SECRET,
            session=self.bot.http_session,
        )

        # for some reason user_agent is a required argument on the laptop
        # but not on the pc (for me at least)
        with contextlib.suppress(TypeError):
            self.wiki: wikipediaapi.Wikipedia = wikipediaapi.Wikipedia(
                language="en",
                headers=self.wiki_headers,
            )

    @property
    def tmdb_key(self: Self) -> str:
        return TMDB_KEY

    @property
    def tmdb_headers(self: Self) -> dict[str, str]:
        return {
            "accept": "application/json",
            "Authorization": f"Bearer {self.tmdb_key}",
        }

    @property
    def spotify_http_client(self: Self) -> http.HTTPClient:
        return self.spotify_client.http

    @property
    def wiki_user_agent(self) -> str:
        return "CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org)"

    @property
    def wiki_headers(self) -> dict[str, str]:
        return {"User-Agent": self.wiki_user_agent}

    # apply for production rate of unsplash api (5k req/h)
    @commands.hybrid_command(
        name="image",
        aliases=["images"],
        brief="Returns the requested image.",
        description="Returns the requested image.",
    )
    async def image(self, ctx: Context, *, image: str = None) -> discord.Message | None:
        """
        Returns the requested image, otherwise - a random image.
        This command might have some issues due to usage of [Unsplash API](<https://unsplash.com/developers>)
        which only accepts a certain amount of requests per hour. Also, this API might be a temporary solution
        for this application.
        """

        url: URL = "https://api.unsplash.com/photos/random"

        headers = {
            "Authorization": f"Client-ID {UNSPLASH_DEMO_ACCESS_KEY}",
        }

        params = {
            "query": image,
        } if image else None

        async with self.bot.http_session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()

            elif response.status >= 400:
                return await ctx.reply(
                    f"Something went wrong while trying to get an image for {mk(image)}",
                )

        embed = Embed(
            title=data["alt_description"].capitalize(),
            url=data["links"]["download"],
            description=f"Photo by [{data['user']['name']}]({data['user']['links']['html']}) on [Unsplash](https://unsplash.com)",
        ).set_image(url=data["urls"]["regular"])

        return await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="album",
        aliases=["albums"],
        brief="Returns the requested album.",
        description="Returns the requested album.",
    )
    async def album(self, ctx: Context, *, album: str) -> discord.Message | None:
        """
        Returns an embed paginator containing multiple albums that closely match your input.
        **Note**: This command uses 3rd party python library which isn't completely finished at the moment
        and might cause some trouble in the future.
        """ # cant find the lib link

        data: SearchResult = await self.spotify_client.search(query=album, types=[ObjectType.Album], limit=5)

        albums: list[dict[str, Any]] = data._data["albums"]["items"]
        if not albums:
            return await ctx.reply(
                f"Can't find any albums by the name of *{mk(album, as_needed=False)}*",
                user_mistake=True,
            )
        embeds: list[Embed] = []
        for album in albums:
            album: dict[str, Any]  # = albums[0]

            _id = album["id"]
            name = album["name"]
            release_date = album["release_date"]
            link = album["external_urls"]["spotify"]
            image_url = album["images"][1]["url"] if album["images"] else None

            artists = [(artist["name"], artist["external_urls"]["spotify"]) for artist in album["artists"]][:2]

            try:
                timestamp = get_unix_timestamp(release_date, "%Y-%m-%d", style="d")
            except ValueError:
                timestamp = release_date
            embed = (
                Embed(
                    title=name,
                    url=link,
                )
                .set_thumbnail(url=image_url)
                .add_field(name="Release Date", value=timestamp, inline=False)
                .add_field(
                    name="Artist" if len(artists) == 1 else "Artists",
                    value="\n".join([f"> [{i[0].title()}]({i[1]})" for i in artists]),
                )
            )
            tracks_data: dict[str, Any] = await self.spotify_http_client.get_album_tracks(id=_id, market="US", limit=5)

            if tracks := tracks_data["items"]:
                embed.add_field(
                    name="Tracks",
                    value="\n".join([f"> [{track['name']}]({track['external_urls']['spotify']})" for track in tracks]),
                )
            embeds.append(embed)

        return await DefaultPaginator.start(ctx, embeds)

    @commands.hybrid_command(
        name="artist",
        aliases=["artists"],
        brief="Returns the requested artist.",
        description="Returns the requested artist.",
    )
    async def artist(self, ctx: Context, *, artist: str) -> discord.Message | None:
        """
        Returns an embed paginator containing multiple artists that closely match your input.
        **Note**: This command uses 3rd party python library which isn't completely finished at the moment
        and might cause some trouble in the future.
        """

        data: SearchResult = await self.spotify_client.search(query=artist, types=[ObjectType.Artist], limit=5)

        artists: list[Artist] = data.artists.items
        if not artists:
            return await ctx.reply(
                f"Can't find any artists by the name of *{mk(artist, as_needed=False)}*",
                user_mistake=True,
            )
        
        # making too many requests here. maybe smh else?
        embeds: list[Embed] = []
        for artist in artists:
            artist: Artist
            album_data: dict[str, Any] = await self.spotify_http_client.get_artist_albums(
                id=artist.id, include_groups=["album"], market="US", limit=5
            )

            tracks_data: dict[str, Any] = await self.spotify_http_client.get_artist_top_tracks(id=artist.id, market="US")

            albums = album_data["items"]

            unique_albums = sorted(albums, key=lambda x: x["name"].split(" (")[0])
            unique_albums = [
                album
                for i, album in enumerate(unique_albums)
                if all(album["name"].split(" (")[0].lower() not in a["name"].lower() for a in unique_albums[:i])
            ]

            album_names = [re.sub(r"\([^()]+\)", "", album["name"]).strip().lower() for album in unique_albums[:3]]
            album_names.sort(key=lambda x: len(x))

            sorted_unique_albums = sorted(
                unique_albums[:3],
                key=lambda x: album_names.index(re.sub(r"\([^()]+\)", "", x["name"]).strip().lower()),
            )
            album_tuples = [
                (capitalize_greek_numbers(name.title()), album["external_urls"]["spotify"])
                for name, album in zip(album_names, sorted_unique_albums)
            ]

            tracks: list[dict[str, Any]] = tracks_data["tracks"]
            top_tracks = sorted(tracks, key=lambda x: x["popularity"], reverse=True)

            _description = f"**Followers**: {artist.followers.total:,}\n**Genres**: " + ", ".join(list(artist.genres[:2]))
            embed = (
                Embed(
                    title=artist.name,
                    url=artist.external_urls.spotify,
                    description=_description,
                )
                .add_field(
                    name="Top Albums",
                    value="\n".join(f"> [{name}]({url})" for name, url in album_tuples),
                )
                .add_field(
                    name="Top Tracks",
                    value="\n".join(f"> [{track['name']}]({track['external_urls']['spotify']})" for track in top_tracks[:3]),
                )
            )
            image: Image = artist.images[1] if artist.images else None
            if image:
                embed.set_thumbnail(url=image.url)
            embeds.append(embed)

        return await DefaultPaginator.start(ctx, embeds)

    @commands.hybrid_command(
        name="playlist",
        aliases=["playlists"],
        brief="Returns the requested playlist.",
        description="Returns the requested playlist.",
    )
    async def playlist(self, ctx: Context, *, playlist: str) -> discord.Message | None:
        """
        Returns an embed paginator containing multiple playlists that closely match your input.
        **Note**: This command uses 3rd party python library which isn't completely finished at the moment
        and might cause some trouble in the future.
        """

        data: SearchResult = await self.spotify_client.search(query=playlist, types=[ObjectType.Playlist], limit=5)

        playlists: list[dict[str, Any]] = data._data["playlists"]["items"]
        if not playlists:
            return await ctx.reply(
                f"Can't find any playlists by the name of *{mk(playlist, as_needed=False)}*",
                user_mistake=True,
            )
        
        embeds: list[Embed] = []
        for playlist in playlists:
            name = playlist["name"]
            url = playlist["external_urls"]["spotify"]
            total_tracks = playlist["tracks"]["total"]
            owner_name = playlist["owner"]["display_name"]
            owner_url = playlist["owner"]["external_urls"]["spotify"]
            image_url = playlist["images"][0]["url"] if playlist["images"] else None
            description = playlist["description"] or None

            embed = (
                Embed(
                    title=name,
                    url=url,
                    description=description,
                )
                .add_field(name="Owner", value=f"[{owner_name}]({owner_url})")
                .add_field(name="Total Tracks", value=total_tracks)
            )
            if image_url:
                embed.set_thumbnail(url=image_url)
            embeds.append(embed)

        return await DefaultPaginator.start(ctx, embeds)

    @commands.hybrid_command(
        name="track",
        aliases=["tracks"],
        brief="Returns the requested track.",
        description="Returns the requested track.",
    )
    async def track(self, ctx: Context, *, track: str) -> discord.Message | None:
        """
        Returns an embed paginator containing multiple ptracks that closely match your input.
        **Note**: This command uses 3rd party python library which isn't completely finished at the moment
        and might cause some trouble in the future.
        """

        data: SearchResult = await self.spotify_client.search(query=track, types=[ObjectType.Track], limit=5)

        tracks: list[Track] = data.tracks.items
        if not tracks:
            return await ctx.reply(
                f"Can't find any tracks by the name of *{mk(track, as_needed=False)}*",
                user_mistake=True,
            )

        embeds: list[Embed] = []
        for _track in tracks:
            _album: PartialAlbum = _track.album
            _artists: list[tuple[str, str]] = [(artist.name, artist.external_urls.spotify) for artist in _track.artists][:2]

            duration_in_minutes = _track.duration / 1000 / 60

            duration_str = (
                f"**Duration**: {f'{duration_in_minutes:.2f}'} min"
                if duration_in_minutes >= 1
                else f"{_track.duration / 1000:.2f}" + " sec"
            )

            release_str = "\n**Release Date**: "
            try:
                release_str += get_unix_timestamp(_album.release_date.date, "%Y-%m-%d", style="d")
            except ValueError:
                release_str += _album.release_date.date

            embed = (
                Embed(
                    title=_track.name,
                    url=f"https://open.spotify.com/track/{_track.id}",
                    description=duration_str + release_str,
                )
                .add_field(
                    name="Artist" if len(_artists) == 1 else "Artists",
                    value="\n".join([f"> [{i[0].title()}]({i[1]})" for i in _artists]),
                )
                .add_field(name="Album", value=f"[{_album.name}]({_album.external_urls.spotify})")
            )
            image: Image = _album.images[1] if _album.images else None
            if image:
                embed.set_thumbnail(url=image.url)
            embeds.append(embed)

        return await DefaultPaginator.start(ctx, embeds)

    async def get_game_by_name(self, name: str) -> int:
        url: URL = "http://api.steampowered.com/ISteamApps/GetAppList/v2/"
        async with self.bot.http_session.get(url=url) as response:
            data = await response.json()

        # await with ResponseHandler(response.status):
        # etc

        if response.status != 200:
            raise discord.HTTPException
        game_list = data["applist"]["apps"]

        for game in game_list:
            if game["name"].lower() == name.lower():
                return game["appid"]

        raise commands.BadArgument(f"Couldn't find a game by the name *{mk(name)}*")

    @commands.hybrid_command(
        name="game",
        aliases=["games"],
        brief="Returns the requested game.",
        description="Returns the requested game.",
    )
    async def game(self, ctx: Context, *, game: str) -> discord.Message | None:
        """
        This command searches and returns a game that matches your input.
        Since it's powered by official [Steam API](<https://steamcommunity.com/dev>),
        which is obviously shit at the moment, the responses may be limited.
        We apologize for any inconvenience and hope to switch to a new API soon.
        """
        #shitty API
        # cant really paginate with that api
        game_id = await self.get_game_by_name(game)

        url: URL = f"https://store.steampowered.com/api/appdetails?appids={game_id}&l=en"
        async with self.bot.http_session.get(url=url) as response:
            data = await response.json()

        if response.status != 200:
            return await ctx.reply("Couldn't connect to the API.", user_mistake=True)

        data = data[str(game_id)]["data"]

        name = data["name"]
        devs = data["developers"]
        website = data["website"]
        thumbnail = data["header_image"]
        metaurl = data["metacritic"]["url"]
        metascore = data["metacritic"]["score"]
        short_description = data["short_description"]
        price = data["price_overview"]["final_formatted"]

        embed = (
            Embed(
                title=name,
                url=website,
                description=short_description,
            )
            .set_thumbnail(url=thumbnail)
            .add_field(name="Metascore", value=f"[{metascore}]({metaurl})")
            .add_field(
                name="Price",
                value=f"[{price}](https://store.steampowered.com/app/{game_id})",
            )
            .add_field(name="Developed by", value=", ".join(devs[:3]), inline=False)
        )

        return await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="actor", # maybe just use search or smh
        aliases=["actors", "actress", "actresses"],
        brief="Displays a figure recognized in the movie industry.",
        description="Displays a figure recognized in the movie industry.",
    )
    async def movie_person(self, ctx: Context, *, person: str) -> discord.Message | None:
        """
        Reveals an individual with recognition in the film industry, encompassing roles beyond actors and actresses.
        This command currently utilizes the [TMDB API](<https://developer.themoviedb.org/docs>) which, unfortunately,
        lacks access to the requested person's birthdate. To address this limitation, we have integrated the 3rd party
        [Wikipedia-API](<https://pypi.org/project/Wikipedia-API/>) library to provide a brief biography of the person.
        Consequently, this command may require additional time to complete.
        """

        pages: int = 1
        url: URL = (
            f"https://api.themoviedb.org/3/search/person?query={person}&include_adult=True&language=en-US&page={pages}"
        )
        async with self.bot.http_session.get(url=url, headers=self.tmdb_headers) as response:
            data = await response.json()

        if response.status != 200:
            return await ctx.reply("Couldn't connect to the API.", user_mistake=True)

        try:
            people = sorted(data["results"], key=lambda person: person["popularity"], reverse=True)[:5]
            if len(people) == 0:
                raise ValueError

        except ValueError:
            return await ctx.reply(f"Couldn't find a person by the name of {person}.", user_mistake=True)
        
        embeds: list[Embed] = []
        for _person in people:
            # its gonna be (a lot of) requests
            page: wikipediaapi.WikipediaPage = self.wiki.page(_person["name"])
            gender = "Male" if _person["gender"] == 2 else "Female"
            top_movies = list(_person["known_for"])

            embed = (
                Embed(
                    title=_person["original_name"],
                    description=f"{page.summary[:500]}..." if len(page.summary) > 500 else "",
                    url=f"https://www.themoviedb.org/person/{_person['id']}",
                )
                .add_field(name="Gender", value=gender)
                .add_field(name="Department", value=_person["known_for_department"])
            )

            if top_movies_desc := "".join(
                f"\n• [{movie['title']}](https://www.themoviedb.org/movie/{movie['id']})" for movie in top_movies
            ):
                embed.add_field(name="Top Movies", value=top_movies_desc, inline=False)

            if _person["profile_path"]:
                embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{_person['profile_path']}")

            embed.set_footer(text=f"Popularity: {_person['popularity']}")
            embeds.append(embed)

        return await DefaultPaginator.start(ctx, embeds)

    @commands.command(
        name="movie",
        brief="Returns the requested movie by title.",
        aliases=["film", "films", "movies"],
    )
    async def movie(self, ctx: Context, *, movie: str) -> discord.Message | None:
        """
        Provides the requested movie while omitting TV shows to ensure a more precise response.
        For TV shows, please utilize `show` command. **Note**: This command utilizes [TMDB API](<https://developer.themoviedb.org/docs>)
        that might become unresponsive once the request threshold is reached.
        """

        pages: int = 1
        url: URL = f"https://api.themoviedb.org/3/search/movie?query={movie}&include_adult=True&language=en-US&page={pages}"
        async with self.bot.http_session.get(url=url, headers=self.tmdb_headers) as response:
            data = await response.json()

        if response.status != 200:
            return await ctx.reply("Couldn't connect to the API.", user_mistake=True)

        try:
            movies = sorted(data["results"], key=lambda _movie: _movie["vote_count"], reverse=True)[:5]
            if len(movies) == 0:
                raise ValueError

        except ValueError:
            return await ctx.reply(f"Couldn't find a movie by the name of {movie}.", user_mistake=True)
        
        embeds: list[Embed] = []
        for _movie in movies:
            embed = (
                Embed(
                    title=_movie["title"],
                    description=_movie["overview"],
                    url=f"https://www.themoviedb.org/movie/{_movie['id']}",
                )
                .add_field(
                    name="Release Date",
                    value=get_unix_timestamp(_movie["release_date"], "%Y-%m-%d", style="d"),
                )
                .add_field(name="Vote Average", value=f"{str(_movie['vote_average'])[:3]} / 10")
                .add_field(name="Vote Count", value=_movie["vote_count"])
            )

            if _movie["poster_path"]:
                embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{_movie['poster_path']}")

            embed.set_footer(text=f"Popularity: {_movie['popularity']}")
            embeds.append(embed)

        return await DefaultPaginator.start(ctx, embeds)

    @app_commands.command(name="movie", description="Returns the requested movie by title.")
    async def _movie(self, interaction: Interaction, *, movie: str, year: int = None) -> discord.Message | None:
        """
        Provides the requested movie while omitting TV shows to ensure a more precise response.
        For TV shows, please utilize `show` command. **Note**: This command utilizes [TMDB API](<https://developer.themoviedb.org/docs>)
        that might become unresponsive once the request threshold is reached.
        """

        pages: int = 1
        url: URL = f"https://api.themoviedb.org/3/search/movie?query={movie}&include_adult=True&language=en-US&primary_release_year={year}&page={pages}"

        if not year:
            url = f"https://api.themoviedb.org/3/search/movie?query={movie}&include_adult=True&language=en-US&page={pages}"

        async with self.bot.http_session.get(url=url, headers=self.tmdb_headers) as response:
            data = await response.json()

        if response.status != 200:
            return await interaction.response.send_message("Couldn't connect to the API.", ephemeral=True)

        try:
            movies = sorted(data["results"], key=lambda _movie: _movie["vote_count"], reverse=True)[:5]
            if len(movies) == 0:
                raise ValueError

        except ValueError:
            return await interaction.response.send_message(
                f"Couldn't find a movie by the name of {movie}.", ephemeral=True
            )

        embeds: list[Embed] = []

        for _movie in movies:
            embed = (
                Embed(
                    title=_movie["title"],
                    description=_movie["overview"],
                    url=f"https://www.themoviedb.org/movie/{_movie['id']}",
                )
                .add_field(
                    name="Release Date",
                    value=get_unix_timestamp(_movie["release_date"], "%Y-%m-%d", style="d"),
                )
                .add_field(name="Vote Average", value=f"{str(_movie['vote_average'])[:3]} / 10")
                .add_field(name="Vote Count", value=_movie["vote_count"])
            )

            if _movie["poster_path"]:
                embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{_movie['poster_path']}")

            embed.set_footer(text=f"Popularity: {_movie['popularity']}")
            embeds.append(embed)

        return await DefaultPaginator.start(interaction, embeds)

    @commands.command(name="show", brief="Returns a TV show by its title.", aliases=["series", "shows"])
    async def show(self, ctx: Context, *, show: str) -> discord.Message | None:
        """
        Provides the requested tv-show while omitting movies to ensure a more precise response.
        For movies, please utilize `movie` command. **Note**: This command utilizes [TMDB API](<https://developer.themoviedb.org/docs>)
        that might become unresponsive once the request threshold is reached.
        """

        pages: int = 1
        url: URL = f"https://api.themoviedb.org/3/search/tv?query={show}&include_adult=True&language=en-US&page={pages}"
        async with self.bot.http_session.get(url=url, headers=self.tmdb_headers) as response:
            data = await response.json()

        if response.status != 200:
            return await ctx.reply("Couldn't connect to the API.", user_mistake=True)

        try:
            shows = sorted(data["results"], key=lambda _show: _show["vote_count"], reverse=True)[:5]
            if len(shows) == 0:
                raise ValueError
            
        except ValueError:
            return await ctx.reply(f"Couldn't find a show by the name of {show}.", user_mistake=True)

        embeds: list[Embed] = []

        for _show in shows:
            embed = (
                Embed(
                    title=_show["original_name"],
                    description=_show["overview"],
                    url=f"https://www.themoviedb.org/tv/{_show['id']}",
                )
                .add_field(
                    name="Release Date",
                    value=get_unix_timestamp(_show["first_air_date"], "%Y-%m-%d", style="d"),
                )
                .add_field(name="Vote Average", value=f"{str(_show['vote_average'])[:3]} / 10")
                .add_field(name="Vote Count", value=_show["vote_count"])
            )

            if _show["poster_path"]:
                embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{_show['poster_path']}")

            embed.set_footer(text=f"Popularity: {_show['popularity']}")
            embeds.append(embed)

        return await DefaultPaginator.start(ctx, embeds)

    @app_commands.command(name="show", description="Returns a TV show by its title.")
    async def _show(self, interaction: Interaction, *, show: str, year: int = None) -> discord.Message | None:
        """
        Provides the requested tv-show while omitting movies to ensure a more precise response.
        For movies, please utilize `movie` command. **Note**: This command utilizes [TMDB API](<https://developer.themoviedb.org/docs>)
        that might become unresponsive once the request threshold is reached.
        """

        pages: int = 1

        url = f"https://api.themoviedb.org/3/search/tv?query={show}&include_adult=True&language=en-US&primary_release_year={year}&page={pages}"

        if not year:
            url = f"https://api.themoviedb.org/3/search/tv?query={show}&include_adult=True&language=en-US&page={pages}"

        async with self.bot.http_session.get(url=url, headers=self.tmdb_headers) as response:
            data = await response.json()

        if response.status != 200:
            return await interaction.response.send_message("Couldn't connect to the API.", ephemeral=True)

        try:
            shows = sorted(data["results"], key=lambda _show: _show["vote_count"], reverse=True)[:5]
            if len(shows) == 0:
                raise ValueError
            
        except ValueError:
            return await interaction.response.send_message(f"Couldn't find a show by the name of {show}.", ephemeral=True)

        embeds: list[Embed] = []

        for _show in shows:
            embed = (
                Embed(
                    title=_show["original_name"],
                    description=_show["overview"],
                    url=f"https://www.themoviedb.org/tv/{_show['id']}",
                )
                .add_field(
                    name="Release Date",
                    value=get_unix_timestamp(_show["first_air_date"], "%Y-%m-%d", style="d"),
                )
                .add_field(name="Vote Average", value=f"{str(_show['vote_average'])[:3]} / 10")
                .add_field(name="Vote Count", value=_show["vote_count"])
            )

            if _show["poster_path"]:
                embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{_show['poster_path']}")

            embed.set_footer(text=f"Popularity: {_show['popularity']}")
            embeds.append(embed)

        return await DefaultPaginator.start(interaction, embeds)

    @commands.hybrid_command(
        name="weather",
        brief="Shows the temparature in the requested location.",
        description="Shows the temparature in the requested location.",
    )
    async def weather(self, ctx: Context, *, city: str) -> discord.Message | None:
        """
        Displays the temperature in both Celsius and Fahrenheit for the location you specify,
        which can be a country, city, or region.
        This functionality relies on the [OpenWeatherMap API](<https://openweathermap.org/api>),
        and it's important to note that it may approach the API's request limit.
        """

        if not city: # missing param error triggered, so this check is useless
            return await ctx.reply("Please provide a city or a contry.", mention_author=True)

        _location = city.lower()

        async with self.bot.http_session.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={_location}&APPID={WEATHER_KEY}&units=metric"
        ) as response:
            data = await response.json()

        if data["cod"] == "404":
            # please don't use this... find a way for openweathermap to return a similair city maybe,
            # or just use another api to get similair matches
            async with aiofiles.open("storage/datasets/countries.json") as file:
                data: dict = json.loads(await file.read())

            matches = []
            for key, value in data.items():
                if country_match := difflib.get_close_matches(_location, [key]):
                    matches.append(country_match[0])
                elif city_matches := difflib.get_close_matches(_location, value):
                    matches.append(city_matches[0])

            clean_matches = difflib.get_close_matches(_location, matches, 5)

            description = "Please check the spelling and try again."
            if clean_matches:
                description = "**Did you mean...**\n"
                for match in clean_matches:
                    description += f"\n{match}"

            matches_embed = Embed(
                description=f"Sorry, but I couldn't recognise the city **{_location.title()}**." f"\n{description}",
                color=cs.WARNING_COLOR,
            )
            return await ctx.reply(embed=matches_embed, mention_author=True)

        curr_temp_celsius = data["main"]["temp"]
        curr_feels_like_celsius = data["main"]["feels_like"]

        curr_temp_fahrenheit = (curr_temp_celsius * 9 / 5) + 32
        curr_feels_like_fahrenheit = (curr_feels_like_celsius * 9 / 5) + 32

        payload = (
            f"Right now it is **{curr_temp_celsius} °C** / **{curr_temp_fahrenheit:.2f} °F**.\n"
            f"But it feels like **{curr_feels_like_celsius} °C** / **{curr_feels_like_fahrenheit:.2f} °F**.\n"
        )

        weather_embed = (
            Embed(
                title=f"Current weather in {data['name']}",
                description=payload,
                color=discord.Colour.blurple(),
            )
            .set_footer(text="Powered by OpenWeatherMap")
            .set_thumbnail(url=f"http://openweathermap.org/img/w/{data['weather'][0]['icon']}.png")
            .add_field(
                name="Location",
                value=f"{data['name']}, {data['sys']['country']}",
                inline=False,
            )
            .add_field(
                name="Weather",
                value=data["weather"][0]["description"].title(),
                inline=False,
            )
            .add_field(name="Humidity", value=f"{data['main']['humidity']}%", inline=True)
            .add_field(name="Wind", value=f"{data['wind']['speed']} m/s", inline=True)
            .add_field(name="Pressure", value=f"{data['main']['pressure']} hPa", inline=True)
        )

        return await ctx.reply(embed=weather_embed, ephemeral=False)
    
    @commands.hybrid_command(
        name="urban",
        brief="Searches urban dictionary.",
        description="Searches urban dictionary.",
    )
    async def _urban(self, ctx: Context, *, word: str = None):
        """Searches urban dictionary."""

        url = 'http://api.urbandictionary.com/v0/define' if word else "https://api.urbandictionary.com/v0/random"
        async with ctx.bot.http_session.get(url, params={'term': word} if word else None) as resp:
            if resp.status != 200:
                return await ctx.send(f'An error occurred: {resp.status} {resp.reason}') # not a very good handler haha

            js = await resp.json()
            data = js.get('list', [])
            if not data:
                return await ctx.send('No results found, sorry.')

        embeds: list[Embed] = [
            Embed(
                title=f"Word: {i['word']}",
                timestamp=datetime.strptime(i['written_on'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                description=(
                    f"**Definition**\n{i['definition']}\n\n"
                    f"**Example**\n{i['example']}"
                )[:4096]
            )
            .set_author(name="Urban Dictionary", url=i['permalink']).set_footer(text=f"by {i['author']}")
            .add_field(
                name="Votes",
                value=f"\N{THUMBS UP SIGN}: {i['thumbs_up']}  \N{THUMBS DOWN SIGN}: {i['thumbs_down']}",
                inline=False,
            )
            for i in data[:5]
        ]
        return await DefaultPaginator.start(ctx, embeds)



