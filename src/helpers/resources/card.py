import typing as t

from pydantic import BaseModel

from helpers.json_loader import load_json


class Card(BaseModel):
    id: str
    name: str
    cost: int
    rarity: t.Literal["NA", "M", "EX", "C", "R", "E", "L"]

    description: str
    brief: str

    def __str__(self):
        return f"[{self.rarity}/{self.cost}] **{self.name}**"


def card(name: str) -> Card | None:
    name = " ".join(name.lower().replace("_", " ").split())
    return CARDS.get(name, None)


raw_cards = load_json("cards")
CARDS: dict[str, Card] = {}
for id_, node in raw_cards.items():
    CARDS[id_] = Card(**node, id=id_)
