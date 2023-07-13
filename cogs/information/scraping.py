from __future__ import annotations

import difflib
import json
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import discord
import wikipediaapi
from aiospotify import Artist, Image, ObjectType, PartialAlbum, SearchResult, SpotifyClient, Track, http
from discord import app_commands
from discord.ext import commands
from typing_extensions import Self
from yarl import URL

import constants as cs
from core import BaseCog, Dwello, DwelloContext
from utils import ENV, capitalize_greek_numbers, get_unix_timestamp

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


class GameNotFound(Exception):  # <- look into it
    def __init__(self, game_id: Union[int, str] = None):
        self.game_id = game_id
        error_message = "Game not found"
        if game_id is not None:
            error_message += f" with ID: {game_id}"
        super().__init__(error_message)


class OptionSelectView(discord.ui.View):
    def __init__(
        self,
        ctx: DwelloContext,
        options: List[Tuple[str, discord.Embed]],
    ):
        super().__init__()
        self.ctx = ctx
        self.options = options
        self.embeds: List[discord.Embed] = [embed[1] for embed in options]

        self.main_embed = self.embeds[0]
        print(self.embeds)
        print("\n\n", self.main_embed)

    @discord.ui.select(placeholder="Select a category", row=0)
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        print(select.values)
        return await interaction.response.edit_message(embed=select.values[0], view=self)

    def build_select(self: Self) -> None:
        self.category_select.options = []

        for label, embed in self.options:
            self.category_select.add_option(label=label, value=embed, emoji="🏠")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user == self.ctx.author:
            return True
        await interaction.response.defer()
        return False

    async def on_timeout(self: Self) -> None:
        self.clear_items()
        await self.message.edit(view=self)

    async def start(self: Self) -> Optional[discord.Message]:
        self.build_select()
        self.message = await self.ctx.send(embed=self.main_embed, view=self)


class Scraping(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)
        self.bot = bot

        self.spotify_client: SpotifyClient = SpotifyClient(
            SPOTIFY_CLIENT_ID,
            SPOTIFY_CLIENT_SECRET,
            session=self.bot.http_session,
        )

        self.wiki: wikipediaapi.Wikipedia = wikipediaapi.Wikipedia(
            language="en",
            headers=self.wiki_headers,
        )

    @property
    def tmdb_key(self: Self) -> str:
        return TMDB_KEY

    @property
    def tmdb_headers(self: Self) -> Dict[str, str]:
        return {
            "accept": "application/json",
            "Authorization": f"Bearer {self.tmdb_key}",
        }

    @property
    def spotify_http_client(self: Self) -> http.HTTPClient:
        return self.spotify_client.http

    @property
    def wiki_headers(self) -> Dict[str, str]:
        return {"User-Agent": "CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org)"}

    """@property
    def spotify_headers(self: Self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.spotify_token}"}"""

    """async def get_spotify_access_token(self: Self) -> Tuple[str, int]:

        client_id: str = get_or_fail('SPOTIFY_CLIENT_ID')
        client_secret: str = get_or_fail('SPOTIFY_CLIENT_SECRET')

        #client: aiospotify.SpotifyClient = aiospotify.SpotifyClient(client_id, client_secret)

        auth_bytes: bytes = f"{client_id}:{client_secret}".encode("utf-8")
        auth_base = str(base64.b64encode(auth_bytes), "utf-8")

        auth_url: URL = "https://accounts.spotify.com/api/token"
        auth_headers: Dict[str, str] = {
            "Authorization": "Basic " + auth_base,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        auth_data: Dict[str, str] = {"grant_type": "client_credentials"}
        async with self.bot.http_session.post(url=auth_url, headers=auth_headers, data=auth_data) as response:
            data: Any = await response.json()

        match response.status:
            case 200:
                _token = data['access_token']
                _expires = data['expires_in']
            case 400:
                return "The request was invalid or malformed. This could be due to missing or incorrect parameters."
            case 401:
                return "The request lacks valid authentication credentials." # temp
            case 403:
                return "The server understood the request, but you are not allowed to access the requested resource."

        self.spotify_token = _token
        return _token, _expires"""

    """@commands.command()
    async def test(self, ctx: DwelloContext):
        message = await ctx.author.fetch_message(1119035015842504744)
        return await ctx.reply(message.content)"""

    @commands.hybrid_command(
        name="image",
        help="Returns an image.",
        aliases=["images"],
        with_app_command=True,
    )
    async def image(self, ctx: DwelloContext, *, image: str) -> Optional[discord.Message]:
        url: URL = "https://api.unsplash.com/photos/random"

        headers = {
            "Authorization": f"Client-ID {UNSPLASH_DEMO_ACCESS_KEY}",
        }

        params = {
            "query": image,
        }

        async with self.bot.http_session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()

            elif response.status == 401:
                print("Unauthorized: Please check your Unsplash access key.")

            elif response.status == 403:
                print("Rate limited: Please try again later.")

            else:
                print("Bad request: Unable to retrieve image.")

        description = (
            f"Photo by [{data['user']['name']}]({data['user']['links']['html']}) on [Unsplash](https://unsplash.com)"
        )
        embed: discord.Embed = discord.Embed(
            title=data["alt_description"].capitalize(),
            url=data["links"]["download"],
            description=description,
            color=cs.RANDOM_COLOR,
        )
        embed.set_image(url=data["urls"]["regular"])

        return await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="album",
        help="Returns an album.",
        aliases=["albums"],
        with_app_command=True,
    )
    async def album(self, ctx: DwelloContext, *, album: str) -> Optional[discord.Message]:
        data: SearchResult = await self.spotify_client.search(query=album, types=[ObjectType.Album], limit=5)

        albums: List[Dict[str, Any]] = data._data["albums"]["items"]
        if not albums:
            return await ctx.reply(
                f"Can't find any albums by the name of *{mk(album, as_needed=False)}*",
                user_mistake=True,
            )

        for album in albums:
            album: Dict[str, Any]  # = albums[0]

            _id = album["id"]
            name = album["name"]
            release_date = album["release_date"]
            link = album["external_urls"]["spotify"]
            image_url = album["images"][1]["url"] if album["images"] else None

            artists = [(artist["name"], artist["external_urls"]["spotify"]) for artist in album["artists"]][:2]

            embed: discord.Embed = discord.Embed(
                title=name,
                url=link,
                color=cs.RANDOM_COLOR,
            )
            embed.set_thumbnail(url=image_url)

            try:
                timestamp = get_unix_timestamp(release_date, "%Y-%m-%d", style="d")
            except ValueError:
                timestamp = release_date

            embed.add_field(name="Release Date", value=timestamp, inline=False)

            tracks_data: Dict[str, Any] = await self.spotify_http_client.get_album_tracks(id=_id, market="US", limit=5)

            if tracks := tracks_data["items"]:
                embed.add_field(
                    name="Tracks",
                    value="\n".join([f"> [{track['name']}]({track['external_urls']['spotify']})" for track in tracks]),
                )

            embed.add_field(
                name="Artist" if len(artists) == 1 else "Artists",
                value="\n".join([f"> [{i[0].title()}]({i[1]})" for i in artists]),
            )

        embeds = [(name, embed)]
        # await ctx.send(embeds)
        # view = OptionSelectView(ctx, embeds)
        # await view.start()
        return await ctx.reply(embed=embeds[0][1])

    """not_found = f"Can't find any albums by the name of *{discord.utils.escape_markdown(album, as_needed=False)}*"

        try:
            data: SearchResult = await self.spotify_client.search(query=album, types=[ObjectType.Album], limit=5)

        except NotFound:
            return await ctx.reply(not_found, user_mistake=True)

        albums: List[Dict[str, Any]] = data._data['albums']['items']
        if not albums:
            return await ctx.reply(not_found, user_mistake=True)

        embeds: List[Tuple[str, discord.Embed]] = []

        for album in albums:

            album: Dict[str, Any]

            _id = album['id']
            name = album['name']
            release_date = album['release_date']
            link = album['external_urls']['spotify']
            image_url = album['images'][1]['url'] if album['images'] else None

            artists = [(artist['name'], artist['external_urls']['spotify']) for artist in album['artists']][:2]

            embed: discord.Embed = discord.Embed(
                title=name,
                url=link,
                color=cs.RANDOM_COLOR,
            )
            embed.set_thumbnail(url=image_url)

            try:
                timestamp = self.get_unix_timestamp(release_date, "%Y-%m-%d", style="d")
            except ValueError:
                timestamp = release_date

            embed.add_field(name="Release Date", value=timestamp, inline=False)

            tracks_data: Dict[str, Any] = await self.spotify_http_client.get_album_tracks(id=_id, market="US", limit=5)

            tracks: List[Dict[str, Any]] = tracks_data['items']
            if tracks:
                embed.add_field(name="Tracks", value="\n".join([f"> [{track['name']}]({track['external_urls']['spotify']})" for track in tracks]))

            embed.add_field(
                name="Artist" if len(artists) == 1 else "Artists",
                value="\n".join([f"> [{i[0].title()}]({i[1]})" for i in artists]),
            )

            embeds.append((name, embed))

        view = OptionSelectView(ctx, embeds)
        return await view.start()"""  # noqa: E501

    @commands.hybrid_command(
        name="artist",
        help="Returns an artist.",
        aliases=["artists"],
        with_app_command=True,
    )
    async def artist(self, ctx: DwelloContext, *, artist: str) -> Optional[discord.Message]:
        data: SearchResult = await self.spotify_client.search(query=artist, types=[ObjectType.Artist], limit=5)

        artists: List[Artist] = data.artists.items
        if not artists:
            return await ctx.reply(
                f"Can't find any artists by the name of *{mk(artist, as_needed=False)}*",
                user_mistake=True,
            )

        artist: Artist = artists[0]

        album_data: Dict[str, Any] = await self.spotify_http_client.get_artist_albums(
            id=artist.id, include_groups=["album"], market="US", limit=5
        )

        tracks_data: Dict[str, Any] = await self.spotify_http_client.get_artist_top_tracks(id=artist.id, market="US")

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

        tracks: List[Dict[str, Any]] = tracks_data["tracks"]
        top_tracks = sorted(tracks, key=lambda x: x["popularity"], reverse=True)

        _description = f"**Followers**: {artist.followers.total:,}\n**Genres**: " + ", ".join(list(artist.genres[:2]))
        embed: discord.Embed = discord.Embed(
            title=artist.name,
            url=artist.external_urls.spotify,
            description=_description,
            color=cs.RANDOM_COLOR,
        )
        image: Image = artist.images[1] if artist.images else None
        if image:
            embed.set_thumbnail(url=image.url)
        embed.add_field(
            name="Top Albums",
            value="\n".join(f"> [{name}]({url})" for name, url in album_tuples),
        )  # •
        embed.add_field(
            name="Top Tracks",
            value="\n".join(f"> [{track['name']}]({track['external_urls']['spotify']})" for track in top_tracks[:3]),
        )

        return await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="playlist",
        help="Returns a playlist.",
        aliases=["playlists"],
        with_app_command=True,
    )
    async def playlist(self, ctx: DwelloContext, *, playlist: str) -> Optional[discord.Message]:
        data: SearchResult = await self.spotify_client.search(query=playlist, types=[ObjectType.Playlist], limit=5)

        playlists: List[Dict[str, Any]] = data._data["playlists"]["items"]
        if not playlists:
            return await ctx.reply(
                f"Can't find any playlists by the name of *{mk(playlist, as_needed=False)}*",
                user_mistake=True,
            )

        playlist: Dict[str, Any] = playlists[0]

        name = playlist["name"]
        url = playlist["external_urls"]["spotify"]
        total_tracks = playlist["tracks"]["total"]
        owner_name = playlist["owner"]["display_name"]
        owner_url = playlist["owner"]["external_urls"]["spotify"]
        image_url = playlist["images"][0]["url"] if playlist["images"] else None
        description = playlist["description"] or None

        embed: discord.Embed = discord.Embed(
            title=name,
            url=url,
            description=description,
            color=cs.RANDOM_COLOR,
        )
        if image_url:
            embed.set_thumbnail(url=image_url)
        embed.add_field(name="Owner", value=f"[{owner_name}]({owner_url})")
        embed.add_field(name="Total Tracks", value=total_tracks)

        return await ctx.reply(embed=embed)

    @commands.hybrid_command(name="track", help="Returns a track.", aliases=["tracks"], with_app_command=True)
    async def track(self, ctx: DwelloContext, *, track: str) -> Optional[discord.Message]:
        data: SearchResult = await self.spotify_client.search(query=track, types=[ObjectType.Track], limit=5)

        tracks: List[Track] = data.tracks.items
        if not tracks:
            return await ctx.reply(
                f"Can't find any tracks by the name of *{mk(track, as_needed=False)}*",
                user_mistake=True,
            )

        _track: Track = tracks[0]
        _album: PartialAlbum = _track.album
        _artists: List[Tuple[str, str]] = [(artist.name, artist.external_urls.spotify) for artist in _track.artists][:2]

        duration_in_minutes = _track.duration / 1000 / 60

        duration_str = (
            f"**Duration**: {'{:.2f}'.format(duration_in_minutes)} min"
            if duration_in_minutes >= 1
            else "{:.2f}".format(_track.duration / 1000) + " sec"
        )

        release_str = "\n**Release Date**: "
        try:
            release_str += get_unix_timestamp(_album.release_date.date, "%Y-%m-%d", style="d")
        except ValueError:
            release_str += _album.release_date.date

        embed: discord.Embed = discord.Embed(
            title=_track.name,
            url=f"https://open.spotify.com/track/{_track.id}",
            description=duration_str + release_str,
            color=cs.RANDOM_COLOR,
        )
        image: Image = _album.images[1] if _album.images else None
        if image:
            embed.set_thumbnail(url=image.url)
        embed.add_field(
            name="Artist" if len(_artists) == 1 else "Artists",
            value="\n".join([f"> [{i[0].title()}]({i[1]})" for i in _artists]),
        )
        embed.add_field(name="Album", value=f"[{_album.name}]({_album.external_urls.spotify})")

        return await ctx.reply(embed=embed)

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

        raise GameNotFound(name)

    @commands.hybrid_command(name="game", help="Returns a game.", aliases=["games"], with_app_command=True)
    async def game(self, ctx: DwelloContext, *, game: str) -> Optional[discord.Message]:
        # start = time.time()
        # end = time.time()
        # await ctx.send(f"Executed in: {end-start}") # Idea for a time per func to calculate overall latency/response time?
        # use different api
        # not enough data ^ and cant search for similair results

        try:
            game_id = await self.get_game_by_name(game)
        except GameNotFound:
            return await ctx.reply(f"Couldn't find a game by the name *{mk(game)}*", user_mistake=True)

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

        # minimum_pc_requirements = data['pc_requirements']['minimum']
        # recommended_pc_requirements = data['pc_requirements']['recommended']
        # publishers = data['publishers']
        # price_overview = data['price_overview']
        # genres = [genre['description'] for genre in data['genres']]

        embed: discord.Embed = discord.Embed(
            title=name,
            url=website,
            description=short_description,
            color=cs.RANDOM_COLOR,
        )
        embed.set_thumbnail(url=thumbnail)

        embed.add_field(name="Metascore", value=f"[{metascore}]({metaurl})")
        embed.add_field(
            name="Price",
            value=f"[{price}](https://store.steampowered.com/app/{game_id})",
        )
        embed.add_field(name="Developed by", value=", ".join(devs[:3]), inline=False)

        return await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="actor",
        help="Returns a person who's known in the movie industry.",
        aliases=["actors", "actress", "actresses"],
        with_app_command=True,
    )  # amybe people alias, but later if there are no other ppl aliases
    async def movie_person(self, ctx: DwelloContext, *, person: str) -> Optional[discord.Message]:
        pages: int = 1
        url: URL = (
            f"https://api.themoviedb.org/3/search/person?query={person}&include_adult=True&language=en-US&page={pages}"
        )
        async with self.bot.http_session.get(url=url, headers=self.tmdb_headers) as response:
            data = await response.json()

        if response.status != 200:
            return await ctx.reply("Couldn't connect to the API.", user_mistake=True)

        try:
            person = max(data["results"], key=lambda _person: _person["popularity"])

        except ValueError:
            return await ctx.reply(f"Couldn't find a person by the name of {person}.", user_mistake=True)

        page: wikipediaapi.WikipediaPage = self.wiki.page(person["name"])

        embed: discord.Embed = discord.Embed(
            title=person["original_name"],
            description=page.summary[:500] + "..." if len(page.summary) > 500 else "",
            url=f"https://www.themoviedb.org/person/{person['id']}",
            color=cs.RANDOM_COLOR,
        )
        # rd: List[str] = movie['release_date'].split('-')
        # year, month, day = int(rd[0]), int(rd[1]), int(rd[2])
        # release_date: datetime.datetime = datetime.datetime(year, month, day, tzinfo=None)

        # embed.add_field(name='Release Date', value=discord.utils.format_dt(release_date, style='d'))

        gender = "Male" if person["gender"] == 2 else "Female"
        top_movies = list(person["known_for"])

        embed.add_field(name="Gender", value=gender)
        # embed.add_field(name='Age', value=None)
        embed.add_field(name="Department", value=person["known_for_department"])

        if top_movies_desc := "".join(
            f"\n• [{movie['title']}](https://www.themoviedb.org/movie/{movie['id']})" for movie in top_movies
        ):
            embed.add_field(name="Top Movies", value=top_movies_desc, inline=False)

        if person["profile_path"]:
            embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{person['profile_path']}")

        embed.set_footer(text=f"Popularity: {person['popularity']}")

        return await ctx.reply(embed=embed)

    @commands.command(
        name="movie",
        help="Returns a movie by its title.",
        aliases=["film", "films", "movies"],
    )
    async def movie(self, ctx: DwelloContext, *, movie: str) -> Optional[discord.Message]:
        # Docs: https://developer.themoviedb.org/reference/intro/getting-started

        pages: int = 1
        url: URL = f"https://api.themoviedb.org/3/search/movie?query={movie}&include_adult=True&language=en-US&page={pages}"
        async with self.bot.http_session.get(url=url, headers=self.tmdb_headers) as response:
            data = await response.json()

        if response.status != 200:
            return await ctx.reply("Couldn't connect to the API.", user_mistake=True)

        try:
            movie = max(data["results"], key=lambda _movie: _movie["vote_count"])

        except ValueError:
            return await ctx.reply(f"Couldn't find a movie by the name of {movie}.", user_mistake=True)

        embed: discord.Embed = discord.Embed(
            title=movie["title"],
            description=movie["overview"],
            url=f"https://www.themoviedb.org/movie/{movie['id']}",
            color=cs.RANDOM_COLOR,
        )
        embed.add_field(
            name="Release Date",
            value=get_unix_timestamp(movie["release_date"], "%Y-%m-%d", style="d"),
        )
        embed.add_field(name="Vote Average", value=f"{str(movie['vote_average'])[:3]} / 10")
        embed.add_field(name="Vote Count", value=movie["vote_count"])

        if movie["poster_path"]:
            embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{movie['poster_path']}")

        embed.set_footer(text=f"Popularity: {movie['popularity']}")

        return await ctx.reply(embed=embed)

    @app_commands.command(name="movie", description="Returns a movie by its title.")
    async def _movie(self, interaction: Interaction, *, movie: str, year: int = None) -> Optional[discord.Message]:
        pages: int = 1

        url: URL = f"https://api.themoviedb.org/3/search/movie?query={movie}&include_adult=True&language=en-US&primary_release_year={year}&page={pages}"

        if not year:
            url = f"https://api.themoviedb.org/3/search/movie?query={movie}&include_adult=True&language=en-US&page={pages}"

        async with self.bot.http_session.get(url=url, headers=self.tmdb_headers) as response:
            data = await response.json()

        if response.status != 200:
            return await interaction.response.send_message("Couldn't connect to the API.", ephemeral=True)

        try:
            movie = max(data["results"], key=lambda _movie: _movie["vote_count"])

        except ValueError:
            return await interaction.response.send_message(
                f"Couldn't find a movie by the name of {movie}.", ephemeral=True
            )  # noqa: E501

        embed: discord.Embed = discord.Embed(
            title=movie["title"],
            description=movie["overview"],
            url=f"https://www.themoviedb.org/movie/{movie['id']}",
            color=cs.RANDOM_COLOR,
        )
        embed.add_field(
            name="Release Date",
            value=get_unix_timestamp(movie["release_date"], "%Y-%m-%d", style="d"),
        )
        embed.add_field(name="Vote Average", value=f"{str(movie['vote_average'])[:3]} / 10")
        embed.add_field(name="Vote Count", value=movie["vote_count"])

        if movie["poster_path"]:
            embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{movie['poster_path']}")

        embed.set_footer(text=f"Popularity: {movie['popularity']}")

        return await interaction.response.send_message(embed=embed)

    @commands.command(name="show", help="Returns a TV show by its title.", aliases=["series", "shows"])
    async def show(self, ctx: DwelloContext, *, show: str) -> Optional[discord.Message]:
        pages: int = 1
        url: URL = f"https://api.themoviedb.org/3/search/tv?query={show}&include_adult=True&language=en-US&page={pages}"
        async with self.bot.http_session.get(url=url, headers=self.tmdb_headers) as response:
            data = await response.json()

        if response.status != 200:
            return await ctx.reply("Couldn't connect to the API.", user_mistake=True)

        try:
            show = max(data["results"], key=lambda _show: _show["vote_count"])

        except ValueError:
            return await ctx.reply(f"Couldn't find a show by the name of {show}.", user_mistake=True)

        embed: discord.Embed = discord.Embed(
            title=show["original_name"],
            description=show["overview"],
            url=f"https://www.themoviedb.org/tv/{show['id']}",
            color=cs.RANDOM_COLOR,
        )
        embed.add_field(
            name="Release Date",
            value=get_unix_timestamp(show["first_air_date"], "%Y-%m-%d", style="d"),
        )
        embed.add_field(name="Vote Average", value=f"{str(show['vote_average'])[:3]} / 10")
        embed.add_field(name="Vote Count", value=show["vote_count"])

        if show["poster_path"]:
            embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{show['poster_path']}")

        embed.set_footer(text=f"Popularity: {show['popularity']}")

        return await ctx.reply(embed=embed)

    @app_commands.command(name="show", description="Returns a TV show by its title.")
    async def _show(self, interaction: Interaction, *, show: str, year: int = None) -> Optional[discord.Message]:
        pages: int = 1

        url = f"https://api.themoviedb.org/3/search/tv?query={show}&include_adult=True&language=en-US&primary_release_year={year}&page={pages}"

        if not year:
            url = f"https://api.themoviedb.org/3/search/tv?query={show}&include_adult=True&language=en-US&page={pages}"

        async with self.bot.http_session.get(url=url, headers=self.tmdb_headers) as response:
            data = await response.json()

        if response.status != 200:
            return await interaction.response.send_message("Couldn't connect to the API.", ephemeral=True)

        try:
            show = max(data["results"], key=lambda _show: _show["vote_count"])

        except ValueError:
            return await interaction.response.send_message(f"Couldn't find a show by the name of {show}.", ephemeral=True)

        embed: discord.Embed = discord.Embed(
            title=show["original_name"],
            description=show["overview"],
            url=f"https://www.themoviedb.org/tv/{show['id']}",
            color=cs.RANDOM_COLOR,
        )
        embed.add_field(
            name="Release Date",
            value=get_unix_timestamp(show["first_air_date"], "%Y-%m-%d", style="d"),
        )
        embed.add_field(name="Vote Average", value=f"{str(show['vote_average'])[:3]} / 10")
        embed.add_field(name="Vote Count", value=show["vote_count"])

        if show["poster_path"]:
            embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{show['poster_path']}")

        embed.set_footer(text=f"Popularity: {show['popularity']}")

        return await interaction.response.send_message(embed=embed)

    @commands.hybrid_command(
        name="weather",
        help="Shows you the temparature in the city you've typed in.",
        with_app_command=True,
    )
    async def weather(self, ctx: DwelloContext, *, city: str) -> Optional[discord.Message]:
        if not city:
            return await ctx.reply("Please provide a city or a contry.", mention_author=True)

        args = city.lower()

        async with self.bot.http_session.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={args}&APPID={WEATHER_KEY}&units=metric"
        ) as response:
            data = await response.json()

        if data["cod"] == "404":
            with open("datasets/countries.json", "r") as file:
                data: dict = json.load(file)

            matches = []
            for key, value in data.items():
                if country_match := difflib.get_close_matches(args, [key]):
                    matches.append(country_match[0])
                elif city_matches := difflib.get_close_matches(args, value):
                    matches.append(city_matches[0])

            clean_matches = difflib.get_close_matches(args, matches, 5)

            description = "Please check the spelling and try again."
            if clean_matches:
                description = "**Did you mean...**\n"
                for match in clean_matches:
                    description += f"\n{match}"

            matches_embed: discord.Embed = discord.Embed(
                description=f"Sorry, but I couldn't recognise the city **{args.title()}**." f"\n{description}",
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
            # f"I recommend wearing {dress_code} clothes outside."
        )

        weather_embed = discord.Embed(
            title=f"Current weather in {data['name']}",
            description=payload,
            color=discord.Colour.blurple(),
        )

        weather_embed.set_footer(text="Powered by OpenWeatherMap")
        weather_embed.set_thumbnail(url=f"http://openweathermap.org/img/w/{data['weather'][0]['icon']}.png")

        weather_embed.add_field(
            name="Location",
            value=f"{data['name']}, {data['sys']['country']}",
            inline=False,
        )
        weather_embed.add_field(
            name="Weather",
            value=data["weather"][0]["description"].title(),
            inline=False,
        )
        weather_embed.add_field(name="Humidity", value=f"{data['main']['humidity']}%", inline=True)
        weather_embed.add_field(name="Wind", value=f"{data['wind']['speed']} m/s", inline=True)
        weather_embed.add_field(name="Pressure", value=f"{data['main']['pressure']} hPa", inline=True)

        return await ctx.reply(embed=weather_embed, ephemeral=False)
