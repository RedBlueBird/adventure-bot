import typing as t

from pydantic.dataclasses import dataclass

from helpers.json_loader import load_json


@dataclass
class Card:
    name: str
    cost: int
    rarity: t.Literal["NA", "M", "EX", "C", "R", "E", "L"]

    description: str
    brief: str


raw_cards = load_json("cards")
CARDS: dict[str, Card] = {}
for name, node in raw_cards.items():
    CARDS[name] = Card(**node)
