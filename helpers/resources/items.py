import typing as t
import dataclasses

from pydantic import validator, root_validator
from pydantic.dataclasses import dataclass

from .loader import load_json

ITEMS = load_json("items")
ITEM_ABB = load_json("item_abbreviations")


@dataclass
class Item:
    name: str
    description: str
    brief: str

    rarity: t.Literal["NA", "C", "R", "E", "L"]
    weight: int
    attacks: int
    acc: int
    crit: int
    eff_acc: int
    one_use: bool
    in_battle: bool
    abb: str
    sell: int
    buy: int | None = dataclasses.field(default=None)

    @validator("name")
    def name_lower(cls, v: str):
        return v.lower()

    @root_validator
    def abb_matches(cls, v):
        assert ITEM_ABB.get(v["abb"], v["name"]) == v["name"]
        return v



for abb, name in ITEM_ABB.items():
    ITEM_ABB[abb] = name.lower()
for name, node in ITEMS.items():
    ITEMS[name] = Item(**node)
