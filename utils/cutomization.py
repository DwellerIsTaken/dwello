import matplotlib.colors as clr
from colorthief import ColorThief
from typing import Optional, Tuple
from io import BytesIO
import discord
import PIL

# MAYBE
async def get_avatar_dominant_color(member: Optional[discord.Member]) -> Optional[Tuple[int, int, int]]:
    image = PIL.Image.open(BytesIO(await member.display_avatar.read()))
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
    print(f"RGB: {most_used_colour}")
    return most_used_colour
    #hex_ = clr.to_hex(most_used_colour)
    #return hex_