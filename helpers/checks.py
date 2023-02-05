import typing as t

import discord

from exceptions import *
from helpers import db_manager as dm
import util as u

T = t.TypeVar("T")


def is_owner() -> t.Callable[[T], T]:
    """Checks if the calling user is an owner of the bot"""

    async def predicate(context: commands.Context) -> bool:
        if context.author.id not in u.ADMINS:
            raise UserNotOwner
        return True

    return commands.check(predicate)


def not_preoccupied(action: str = "doing something"):
    async def predicate(ctx: commands.Context) -> bool:
        a_id = str(ctx.author.id)
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
        valid_replies: list[str] | str,
        valid_authors: list[discord.Member] | discord.Member,
        valid_channels: list[discord.TextChannel] | discord.TextChannel
):
    if not isinstance(valid_replies, list):
        valid_replies = [valid_replies]
    if not isinstance(valid_authors, list):
        valid_authors = [valid_authors]
    if not isinstance(valid_channels, list):
        valid_channels = [valid_channels]

    def _valid_reply(msg: discord.Message):
        if msg.channel not in valid_channels:
            return False
        if msg.author not in valid_authors:
            return False
        return any(msg.content.lower().startswith(f"{u.PREF}{s}") for s in valid_replies)

    return _valid_reply


def valid_reaction(
        valid_reactions: list[str] | str,
        valid_reactors: list[discord.Member] | discord.Member,
        valid_messages: list[discord.Message] | discord.Message
):
    if not isinstance(valid_reactions, list):
        valid_reactions = [valid_reactions]
    if not isinstance(valid_reactors, list):
        valid_reactors = [valid_reactors]
    if not isinstance(valid_messages, list):
        valid_messages = [valid_messages]

    def _valid_reaction(rct: discord.Reaction, author: discord.Member):
        if str(rct.emoji) not in valid_reactions:
            return False
        if author not in valid_reactors:
            return False
        return rct.message.id in [m.id for m in valid_messages]

    return _valid_reaction
