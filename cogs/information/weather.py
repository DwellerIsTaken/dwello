from __future__ import annotations

from discord.ext import commands
import discord, aiohttp, os
from typing import Optional
import text_variables as tv

class Weather(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  # THINK OF A NEW FOLDER WHERE TO ADD ALL THIS
  @commands.hybrid_command(name="hello",with_app_command=True)
  async def ping_command(self, ctx: commands.Context) -> None:

      return await ctx.send("Hello!")

  @commands.hybrid_command(name='weather', help="Shows you the temparature in the city you've typed in.", with_app_command=True)
  async def weather(self, ctx: commands.Context, *, city: str) -> Optional[discord.Message]:
    
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

          weather_embed.set_footer(text=f"This bot was programmed by Dweller_Igor©")

      weather_embed.set_author(
      name = str(ctx.author.name),
      icon_url = ctx.author.display_avatar
      )

      return await ctx.reply(embed = weather_embed, mention_author=False)
      #await ctx.message.delete()
