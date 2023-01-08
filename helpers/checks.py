import json
import os
from typing import List, Callable, TypeVar

import discord

from exceptions import *
from helpers import db_manager

T = TypeVar("T")


def is_owner() -> Callable[[T], T]:
    """
    This is a custom check to see if the user executing the command is an owner of the bot.
    """
    async def predicate(context: commands.Context) -> bool:
        with open(f"{os.path.realpath(os.path.dirname(__file__))}/../config.json") as file:
            data = json.load(file)
        if context.author.id not in data["owners"]:
            raise UserNotOwner
        return True

    return commands.check(predicate)


def not_blacklisted() -> Callable[[T], T]:
    """
    This is a custom check to see if the user executing the command is blacklisted.
    """
    async def predicate(context: commands.Context) -> bool:
        if await db_manager.is_blacklisted(context.author.id):
            raise UserBlacklisted
        return True

    return commands.check(predicate)


def valid_reply(
        valid_replies: List[str],
        valid_authors: List[discord.User],
        valid_channels: List[discord.TextChannel]
):
    def _valid_reply(msg: discord.Message):
        if msg.channel not in valid_channels:
            return False
        if msg.author not in valid_authors:
            return False
        return any(msg.content.lower().startswith(f"a.{s}") for s in valid_replies)

    return _valid_reply


def valid_reaction(
        valid_reactions: List[str],
        valid_reactors: List[discord.User],
        valid_messages: List[discord.Message]
):
    def _valid_reaction(rct: discord.Reaction, author: discord.User):
        if str(rct.emoji) not in valid_reactions:
            return False
        if author not in valid_reactors:
            return False
        return rct.message.id in [m.id for m in valid_messages]

    return _valid_reaction
