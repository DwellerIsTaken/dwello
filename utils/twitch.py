import requests, discord, os

from typing import Optional, Union, Tuple

from discord.ext import commands

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

async def username_to_id(username: str) -> Optional[int]:
        
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

async def event_subscription(ctx: commands.Context, type_: str, username: str) -> Optional[Tuple[discord.Message, dict]]:

    user_id = await username_to_id(username)

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

    # Print the response to confirm whether the subscription was created successfully or not
    return await ctx.reply(f"Added **{username}** to twitch notifications list.",ephemeral=True), response.json()

    # type_ = stream.online

async def event_subscription_list(): # RETURNS ALL SUBSCRIPTIONS FOR A CERTAIN CLIENT_ID
    response = requests.get(helix_url, headers=headers).json()

    # Print the response to show the list of subscriptions
    for i in response['data']:
        print(i['condition']['broadcaster_user_id'])
        print(i['type'])
    print(response['data'])

async def unsubscribe(username: str): # IF ALL: GET ALL TWITCH USERS THAT GUILD IS SUBSCRIBED TO AND UNSUB (what if the same user for multiple guilds)

    user_id = await username_to_id(username)
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