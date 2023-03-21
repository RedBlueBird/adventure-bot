import typing as t
import dataclasses

from pydantic import validator, root_validator
from pydantic.dataclasses import dataclass

from .loader import load_json

CARDS = load_json("cards")


@dataclass
class Card:
    name: str
    cost: int
    rarity: t.Literal["NA", "M", "EX", "C", "R", "E", "L"]

    description: str
    brief: str


for name, node in CARDS.items():
    CARDS[name] = Card(**node)
print(CARDS)
