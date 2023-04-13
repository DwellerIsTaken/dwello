import requests, discord, os, asyncpg

from typing import Optional, Union, Tuple, List

from discord.ext import commands

import text_variables as tv
from utils import DB_Operations

# Set your app's client ID and secret
CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')

def get_access_token():

    body = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": 'client_credentials'
    }

    r = requests.post('https://id.twitch.tv/oauth2/token', body)
    keys = r.json()
    access_token = keys['access_token']

    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }

    return access_token, headers

helix_url = 'https://api.twitch.tv/helix/eventsub/subscriptions'

class Twitch:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.access_token, self.headers = get_access_token()
        self.db = DB_Operations(self.bot)

    async def username_to_id(self, username: str) -> Optional[str]:
            
        username = username.lower()

        url = f'https://api.twitch.tv/helix/users?login={username}'
        response = requests.get(url, headers=self.headers).json()

        # The Twitch user ID to subscribe to
        if "data" in response and len(response["data"]) > 0:
            user_id_ = response["data"][0]["id"]
            #print(f"The user ID for {username} is {user_id_}")

        else:
            raise Exception(f"Could not find user {username}")
        
        return user_id_
    
    async def id_to_username(self, user_id: int) -> Optional[str]:

        url = f'https://api.twitch.tv/helix/users?id={user_id}'
        response = requests.get(url, headers=self.headers).json()

        # The Twitch username to subscribe to
        if "data" in response and len(response["data"]) > 0:
            username = response["data"][0]["login"]
            print(f"The username for user ID {user_id} is {username}")

        else:
            raise Exception(f"Could not find user with ID {user_id}")
        
        return username

    async def event_subscription(self, ctx: commands.Context, type_: str, username: str) -> Optional[Tuple[discord.Message, dict]]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                try:
                    user_id = await self.username_to_id(username)

                except:
                    return await ctx.reply(embed=discord.Embed(description= f"Could not find user **{username}**.", color = tv.color), ephemeral=True)

                broadcaster_check_dict = {}

                # List of subscriptions
                response_ = requests.get(helix_url, headers=self.headers).json()
                
                # FIX THE CHECK
                for i in response_['data']:
                    broadcaster_id = int(i['condition']['broadcaster_user_id'])
                    if broadcaster_id not in broadcaster_check_dict:
                        broadcaster_check_dict[broadcaster_id] = {'types': []}
                    if str(i['type']) not in broadcaster_check_dict[broadcaster_id]['types']:
                        broadcaster_check_dict[broadcaster_id]['types'].append(str(i['type']))

                if user_id in broadcaster_check_dict and type_ in broadcaster_check_dict[user_id]['types']:
                    return await ctx.reply(f"Guild is already subscribed to user **{username}**.", ephemeral=True)
                
                channel_id = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, "twitch")
                if not channel_id or not self.bot.get_channel(int(channel_id[0]) if channel_id else None):
                    return await ctx.reply("You must set the channel for twitch notifications first. ```/twitch channel set [#channel]```")
                
                # Set up the request body for creating a subscription
                callback_url = 'https://hitoshi.org/eventsub/callback'
                body = {
                    'type': type_,
                    'version': '1',
                    'condition': {'broadcaster_user_id': user_id},
                    'transport': {
                        'method': 'webhook',
                        'callback': callback_url,
                        'secret': CLIENT_SECRET
                    }
                }

                # Send the API request to create the subscription

                headers = {
                    "Client-ID": CLIENT_ID, 
                    "Authorization": f"Bearer {self.access_token}", 
                    "Content-Type": "application/json"
                }

                response = requests.post(helix_url, headers=headers, json=body)

                # add some extra checks here
                # one user now; update later
                await conn.execute("INSERT INTO twitch_users(username, user_id, guild_id) VALUES($1, $2, $3)", username, int(user_id), ctx.guild.id)
                #await conn.execute("UPDATE server_data SET twitch_id = $1 WHERE guild_id = $2 AND event_type = 'twitch'", user_id, ctx.guild.id)
                # Print the response to confirm whether the subscription was created successfully or not
                
        await self.db.fetch_table_data("twitch_users")
        return await ctx.reply(f"Added **{username}** to twitch notifications list.",ephemeral=True), response.json()

                # type_ = stream.online

    # return a list of users the guild is subscribed to
    async def guild_twitch_subscriptions(self, ctx: commands.Context) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                data = await conn.fetch("SELECT username, user_id FROM twitch_users WHERE guild_id = $1", ctx.guild.id)
                twitch_embed = discord.Embed(title="Twitch subscriptions", color = tv.color)
                twitch_embed.set_thumbnail(url="https://mlpnk72yciwc.i.optimole.com/cqhiHA-5_fN-hee/w:350/h:350/q:90/rt:fill/g:ce/https://bleedingcool.com/wp-content/uploads/2019/09/twitch-logo-icon-2019.jpg")

                if data:
                    for record in data:
                        twitch_id = record['user_id']
                        twitch_name = record['username']
                        #name = await self.id_to_username(twitch_id)
                        twitch_embed.add_field(name=twitch_name, value=twitch_id, inline=False)

                elif not (data[0] if data else None):
                    return await ctx.reply(embed=discord.Embed(description="The guild isn't subscribed to any twitch streamers.", color = tv.color))
                
        return await ctx.reply(embed=twitch_embed)


    async def event_subscription_list(self): # RETURNS ALL SUBSCRIPTIONS FOR A CERTAIN CLIENT_ID (?)
        response = requests.get(helix_url, headers=self.headers).json()

        # Print the response to show the list of subscriptions
        for i in response['data']:
            print(i['condition']['broadcaster_user_id'])
            print(i['type'])
        print(response['data'])

    async def twitch_unsubscribe_from_streamer(self, ctx: commands.Context, username: Union[str, bool]) -> Optional[discord.Message]: # IF ALL: GET ALL TWITCH USERS THAT GUILD IS SUBSCRIBED TO AND UNSUB (what if the same user for multiple guilds)
        async with self.bot.pool.acquire() as conn: # LOOKS SHITTY - SHOULD REWRITE
            async with conn.transaction():

                response = requests.get(helix_url, headers=self.headers).json()

                if not response['data']:
                    return await ctx.reply(embed=discord.Embed(description="No events to unsubscribe from.", color=tv.color), ephemeral=True)
                
                done = 0
                count = 0
                for i in response['data']:
                    subscription_id = i['id']
                    broadcaster_id = int(i['condition']['broadcaster_user_id'])
                    url = f'https://api.twitch.tv/helix/eventsub/subscriptions?id={subscription_id}'

                    if isinstance(username, str):
                        user_id = int(await conn.fetchval("SELECT user_id FROM twitch_users WHERE username = $1 AND guild_id = $2", username, ctx.guild.id))

                        if user_id and broadcaster_id == user_id:
                            response = requests.delete(url, headers=self.headers)
                            await conn.execute("DELETE FROM twitch_users WHERE user_id = $1 AND guild_id = $2", user_id, ctx.guild.id)
                            break

                    elif isinstance(username, bool) and username:
                        response = requests.delete(url, headers=self.headers)
                        if not done:
                            await conn.execute("DELETE FROM twitch_users WHERE guild_id = $1", ctx.guild.id)
                            done = 1
                        count += 1

        await self.db.fetch_table_data("twitch_users")
        return await ctx.reply(f"Unsubscribed from {f'{count} streamer(s)' if count != 0 else username}.", ephemeral=True)

    # OUTSIDE OF CLASS CAUSE WILL INTERACT WITH FLASK (?)
    async def twitch_to_discord(self, data) -> None:
        async with await asyncpg.connect(database= os.getenv('pg_name'), user= os.getenv('pg_username'), password= os.getenv('pg_password')) as conn:
            async with conn.transaction():
                twitch_id = data['subscription']['condition']['broadcaster_user_id']
                username = await self.id_to_username(twitch_id)

                guilds = await conn.fetch("SELECT * FROM twitch_users WHERE user_id = $1", twitch_id)
                for guild in guilds:
                    result = await conn.fetchrow("SELECT message_text, channel_id FROM server_data WHERE guild_id = $1", guild['guild_id'])
                    message_text, channel_id = result[0], result[1]

                    twitch_embed = discord.Embed(title= f"{username} started streaming", description= f"{message_text}\n\nhttps://www.twitch.tv/{username}", color= tv.twitch_color)

                    channel: discord.TextChannel = await self.bot.get_channel(int(channel_id)) if channel_id else None
                    if channel:
                        await channel.send(embed = twitch_embed)

                    #for row in results:
                    #message_text = row['message_text']
                    #channel_id = row['channel_id']
