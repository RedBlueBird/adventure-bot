import typing as t
from collections import abc

import discord

from exceptions import *
import db
import resources as r

T = t.TypeVar("T")


def is_admin() -> abc.Callable[[T], T]:
    """Checks if the calling user is an owner of the bot"""

    async def predicate(context: commands.Context) -> bool:
        if context.author.id not in r.ADMINS:
            raise UserNotAdmin
        return True

    return commands.check(predicate)


def not_preoccupied(action: str = "doing something"):
    async def predicate(ctx: commands.Context) -> bool:
        db.lock_user(ctx.author.id, ctx.command.qualified_name, action)
        return True

    return commands.check(predicate)


def is_registered():
    """Check if the user is registered in the bot."""

    async def predicate(ctx: commands.Context) -> bool:
        if not db.Player.select().where(db.Player.id == ctx.author.id).exists():
            raise UserNotRegistered
        return True

    return commands.check(predicate)


def level_check(lvl: int):
    """Check if the user is of the given level. Must be followed by an is_registered() decorator."""

    async def predicate(ctx: commands.Context) -> bool:
        player = db.Player.get_by_id(ctx.author.id)
        if player.level < lvl:
            raise UserSkillIssue(lvl)
        return True

    return commands.check(predicate)


def valid_reply(
    replies: list[str] | str,
    authors: list[discord.Member] | discord.Member,
    channels: list[discord.TextChannel] | discord.TextChannel,
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
        return any(msg.content.lower().startswith(f"{r.PREF}{s}") for s in replies)

    return _valid_reply


def valid_reaction(
    reactions: list[str] | str,
    reactors: list[discord.Member] | discord.Member,
    msg: list[discord.Message] | discord.Message,
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
