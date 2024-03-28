from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:  # https://stackoverflow.com/a/71961824/12128483
    from .card import Card


@dataclass
class Player:
    user: discord.Member = None
    icon: str = ""

    team: int = 0
    id: int = 0

    level: int = 1
    hp: int = 100
    max_hp: int = hp
    block: int = 0
    absorb: int = 0
    stamina: int = 30
    stored_energy: int = 2
    crit: int = 0

    deck: list["Card"] = field(default_factory=list)
    hand_size: int = 4

    dialogue: list[str] = field(default_factory=list)
    inbox: dict[int, list] = field(default_factory=lambda: {1: [], 2: [], 3: []})
    effects: dict = field(default_factory=dict)

    dead: bool = False
    flee: bool = False
    skip: bool = False
