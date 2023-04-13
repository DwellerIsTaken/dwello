import matplotlib.colors as clr
from colorthief import ColorThief
from typing import Optional, Tuple
from io import BytesIO
import discord
import PIL

# DEFAULT IMAGES DONT WORK
async def get_avatar_dominant_color(member: Optional[discord.Member]) -> Optional[discord.Colour]:
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
    r, g, b = most_used_colour[0], most_used_colour[1], most_used_colour[2]
    return discord.Colour.from_rgb(r, g, b)
    #hex_ = clr.to_hex(most_used_colour)
    #return hex_