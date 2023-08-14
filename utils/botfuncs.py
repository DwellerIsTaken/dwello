from __future__ import annotations

import datetime
import re
from typing import LiteralString

import discord

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


def create_codeblock(content: str) -> str:
    fmt: LiteralString = "`" * 3
    return f"{fmt}py\n{content}{fmt}"
