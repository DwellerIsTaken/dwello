from __future__ import annotations

import difflib
import json
from typing import Any, Optional

import discord
from discord.ext import commands

import constants as cs
from core import Bot, Cog, Context
from utils import ENV


class Weather(Cog):
    def __init__(self, bot: Bot, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)

    @commands.hybrid_command(
        name="weather",
        help="Shows you the temparature in the city you've typed in.",
        with_app_command=True,
    )
    async def weather(self, ctx: Context, *, city: str) -> Optional[discord.Message]:
        if not city:
            return await ctx.reply("Please provide a city or a contry.", mention_author=True)

        key = ENV["OPENWEATHERMAP_KEY"]
        args = city.lower()

        async with self.bot.http_session.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={args}&APPID={key}&units=metric"
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

        # await ctx.message.delete()
