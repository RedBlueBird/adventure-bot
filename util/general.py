import math
import datetime as dt


def time_converter(seconds: str | int) -> str:
    """
    Returns a string representation of the amount of time given in seconds.
    :param seconds: The amount of seconds to convert.
    :return: A string representation of how many days, hours, etc. that is.
    """
    seconds = max(0, int(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

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


def time_til_midnight() -> str:
    dts = dt.datetime.now()
    # https://stackoverflow.com/a/45986036/12128483
    return time_converter(
        ((24 - dts.hour - 1) * 60 * 60) + ((60 - dts.minute - 1) * 60) + (60 - dts.second)
    )


def log_level_gen(i: int) -> int:
    """
    Since this function logarithmically decreases, i has to increase
    dramatically for the value to go from 5 to 4 than from, say, 10 to 9.
    :param i: Any positive number.
    :return: An integer between 1 and 10, inclusive.
    """
    if i <= 1:
        return 10
    val = 10 - math.floor(math.log(i - 1) / math.log(2))
    return min(10, max(1, val))  # Clamp between 1 and 10


def level_xp(lvl: int) -> int:
    """:return: The amount of XP required to advance to the next level, given the current one."""
    return math.floor(int((lvl ** 2) * 40 + 60))


def clamp(i: int, lo: int, hi: int) -> int:
    return max(lo, min(i, hi))
