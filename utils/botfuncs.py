from __future__ import annotations

import datetime
import re
from io import BytesIO
from typing import LiteralString, Optional, Union

import discord
from PIL import Image

# MODIFY | FIX
# DO WE NEED THIS?


def apostrophize(word: str) -> str:
    return f"{word}'" if word[-1] == "s" else f"{word}'s"


def is_discord_link(link: str) -> bool:
    url_pattern = re.compile(r"^https://discord\.com/.*$")
    return bool(re.match(url_pattern, link))


def capitalize_greek_numbers(text):
    pattern = r"\b(?=[MDCLXVIΙΙ]+)\b(M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,2})(?!\S))\b"
    return re.sub(pattern, lambda match: match.group().upper(), text, flags=re.IGNORECASE)


def find_greek_numbers(text):
    pattern = r"\b(?=[MDCLXVIΙΙ]+)\b(M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))\b"
    matches = re.findall(pattern, text, re.IGNORECASE)
    return [match[0] for match in matches]


def get_unix_timestamp(_date_string: str, _format: str, /, style: discord.utils.TimestampStyle) -> str:
    _date = datetime.datetime.strptime(_date_string, _format)
    _seconds = (_date - datetime.datetime(1970, 1, 1)).total_seconds()

    if style is None:
        return f"<t:{int(_seconds)}>"
    return f"<t:{int(_seconds)}:{style}>"


async def get_avatar_dominant_color(member: Union[discord.Member, discord.User]) -> Optional[discord.Colour]:
    image = Image.open(BytesIO(await member.display_avatar.read()))
    colours = [
        colour
        for colour in sorted(
            image.getcolors(image.size[0] * image.size[1]),
            key=lambda c: c[0],  # Sorts by most amount of pixels
            reverse=True,
        )
        if colour[-1][-1] != 0  # Ignores transparent pixels
    ]

    most_used_colour = colours[0][1]  # This will be a tuple of the format (RRR, GGG, BBB, AAA)
    r, g, b = most_used_colour[0], most_used_colour[1], most_used_colour[2]
    return discord.Colour.from_rgb(r, g, b)

def create_codeblock(content: str) -> str:
    fmt: LiteralString = "`" * 3
    return f"{fmt}py\n{content}{fmt}"
