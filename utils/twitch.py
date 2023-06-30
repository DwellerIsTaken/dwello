from __future__ import annotations

import os  # noqa: F401
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, Tuple, Union

import aiohttp
import asyncpg
import discord
from typing_extensions import Self, Type

import constants as cs
from utils import ENV

if TYPE_CHECKING:
    from core import Dwello, DwelloContext


CLIENT_ID = ENV["TWITCH_CLIENT_ID"]
CLIENT_SECRET = ENV["TWITCH_CLIENT_SECRET"]
HELIX_URL = "https://api.twitch.tv/helix/eventsub/subscriptions"


async def get_access_token(bot: Dwello):
    body = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
    }
    request: aiohttp.ClientResponse = await bot.http_session.post("https://id.twitch.tv/oauth2/token", data=body)
    keys = await request.json()
    keys["expires_in"]

    return keys["access_token"]


class Twitch:
    # FIX ACCESS TOKEN ISSUE. CREATE LOOP BASED ON EXPIRATION DATE AND REQUEST NEW ONE WHENEVER ONE EXPIRES
    def __init__(self, access_token: str, bot: Dwello) -> None:
        self.bot = bot
        self.session = bot.session
        self.access_token = access_token

    @classmethod
    async def create_access_token(cls: Type[Self], bot: Dwello) -> Self:
        access_token = await get_access_token(bot)
        return cls(access_token, bot)

    @property
    def headers(self: Self) -> Dict[str, Any]:
        return {
            "Client-ID": CLIENT_ID,
            "Authorization": f"Bearer {self.access_token}",
        }

    async def username_to_id(self, username: str) -> Optional[str]:
        url = f"https://api.twitch.tv/helix/users?login={username.lower()}"

        response: aiohttp.ClientResponse = await self.session.get(url, headers=self.headers)
        data = await response.json()

        if "data" not in data or len(data["data"]) <= 0:
            raise Exception(f"Could not find user {username}")  # incorrect check ?

        _user_id = data["data"][0]["id"]
        print(type(_user_id))

        return _user_id

    async def id_to_username(self, user_id: int) -> Optional[str]:
        url = f"https://api.twitch.tv/helix/users?id={user_id}"

        response: aiohttp.ClientResponse = await self.session.get(url, headers=self.headers)
        data = await response.json()

        # The Twitch username to subscribe to
        if "data" in data and len(data["data"]) > 0:
            _username = data["data"][0]["login"]

        else:
            raise Exception(f"Could not find user with ID {user_id}")

        return _username

    async def event_subscription(
        self, ctx: DwelloContext, type_: str, username: str
    ) -> Union[Tuple[discord.Message, dict], Any]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                session = self.bot.http_session

                try:
                    user_id = await self.username_to_id(username)

                except Exception:
                    return await ctx.reply(
                        embed=discord.Embed(
                            description=f"Could not find user **{username}**.",
                            color=cs.RANDOM_COLOR,
                        ),
                        ephemeral=True,
                    )

                broadcaster_check_dict = {}

                # List of subscriptions
                response_ = session.get(HELIX_URL, headers=self.headers).json()

                # FIX THE CHECK
                for i in response_["data"]:
                    broadcaster_id = int(i["condition"]["broadcaster_user_id"])
                    if broadcaster_id not in broadcaster_check_dict:
                        broadcaster_check_dict[broadcaster_id] = {"types": []}
                    if str(i["type"]) not in broadcaster_check_dict[broadcaster_id]["types"]:
                        broadcaster_check_dict[broadcaster_id]["types"].append(str(i["type"]))

                if user_id in broadcaster_check_dict and type_ in broadcaster_check_dict[user_id]["types"]:
                    return await ctx.reply(
                        f"Guild is already subscribed to user **{username}**.",
                        ephemeral=True,
                    )

                channel_record = await conn.fetchrow(
                    "SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2",
                    ctx.guild.id,
                    "twitch",
                )
                channel_id = int(channel_record[0]) if isinstance(channel_record[0], (str, int)) else None
                if not channel_record or not self.bot.get_channel(channel_id):
                    return await ctx.reply(
                        "You must set the channel for twitch notifications first. ```/twitch channel set [#channel]```"
                    )

                # Set up the request body for creating a subscription
                callback_url = "https://hitoshi.org/eventsub/callback"
                body = {
                    "type": type_,
                    "version": "1",
                    "condition": {"broadcaster_user_id": user_id},
                    "transport": {
                        "method": "webhook",
                        "callback": callback_url,
                        "secret": CLIENT_SECRET,
                    },
                }

                # Send the API request to create the subscription

                headers = {
                    "Client-ID": CLIENT_ID,
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                }

                response = session.post(HELIX_URL, headers=headers, json=body)

                # add some extra checks here
                # one user now; update later
                await conn.execute(
                    "INSERT INTO twitch_users(username, user_id, guild_id) VALUES($1, $2, $3)",
                    username,
                    int(user_id),
                    ctx.guild.id,
                )
                # await conn.execute("UPDATE server_data SET twitch_id = $1 WHERE guild_id = $2 AND event_type = 'twitch'", user_id, ctx.guild.id)  # noqa: E501
                # Print the response to confirm whether the subscription was created successfully or not

        await self.bot.db.fetch_table_data("twitch_users")
        return (
            await ctx.reply(f"Added **{username}** to twitch notifications list.", ephemeral=True),
            response.json(),
        )

        # type_ = stream.online

    # return a list of users the guild is subscribed to
    async def guild_twitch_subscriptions(self, ctx: DwelloContext) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                data = await conn.fetch(
                    "SELECT username, user_id FROM twitch_users WHERE guild_id = $1",
                    ctx.guild.id,
                )
                twitch_embed = discord.Embed(title="Twitch subscriptions", color=cs.RANDOM_COLOR)
                twitch_embed.set_thumbnail(
                    url="https://mlpnk72yciwc.i.optimole.com/cqhiHA-5_fN-hee/w:350/h:350/q:90/rt:fill/g:ce/https://bleedingcool.com/wp-content/uploads/2019/09/twitch-logo-icon-2019.jpg"
                )

                if data:
                    for record in data:
                        twitch_id = record["user_id"]
                        twitch_name = record["username"]
                        # name = await self.id_to_username(twitch_id)
                        twitch_embed.add_field(name=twitch_name, value=twitch_id, inline=False)

                elif not (data[0] if data else None):
                    return await ctx.reply(
                        embed=discord.Embed(
                            description="The guild isn't subscribed to any twitch streamers.",
                            color=cs.RANDOM_COLOR,
                        )
                    )

        return await ctx.reply(embed=twitch_embed)

    async def twitch_unsubscribe_from_streamer(
        self, ctx: DwelloContext, username: Union[str, Literal["all"]]
    ) -> Optional[
        discord.Message
    ]:  # IF ALL: GET ALL TWITCH USERS THAT GUILD IS SUBSCRIBED TO AND UNSUB (what if the same user for multiple guilds)
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                session = self.bot.http_session

                response = session.get(HELIX_URL, headers=self.headers).json()

                if not response["data"]:
                    return await ctx.reply(
                        embed=discord.Embed(
                            description="No events to unsubscribe from.",
                            color=cs.RANDOM_COLOR,
                        ),
                        ephemeral=True,
                    )

                done = 0
                count = 0
                for i in response["data"]:
                    subscription_id = i["id"]
                    broadcaster_id = int(i["condition"]["broadcaster_user_id"])
                    url = f"https://api.twitch.tv/helix/eventsub/subscriptions?id={subscription_id}"

                    if username == "all":
                        response = session.delete(url, headers=self.headers)
                        if not done:
                            await conn.execute(
                                "DELETE FROM twitch_users WHERE guild_id = $1",
                                ctx.guild.id,
                            )
                            done = 1
                        count += 1

                    elif isinstance(username, str):
                        user_id = int(
                            await conn.fetchval(
                                "SELECT user_id FROM twitch_users WHERE username = $1 AND guild_id = $2",
                                username,
                                ctx.guild.id,
                            )
                        )

                        if user_id and broadcaster_id == user_id:
                            response = session.delete(url, headers=self.headers)
                            await conn.execute(
                                "DELETE FROM twitch_users WHERE user_id = $1 AND guild_id = $2",
                                user_id,
                                ctx.guild.id,
                            )
                            break

        await self.bot.db.fetch_table_data("twitch_users")
        return await ctx.reply(
            f"Unsubscribed from {f'{count} streamer(s)' if count != 0 else username}.",
            ephemeral=True,
        )

    async def twitch_to_discord(
        self, data
    ) -> Optional[discord.Message]:  # LET MEMBERS CUSTOMISE EVERYTHING (thumbnail, title, description, footer, timestamp...)
        async with self.bot.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                twitch_id: int = int(data["subscription"]["condition"]["broadcaster_user_id"])
                broadcaster_user_login: str = data["event"]["broadcaster_user_login"]
                username: str = data["event"]["broadcaster_user_name"]

                guilds = await conn.fetch("SELECT * FROM twitch_users WHERE user_id = $1", twitch_id)
                for guild in guilds:
                    try:
                        result = await conn.fetchrow(
                            "SELECT message_text, channel_id FROM server_data WHERE guild_id = $1 AND event_type = 'twitch'",
                            guild["guild_id"],
                        )
                        message_text, channel_id = (
                            result[0],
                            result[1],
                        )  # SEND DEFAULT STREAM MESSAGE INSTEAD IF NOT message_text

                        if message_text is None:
                            message_text = f"Hey there! {username} just started the stream."

                        twitch_embed = discord.Embed(
                            title=f"{username} started streaming",
                            description=f"{message_text}\n\nhttps://www.twitch.tv/{broadcaster_user_login}",
                            color=cs.TWITCH_COLOR,
                        )
                        twitch_embed.set_thumbnail(
                            url="https://mlpnk72yciwc.i.optimole.com/cqhiHA-5_fN-hee/w:350/h:350/q:90/rt:fill/g:ce/https://bleedingcool.com/wp-content/uploads/2019/09/twitch-logo-icon-2019.jpg"
                        )

                        channel: discord.TextChannel = self.bot.get_channel(int(channel_id)) if channel_id else None
                        if channel:
                            await channel.send(embed=twitch_embed)

                    except Exception as e:
                        print(e)
                        continue

                    # for row in results:
                    # message_text = row['message_text']
                    # channel_id = row['channel_id']

    async def event_subscription_list(
        self,
    ):  # RETURNS ALL SUBSCRIPTIONS FOR A CERTAIN CLIENT_ID (?)
        response: aiohttp.ClientResponse = await self.session.get(HELIX_URL, headers=self.headers)
        data = await response.json()

        # return data['data'] -> make it a property?

        # Print the response to show the list of subscriptions
        for i in data["data"]:
            print(i["condition"]["broadcaster_user_id"])
            print(i["type"])
        print(response["data"])

    # UNSUBSCRIBE FROM ALL (OWNER)
    async def unsubscribe_from_all_eventsubs(self: Self):
        response: aiohttp.ClientResponse = await self.session.get(HELIX_URL, headers=self.headers)
        response.json()

        count = 0
        if not response["data"]:
            print("No events to unsubscribe from.")
            return

        for subscription in response["data"]:
            subscription_id = subscription["id"]
            url = f"https://api.twitch.tv/helix/eventsub/subscriptions?id={subscription_id}"
            response = self.bot.http_session.delete(url, headers=self.headers)
            count += 1

        print(f"Unsubscribed from {count} event(s).")
