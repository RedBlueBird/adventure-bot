import typing as t

import discord

from exceptions import *
from helpers import db_manager as dm
import util as u

T = t.TypeVar("T")


def is_admin() -> t.Callable[[T], T]:
    """Checks if the calling user is an owner of the bot"""

    async def predicate(context: commands.Context) -> bool:
        if context.author.id not in u.ADMINS:
            raise UserNotAdmin
        return True

    return commands.check(predicate)


def not_preoccupied(action: str = "doing something"):
    async def predicate(ctx: commands.Context) -> bool:
        a_id = ctx.author.id
        if a_id in dm.queues:
            raise UserPreoccupied(dm.queues[a_id])
        dm.queues[a_id] = action
        return True

    return commands.check(predicate)


def is_registered():
    async def predicate(ctx: commands.Context) -> bool:
        if not dm.is_registered(ctx.author.id):
            raise UserNotRegistered
        return True

    return commands.check(predicate)


def level_check(lvl: int):
    async def predicate(ctx: commands.Context) -> bool:
        if dm.get_user_level(ctx.author.id) < lvl:
            raise UserSkillIssue(lvl)
        return True

    return commands.check(predicate)


def valid_reply(
        replies: list[str] | str,
        authors: list[discord.Member] | discord.Member,
        channels: list[discord.TextChannel] | discord.TextChannel
):
    if not isinstance(replies, list):
        replies = [replies]
    if not isinstance(authors, list):
        authors = [authors]
    if not isinstance(channels, list):
        channels = [channels]

    def _valid_reply(msg: discord.Message):
        if msg.channel not in channels:
            return False
        if msg.author not in authors:
            return False
        return any(msg.content.lower().startswith(f"{u.PREF}{s}") for s in replies)

    return _valid_reply


def valid_reaction(
        reactions: list[str] | str,
        reactors: list[discord.Member] | discord.Member,
        msg: list[discord.Message] | discord.Message
):
    if not isinstance(reactions, list):
        reactions = [reactions]
    if not isinstance(reactors, list):
        reactors = [reactors]
    if not isinstance(msg, list):
        msg = [msg]

    def _valid_reaction(rct: discord.Reaction, author: discord.Member):
        if str(rct.emoji) not in reactions:
            return False
        if author not in reactors:
            return False
        return rct.message.id in [m.id for m in msg]

    return _valid_reaction
