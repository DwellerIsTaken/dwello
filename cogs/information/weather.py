from __future__ import annotations

from discord.ext import commands
import discord, aiohttp, os
from typing import Optional, Any
import text_variables as tv

from utils import BaseCog

class Weather(BaseCog):

    def __init__(self, bot: commands.Bot, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)

    # THINK OF A NEW FOLDER WHERE TO ADD ALL THIS
    @commands.hybrid_command(name="hello",with_app_command=True)
    async def ping_command(self, ctx: commands.Context) -> None:

        return await ctx.send("Hello!") # display more info about bot

    @commands.hybrid_command(name='weather', help="Shows you the temparature in the city you've typed in.", with_app_command=True)
    async def weather(self, ctx: commands.Context, *, city: str) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):


            key = os.getenv('weather_key')
            args = city.lower()

            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://api.openweathermap.org/data/2.5/weather?q={args}&APPID={key}&units=metric') as response:  

                    data = await response.json()
                                            
                    curr_temp = data['main']['temp']
                    curr_feels_like = data['main']['feels_like']
                                            
            if curr_feels_like < 14:
                dress_code = "warm"

            else:
                dress_code = "light"

            payload = f"Right now it is __*{curr_temp}*__ *° Celcius*, but it feels like __*{curr_feels_like}*__ *° Celcius*. \n I recommend wearing {dress_code} clothes outside."

            weather_embed = discord.Embed(
            title = f'Current weather in {args}', 
            description = payload,
            color = tv.color
            )

            weather_embed.set_footer(text=tv.footer)

            weather_embed.set_author(
            name = str(ctx.author.name),
            icon_url = ctx.author.display_avatar
            )

            return await ctx.reply(embed = weather_embed, mention_author=False)
            #await ctx.message.delete()
