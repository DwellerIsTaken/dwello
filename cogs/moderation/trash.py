'''import text_variables as tv
import discord, datetime

#return await timeout(self.bot, ctx, member, duration, period, reason)
async def timeout(bot, ctx, member, duration, period = None, reason = None) -> None:

    time_period_list = ["seconds","minutes","hours","days","weeks"]

    if not period:
        time = datetime.timedelta(hours = duration)

    elif time_period_list[0] in str(period):
        time = datetime.timedelta(seconds = duration)

    elif time_period_list[1] in str(period):
        time = datetime.timedelta(minutes = duration)

    elif time_period_list[2] in str(period):
        time = datetime.timedelta(hours = duration)

    elif time_period_list[3] in str(period):
        time = datetime.timedelta(days = duration)

    elif time_period_list[4] in str(period):
        time = datetime.timedelta(weeks = duration)

    if await member_check(ctx, member, bot) != True:
        return

    if member.is_timed_out() is True:

        if ctx.interaction is None:
            return await ctx.reply("Provided member is already timed out!", mention_author = True)

        else:
            return await ctx.interaction.followup.send("Provided member is already timed out!", ephemeral = True)
            #return await ctx.interaction.response.send_message("Provided member is already timed out!", ephemeral = True)

    if reason is None:
        reason = "Not specified"
    
    ban_embed=discord.Embed(title="Timed out", description=f"Guten tag! \nYou have been timed out in **{ctx.channel.guild.name}**, in case you were wondering. You must have said something wrong or it's just an administrator whom is playing with his toys. In any way, Make Yourself Great Again.\n \n Reason: **{reason}**\n\nTimed out for: `{time}`", color=tv.warn_color)
    ban_embed.set_image(url = "https://c.tenor.com/vZiLS-HKM90AAAAC/thanos-balance.gif")
    ban_embed.set_footer(text=tv.footer)
    ban_embed.timestamp = discord.utils.utcnow()

    try:
        await member.send(embed=ban_embed)

    except discord.HTTPException:
        pass

    embed = discord.Embed(title="User is timed out!", description=f'*Timed out by:* {ctx.author.mention} \n \n**{member}** has been successfully timed out for awhile from this server! \nReason: `{reason}`',color=tv.warn_color)
    embed.set_footer(text = f"Timed out for {time}")
    embed.timestamp = discord.utils.utcnow()

    await ctx.interaction.followup.send("User is successfully timed out.", ephemeral = True)
    await ctx.channel.send(embed=embed, mention_author = False)

    return await member.timeout(time, reason = reason)'''

'''
from aiohttp import web

from discord.ext import commands
import discord

import sys
import os

from utils.twitch import Twitch

from typing import Any, Optional

class AiohttpWeb:

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.twitch: Twitch = Twitch(self.bot)
        self.app: web.Application = web.Application()
        self.app.router.add_post('/api/post', self.handle_post)

    async def handle_post(self, request) -> web.Response:
        data = await request.json()
        print(data)

        await self.twitch.twitch_to_discord(data)

        return web.json_response({"message": "data received by aiohttp: {}".format(data)})

    async def run(self, port: int = 8081):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", port)

        try:
            await self.bot.loop.create_task(site.start())
            await self.bot.loop.create_task(self.bot.wait_until_ready())
            print(f"Web server running on http://localhost:{port}")

        except Exception as e:
            print(f"Failed to start web server: {e}")
'''