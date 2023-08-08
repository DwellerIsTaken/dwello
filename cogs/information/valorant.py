import json
import re
from datetime import datetime
from textwrap import dedent
from typing import Any, ClassVar, Dict, List, Literal, Optional, TypedDict, TypeVar, Union
from urllib.parse import quote

import aiohttp
import discord
from discord.ext import commands
from typing_extensions import Self

from core import BaseCog, Context, Dwello
from utils import DefaultPaginator

JSON = Dict[str, Any]


class NotFound(Exception):
    pass


class ParsingError(Exception):
    pass


async def json_or_text(response: aiohttp.ClientResponse) -> Union[JSON, str]:
    text = await response.text()
    try:
        if response.headers["content-type"] == "application/json":
            return json.loads(text)

    except KeyError:
        pass

    return text


class Route:
    BASE: ClassVar[str] = "https://api.henrikdev.xyz/valorant"

    def __init__(self, method: str, path: str, **parameters: Any) -> None:
        self.method: str = method
        self.path: str = path

        url = self.BASE + self.path
        if parameters:
            url = url.format_map({k: quote(v) if isinstance(v, str) else v for k, v in parameters.items()})

        self.url: str = url


class HTTPClient:
    def __init__(self, *, token: Optional[str] = None, session: Optional[aiohttp.ClientSession] = None) -> None:
        self.token: str = token
        self._session: aiohttp.ClientSession = session or aiohttp.ClientSession()

    async def request(self, route: Route, **kwargs: Any) -> Any:
        url = route.url
        method = route.method

        headers: Dict[str, str] = {
            "User-Agent": "Dwello Discord Bot (hitoshi.org) (discord.py/%s)" % discord.__version__,
        }

        if self.token:
            headers["key"] = self.token

        if kwargs.get("headers"):
            kwargs["headers"] = headers | kwargs["headers"]
        else:
            kwargs["headers"] = headers

        async with self._session.request(method, url, **kwargs) as response:
            data = await json_or_text(response)

            if 300 > response.status >= 200:
                return data

            elif response.status == 404:
                raise NotFound(data)

            else:
                raise Exception(data)


class MapAssets(TypedDict):
    display_icon: str
    list_view_icon: str
    splash: str


class CharacterAssets(TypedDict):
    display_icon: str
    display_icon_small: str
    bust_portrait: str
    full_portrait: str
    full_portrait_v2: str
    kill_feed_portrait: str
    background: str


class Map:
    def __init__(self, id: str, name: str) -> None:
        self._id = id
        self._name = name

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_json(cls, json: JSON) -> Self:
        return cls(json["id"], json["name"])

    @property
    def id(self) -> str:
        """Returns the map's ID"""
        return self._id

    @property
    def name(self) -> str:
        """Returns the map's name (eg. Haven)"""
        return self._name

    async def get_assets(self, session: aiohttp.ClientSession) -> MapAssets:
        async with session.request("GET", f"https://valorant-api.com/v1/maps/{self.id}") as resp:
            json_ = await resp.json()
            json_ = json_["data"]
            assets: MapAssets = {
                "display_icon": json_["displayIcon"],
                "list_view_icon": json_["listViewIcon"],
                "splash": json_["splash"],
            }
            return assets


class Character:
    def __init__(self, id: str, name: str) -> None:
        self._id = id
        self._name = name

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_json(cls, json: JSON) -> Self:
        return cls(json["id"], json["name"])

    @property
    def id(self) -> str:
        """Returns the characters's ID"""
        return self._id

    @property
    def name(self) -> str:
        """Returns the characters's name (eg. Deadlock)"""
        return self._name

    async def get_assets(self, session: aiohttp.ClientSession) -> CharacterAssets:
        async with session.request("GET", f"https://valorant-api.com/v1/agents/{self.id}") as resp:
            json_ = await resp.json()
            json_ = json_["data"]
            assets: CharacterAssets = {
                "display_icon": json_["displayIcon"],
                "display_icon_small": json_["displayIconSmall"],
                "bust_portrait": json_["bustPortrait"],
                "full_portrait": json_["fullPortrait"],
                "full_portrait_v2": json_["fullPortraitV2"],
                "background": json_["background"],
                "kill_feed_portrait": json_["killfeedPortrait"],
            }
            return assets


class Shots(TypedDict):
    head: int
    body: int
    leg: int


class Damage(TypedDict):
    made: int
    received: int


class Standing(TypedDict):
    red: Optional[int]
    blue: Optional[int]


class Match:
    def __init__(
        self,
        id: str,
        map: Map,
        mode: str,
        started_at: str,
        cluster: str,
        team: Literal["Blue", "Red"],
        character: Character,
        tier: int,
        score: int,
        kills: int,
        deaths: int,
        assists: int,
        shots: Shots,
        damage: Damage,
        standing: Standing,
    ) -> None:
        self._id = id
        self._map = map
        self._mode = mode
        self._started_at = started_at
        self._cluster = cluster
        self._team = team
        self._character = character
        self._tier = tier
        self._score = score
        self._kills = kills
        self._deaths = deaths
        self._assists = assists
        self._shots = shots
        self._damage = damage
        self._standing = standing

    @classmethod
    def from_json(cls, json: JSON) -> Self:
        shots: Shots = {
            "head": json["stats"]["shots"]["head"],
            "body": json["stats"]["shots"]["body"],
            "leg": json["stats"]["shots"]["leg"],
        }
        damage: Damage = {"made": json["stats"]["damage"]["made"], "received": json["stats"]["damage"]["received"]}
        standing: Standing = {"red": json["teams"]["red"], "blue": json["teams"]["blue"]}

        return cls(
            json["meta"]["id"],
            Map.from_json(json["meta"]["map"]),
            json["meta"]["mode"],
            json["meta"]["started_at"],
            json["meta"]["cluster"],
            json["stats"]["team"],
            Character.from_json(json["stats"]["character"]),
            json["stats"]["tier"],
            json["stats"]["score"],
            json["stats"]["kills"],
            json["stats"]["deaths"],
            json["stats"]["assists"],
            shots,
            damage,
            standing,
        )

    @property
    def id(self) -> str:
        """Returns the match's ID."""
        return self._id

    @property
    def map(self) -> Map:
        """Returns the match's map."""
        return self._map

    @property
    def mode(self) -> str:
        """Returns the match's mode."""
        return self._mode

    @property
    def started_at(self) -> datetime:
        """Returns the time the match started at."""
        return datetime.strptime(self._started_at, "%Y-%m-%dT%H:%M:%S.%fZ")

    @property
    def cluster(self) -> str:
        """Returns the match's cluster (eg. Frankfurt, Tokyo)."""
        return self._cluster

    @property
    def team(self) -> Literal["Blue", "Red"]:
        """Returns the players team."""
        return self._team

    @property
    def character(self) -> Character:
        """Returns the character the player played as."""
        return self._character

    @property
    def tier(self) -> int:
        """Returns the player's tier."""
        return self._tier

    @property
    def score(self) -> int:
        """Returns the player's score."""
        return self._score

    @property
    def kills(self) -> int:
        """Returns the player's kills."""
        return self._kills

    @property
    def deaths(self) -> int:
        """Returns the player's deaths."""
        return self._deaths

    @property
    def assists(self) -> int:
        """Returns the player's assists."""
        return self._assists

    @property
    def shots(self) -> Shots:
        """Returns the player's shots"""
        return self._shots

    @property
    def damage(self) -> Damage:
        """Returns the player's damage"""
        return self._damage

    @property
    def standing(self) -> Optional[Standing]:
        """Returns the teams' round wins, if applicable."""
        return self._standing if any((self._standing["blue"], self._standing["red"])) else None


class RankData:
    """Represents the ranked (competetive) data of a Valorant player account"""

    def __init__(
        self,
        puuid: Optional[str],
        current_tier: Optional[int],
        current_tier_patched: Optional[str],
        images: Optional[Dict[str, str]],
        map: Optional[Map],
        change: Optional[int],
        elo: Optional[int],
    ) -> None:
        self._puuid = puuid
        self._current_tier = current_tier
        self._current_tier_patched = current_tier_patched
        self._images = images
        self._map = map
        self._change = change
        self._elo = elo

    def __repr__(self) -> str:
        return f"<RankData puuid='{self._puuid}', current_tier_patched='{self._current_tier_patched}', elo={self._elo}>"

    @classmethod
    def from_json(cls, json: JSON) -> Optional[Self]:
        if not json:
            return None

        return cls(
            json["currenttier"],
            json["currenttierpatched"],
            json["images"],
            Map.from_json(json["map"]),
            json["mmr_change_since_last_game"],
            json["elo"],
        )

    @property
    def id(self) -> Optional[str]:
        return self._puuid

    @property
    def rank(self) -> Optional[str]:
        """Returns the player's current rank (eg. "Gold 3")"""
        return self._current_tier_patched

    @property
    def images(self) -> Optional[Dict[str, str]]:
        return self._images

    @property
    def change(self) -> Optional[int]:
        return self._change

    @property
    def elo(self) -> Optional[int]:
        return self._elo

    @property
    def rank_card_small(self) -> Optional[str]:
        return self._images["small"]

    @property
    def rank_card_large(self) -> Optional[str]:
        return self._images["large"]


class Player:
    """Represents a Valorant player account"""

    def __init__(
        self,
        puuid: str,
        region: str,
        account_level: int,
        name: str,
        tag: str,
        card: Dict[str, str],
        last_update_raw: int,
    ) -> None:
        self._puuid = puuid
        self._region = region
        self._account_level = account_level
        self._name = name
        self._tag = tag
        self._card = card
        self._last_update_raw = last_update_raw

        self._rank_data: Optional[RankData] = None

    def __str__(self) -> str:
        return f"{self.name}#{self.tag}"

    def __repr__(self) -> str:
        return f"<Player puuid='{self._puuid}', name='{self.name}', tag='{self.tag}'>"

    def __eq__(self, other: Any) -> bool:
        return hasattr(other, "_puuid") and self._puuid == other._puuid

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    @classmethod
    def from_json(cls, json: JSON) -> Self:
        return cls(
            json["puuid"],
            json["region"],
            json["account_level"],
            json["name"],
            json["tag"],
            json["card"],
            json["last_update_raw"],
        )

    @property
    def id(self) -> str:
        """Returns the player's `PUUID` (Player Universally Unique Identifier)."""
        return self._puuid

    @property
    def region(self) -> str:
        """Returns the player's region."""
        return self._region

    @property
    def level(self) -> int:
        """Returns the player's account level."""
        return self._account_level

    @property
    def name(self) -> str:
        """Returns the player's name."""
        return self._name

    @property
    def tag(self) -> str:
        """Returns the player's tag."""
        return self._tag

    @property
    def small_card(self) -> str:
        """Returns the player's card in a small format."""
        return self._card["small"]

    @property
    def large_card(self) -> str:
        """Returns the player's card in a large format."""
        return self._card["large"]

    @property
    def wide_card(self) -> str:
        """Returns the player's card in a wide format."""
        return self._card["wide"]

    @property
    def card_id(self) -> str:
        """Returns the player's card's ID."""
        return self._card["id"]

    @property
    def last_updated(self) -> datetime:
        """Returns when the player data was last updated."""
        return datetime.fromtimestamp(self._last_update_raw)

    @property
    def rank_data(self) -> Optional[RankData]:
        """Returns the players rank data, if any."""
        return self._rank_data


PUUID_PATTERN = re.compile("^[A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12}$", flags=re.IGNORECASE)


class PlayerConverter(commands.Converter):
    async def convert(self, ctx: Context, argument: str) -> Optional[Player]:
        cog: Valorant = ctx.cog

        split = argument.split("#")
        if re.fullmatch(PUUID_PATTERN, argument):
            try:
                return await cog.get_player_by_puuid(argument)
            except NotFound:
                return

        elif len(split) == 2:
            try:
                return await cog.get_player_by_tag(*split)
            except NotFound:
                return

        else:
            raise ParsingError(argument)


PlayerT = TypeVar("PlayerT", bound=Player)


class Valorant(BaseCog):
    def __init__(self, bot: Dwello, *args, **kwargs) -> None:
        super().__init__(bot, *args, **kwargs)
        self.bot = bot
        self.http = HTTPClient(session=self.bot.http_session)

    async def get_player_by_tag(self, name: str, tag: str) -> Optional[Player]:
        route = Route("GET", "/v1/account/{name}/{tag}", name=name, tag=tag)
        try:
            res = await self.http.request(route)
        except NotFound:
            return

        json_ = json.loads(res)
        return Player.from_json(json_["data"])

    async def get_player_by_puuid(self, puuid: str) -> Optional[Player]:
        route = Route("GET", "/v1/by-puuid/account/{puuid}", puuid=puuid)
        try:
            res = await self.http.request(route)
        except NotFound:
            return

        json_ = json.loads(res)
        return Player.from_json(json_["data"])

    async def get_rank_data(self, player: PlayerT) -> PlayerT:
        route = Route("GET", "/v1/mmr-history/{region}/{name}/{tag}", region=player.region, name=player.name, tag=player.tag)
        res = await self.http.request(route)

        json_ = json.loads(res)
        try:
            rank_data = RankData.from_json(json_["data"][0])

        except IndexError:
            return player

        player._rank_data = rank_data
        return player

    async def get_matches(self, player: Player, *, amount: int = 1) -> Union[Match, List[Match]]:
        if amount > 10:
            raise ValueError("You can only get 10 matches at a time.")

        region, name, tag = player.region, player.name, player.tag
        route = Route(
            "GET", "/v1/lifetime/matches/{region}/{name}/{tag}?size={size}", region=region, name=name, tag=tag, size=amount
        )
        res = await self.http.request(route)

        json_ = json.loads(res)
        match = Match.from_json(json_["data"][0]) if amount == 1 else [Match.from_json(i) for i in json_["data"]]

        return match

    @commands.group(description="Commands for interacting with the Valorant API.")
    async def valorant(self, ctx: Context):
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @valorant.command(name="player", description="Get information on a Valorant account.")
    async def player_(self, ctx: Context, player: PlayerConverter):
        if player is None:
            return await ctx.send("Couldn't find that player, make sure that player exists and the account is not private.")

        await ctx.typing()
        player: Player = await self.get_rank_data(player)

        embed = discord.Embed(title=f"{player.name}#{player.tag}'s Account")
        embed.set_image(url=player.wide_card)
        if player.rank_data:
            embed.set_thumbnail(url=player.rank_data.rank_card_small)
        embed.description = dedent(
            f"""
            PUUID: `{player.id}`
            Level: `{player.level}`
            Current Rank: `{player.rank_data and player.rank_data.rank or "Unranked"}`
        """
        )
        embed.set_footer(text="Last Updated").timestamp = player.last_updated

        await ctx.send(embed=embed)

    @valorant.command(aliases=["matches"], description="Displays the player's 10 latest matches.")
    async def match(self, ctx: Context, player: PlayerConverter):
        await ctx.typing()
        matches = await self.get_matches(player, amount=10)

        embeds = []
        for index, match in enumerate(matches, start=1):
            match: Match

            color = 0x2B2D31
            if standing := match.standing:
                sorted_standing = list(dict(sorted(standing.items(), key=lambda i: i[1])))
                color = 0x1DB954 if sorted_standing[0] != match.team.lower() else 0xFF0000

            embed = discord.Embed(title=f"{player}'s Latest Matches ({index}/{len(matches)})", color=color)
            embed.set_author(name=f"{match.mode} | {match.map} | {match.character}")
            embed.set_footer(text="Started").timestamp = match.started_at

            character_assets = await match.character.get_assets(self.bot.http_session)
            embed.set_thumbnail(url=character_assets["display_icon"])

            map_assets = await match.map.get_assets(self.bot.http_session)
            embed.set_image(url=map_assets["list_view_icon"])

            embed.description = dedent(
                """
                Score: `{0.score}`
                KDA: `{0.kills}/{0.deaths}/{0.assists}`
            """.format(
                    match
                )
            )

            embed.add_field(
                name="Shots",
                value="Head: `{0[head]}`\nBody: `{0[body]}`\nLegs: `{0[leg]}`".format(match.shots),
                inline=False,
            )
            embed.add_field(name="Damage", value="Dealt: `{0[made]}`\nReceived: `{0[received]}`".format(match.damage))
            if standing:
                embed.add_field(
                    name="Standing", value="Team: `{0}`\nBlue **{1[blue]}** | **{1[red]}** Red".format(match.team, standing)
                )

            embeds.append(embed)

        await DefaultPaginator.start(ctx, embeds)

    @player_.error
    @match.error
    async def parsing_handler(self, ctx: Context, error: Any):
        if hasattr(error, "original") and isinstance(error.original, ParsingError):
            return await ctx.send("Couldn't parse that username or PUUID, please make sure it's correct and try again.")

        else:
            ctx.command.on_error = None  # Triggers global error handler if we don't handle it here
