from io import BytesIO
from typing import List, Optional, Tuple

import discord
import requests
from PIL import Image, ImageDraw, ImageFont

# rename folder and store datasets and pillow within
DIR = "datasets/pillow/"


def get_center(size: Tuple[int, int], bbsize: Tuple[int, int, int, int]) -> List[float]:
    W, H = size
    _, _, w, h = bbsize

    return [(W-w)/2, (H-h)/2]


def download_pfp(url: str) -> BytesIO:
    resp = requests.get(url)

    return BytesIO(resp.content)


def get_font(text: str, size: int) -> ImageFont.FreeTypeFont:
    if text.isascii():
        return ImageFont.truetype(f"{DIR}LemonMilk.otf", size)

    return ImageFont.truetype(f"{DIR}Arial.ttf", size)


def get_welcome_card(text: str, pfp_url: str, text2: Optional[str] = None) -> Image.Image:
    with Image.open(f"{DIR}images/2TVCKxLS.jpg").convert("RGBA") as base:
        base = base.resize((920, 500))
        txt = Image.new("RGBA", base.size, (255, 255, 255, 0))

        # Get fitting font size
        fontsize = 64
        font = get_font(text, fontsize)
        while font.getlength(text) > (base.size[0] - 80):
            fontsize -= 1
            font = get_font(text, fontsize)

        # Draw text
        d = ImageDraw.Draw(txt)
        bb = d.textbbox((0, 0), text, font=font)
        pos1 = get_center(base.size, bb)
        l, t, r, b = d.textbbox(tuple(pos1), text, font=font)  # noqa: E741
        d.rectangle((l-20, t-20, r+20, b+20), fill=(0, 0, 0, 150))
        d.text(tuple(pos1), text, font=font)

        if text2:
            # Get second font
            font2size = 24
            font2 = get_font(text2, font2size)
            while font2.getlength(text2) > (base.size[0] - 80):
                font2size -= 1
                font2 = get_font(text2, font2size)

            # Draw second text
            bb2 = d.textbbox((0, 0), text2, font=font2)
            pos11 = get_center(base.size, bb2)
            pos11[1] += 80
            l, t, r, b = d.textbbox(tuple(pos11), text2, font=font2)  # noqa: E741
            d.rectangle((l-10, t-10, r+10, b+10), fill=(0, 0, 0, 150))
            d.text(tuple(pos11), text2, font=font2)

        # Paste text
        out = Image.alpha_composite(base, txt)
        base.paste(out)

        # Get profile picture
        pfp = Image.open(download_pfp(pfp_url))
        pfp = pfp.resize((172, 172))

        # Get position for profile picture
        pos2 = get_center(base.size, pfp.getbbox())  # type: ignore
        pos2[1] -= (base.size[1] / 3) - 22
        pos2 = tuple(int(i) for i in pos2)

        # Create border and create profile picture
        mask = Image.open(f"{DIR}images/mask.jpg").convert("L").resize((172, 172))
        mask2 = mask.resize((185, 185))
        border = Image.new("L", (185, 185), 255)
        pos3 = get_center(base.size, border.getbbox())  # type: ignore
        pos3[1] -= (base.size[1] / 3) - 22
        pos3 = tuple(int(i) for i in pos3)
        base.paste(border, pos3, mask2)
        base.paste(pfp, pos2, mask)

        return base
    

async def get_avatar_dominant_color(member: discord.Member | discord.User | discord.ClientUser) -> discord.Colour | None:
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