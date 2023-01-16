import math
import datetime as dt

import discord


def log_level_gen(i: int) -> int:
    """
    Spits out a number given an i from 1 to 10.
    Since this function is logarithmic, i has to increase dramatically to go from, say, 5 to 6,
    and even more so from 8 to 9.
    :param i: Any positive number.
    :return: An integer between 1 and 10, inclusive.
    """
    return min(10, max(1, (10 - math.floor(math.log(i - 1) / math.log(2))))) if i > 1 else 10


# region Utilities
def time_converter(seconds: str | int) -> str:
    """
    Returns a string representation of the amount of time given in seconds.
    :param seconds: The amount of seconds to convert.
    :return: A string representation of how many days, hours, etc. that is.
    """
    seconds = int(seconds)
    if seconds >= 0:
        days = math.floor(seconds / 86400)
        hours = math.floor((seconds - days * 86400) / 3600)
        minutes = math.floor((seconds - days * 86400 - hours * 3600) / 60)
        seconds = seconds - (days * 86400) - (hours * 3600) - (minutes * 60)
        if days != 0:
            return f"{days}d, {hours}h, {minutes}m, and {seconds}s"
        if hours != 0:
            return f"{hours}h, {minutes}m, and {seconds}s"
        elif minutes != 0:
            return f"{minutes}m, and {seconds}s"
        elif seconds > 0:
            return f"{seconds}s"
        else:
            return "Right Now"
    return "Right Now"


def remain_time():
    dts = dt.datetime.now()
    dts = str(time_converter(((24 - dts.hour - 1) * 60 * 60) + ((60 - dts.minute - 1) * 60) + (60 - dts.second)))
    return dts


def uid_converter(name: str) -> str:
    if len(name) > 10:
        if name[2] == "!":
            return name[3: len(name) - 1]
        else:
            return name[2: len(name) - 1]
    return name


def get_user(user, msg: discord.Message):
    if user is not None:
        if "@<" not in str(user) and ">" not in str(user):
            author_id = str(user)
        else:
            author_id = uid_converter(str(user))
    else:
        author_id = str(msg.author.id)

    if msg.guild is None:
        return msg.author

    try:
        member = msg.guild.get_member(int(author_id))
        if member is not None:
            return member
    except:
        pass

    for mem in msg.guild.members:
        if mem.display_name.lower().startswith(user.lower()):
            return mem
        elif mem.name.lower().startswith(user.lower()):
            return mem

    return msg.author
