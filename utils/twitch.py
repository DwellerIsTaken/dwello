import requests, discord, os, asyncpg

from typing import Optional, Union, Tuple

from discord.ext import commands

import text_variables as tv

# Set your app's client ID and secret
CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')

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

helix_url = 'https://api.twitch.tv/helix/eventsub/subscriptions'

class Twitch():
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def username_to_id(self, username: str) -> Optional[int]:
            
            username = username.lower()

            url = f'https://api.twitch.tv/helix/users?login={username}'
            response = requests.get(url, headers=headers).json()

            # The Twitch user ID to subscribe to
            if "data" in response and len(response["data"]) > 0:
                user_id_ = response["data"][0]["id"]
                print(f"The user ID for {username} is {user_id_}")

            else:
                raise Exception(f"Could not find user {username}")
            
            return user_id_
    
    async def id_to_username(self, user_id: int) -> Optional[str]:

        url = f'https://api.twitch.tv/helix/users?id={user_id}'
        response = requests.get(url, headers=headers).json()

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

                user_id = await self.username_to_id(username)

                broadcaster_check_dict = {}

                # List of subscriptions
                response_ = requests.get(helix_url, headers=headers).json()
                
                for i in response_['data']:
                    broadcaster_id = int(i['condition']['broadcaster_user_id'])
                    if broadcaster_id not in broadcaster_check_dict:
                        broadcaster_check_dict[broadcaster_id] = {'types': []}
                    if str(i['type']) not in broadcaster_check_dict[broadcaster_id]['types']:
                        broadcaster_check_dict[broadcaster_id]['types'].append(str(i['type']))

                if user_id in broadcaster_check_dict and type_ in broadcaster_check_dict[user_id]['types']:
                    return await ctx.reply(f"Guild is already subscribed to user **{username}**.", ephemeral=True)
                
                channel_id = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2", ctx.guild.id, "twitch")
                if not channel_id or not self.bot.get_channel(int(channel_id)):
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
                    "Authorization": f"Bearer {access_token}", 
                    "Content-Type": "application/json"
                }

                response = requests.post(helix_url, headers=headers, json=body)

                # add some extra checks here
                # one user now; update later
                await conn.execute("INSERT INTO server_data(guild_id, twitch_id, event_type) VALUES($1, $2, 'twitch')", ctx.guild.id, str(user_id))
                #await conn.execute("UPDATE server_data SET twitch_id = $1 WHERE guild_id = $2 AND event_type = 'twitch'", user_id, ctx.guild.id)
                # Print the response to confirm whether the subscription was created successfully or not
                return await ctx.reply(f"Added **{username}** to twitch notifications list.",ephemeral=True), response.json()

                # type_ = stream.online

    async def event_subscription_list(self): # RETURNS ALL SUBSCRIPTIONS FOR A CERTAIN CLIENT_ID
        response = requests.get(helix_url, headers=headers).json()

        # Print the response to show the list of subscriptions
        for i in response['data']:
            print(i['condition']['broadcaster_user_id'])
            print(i['type'])
        print(response['data'])

    async def unsubscribe(self, username: str): # IF ALL: GET ALL TWITCH USERS THAT GUILD IS SUBSCRIBED TO AND UNSUB (what if the same user for multiple guilds)

        user_id = await self.username_to_id(username)
        response = requests.get(helix_url, headers=headers).json()

        # FINISH

        count = 0
        if not response['data']:
            print("No events to unsubscribe from.")
            return

        for subscription in response['data']:
            subscription_id = subscription['id']
            url = f'https://api.twitch.tv/helix/eventsub/subscriptions?id={subscription_id}'
            response = requests.delete(url, headers=headers)
            count += 1

        print(f"Unsubscribed from {count} event(s).")

    # OUTSIDE OF CLASS CAUSE WILL INTERACT WITH FLASK (?)
    async def twitch_to_discord(self, data) -> None:
        async with await asyncpg.connect(database= os.getenv('pg_name'), user= os.getenv('pg_username'), password= os.getenv('pg_password')) as conn:
            async with conn.transaction():
                twitch_id = data['subscription']['condition']['broadcaster_user_id']
                username = await self.id_to_username(twitch_id)

                guilds = await conn.fetch("SELECT guild_id FROM server_data WHERE twitch_id = $1", twitch_id)
                for guild in guilds:
                    result = await conn.fetchrow("SELECT message_text, channel_id FROM server_data WHERE guild_id = $1", guild['guild_id'])
                    message_text, channel_id = result[0], result[1]

                    twitch_embed = discord.Embed(title= f"{username} started streaming", description= f"{message_text}\n\nhttps://www.twitch.tv/{username}", color= tv.twitch_color)

                    channel = await self.bot.get_channel(int(channel_id)) if channel_id else None
                    if channel:
                        await channel.send(embed = twitch_embed)

                    #for row in results:
                    #message_text = row['message_text']
                    #channel_id = row['channel_id']
