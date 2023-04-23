import enum
from datetime import datetime
from math import ceil
from typing import Dict, Union

import discord


class Colour(enum.Enum):
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    WHITE = (255, 255, 255)


def make_embed(
        title="",
        description="",
        colour=Colour.WHITE,
        fields: list[Dict[str, Union[str, bool]]] = []
) -> discord.Embed:
    c = colour.value
    embed = discord.Embed(
        title=title,
        description=description,
        colour=discord.Colour.from_rgb(c[0], c[1], c[2])
    )
    for field in fields:
        embed.add_field(
            name=field["name"],
            value=field["value"],
            inline=field["inline"] if "inline" in field else True
        )
    return embed


def get_user_name(interaction: discord.Interaction) -> str:
    return f'{interaction.user.name}#{interaction.user.discriminator}'


def get_unix_time() -> int:
    return round((datetime.utcnow() - datetime(year=1970, month=1, day=1)).total_seconds())


def get_next_ping(unix: int) -> str:
    now = get_unix_time()

    if unix - now <= 0:
        return '**Now**'

    total_minutes = (unix - now) / 60
    minutes = ceil(total_minutes % 60)
    hours = ceil(total_minutes // 60)

    if hours >= 24:
        days = round(hours / 24, 1)
        text = f"`{days}` day{'' if days == 1 else 's'}"
    elif hours == 23 and minutes == 60:
        text = "`1` day"
    elif hours == 0:
        text = f"`{minutes}` minute{'' if minutes == 1 else 's'}"
    else:
        text = f"`{hours}` hour{'' if hours == 1 else 's'} `{minutes}` minute{'' if minutes == 1 else 's'}"

    return text


def get_ping_interval(interval: int, time_intervals: list[tuple[int, str]]) -> str:
    for seconds, time_unit in time_intervals:
        if interval % seconds == 0:
            return f"{str(interval // seconds)} {time_unit}"
