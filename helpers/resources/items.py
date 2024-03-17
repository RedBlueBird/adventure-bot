import typing as t
from copy import deepcopy

from pydantic import field_validator, model_validator, ConfigDict, Extra, BaseModel

from helpers.json_loader import load_json
from .constants import SCALE


class Item(BaseModel):
    model_config = ConfigDict(extra=Extra.allow)

    name: str
    abb: str
    description: str
    brief: str
    rarity: t.Literal["NA", "C", "R", "E", "L"]

    attacks: int
    acc: int
    crit: int
    eff_acc: int
    one_use: bool
    in_battle: bool

    sta_gain: int

    weight: int
    sell: int
    buy: int | None = None

    @field_validator("name")
    @classmethod
    def name_lower(cls, v: str):
        return v.lower()

    @model_validator(mode="after")
    def abb_matches(self):
        assert ITEM_ABB.get(self.abb, self.name) == self.name
        return self


def item(name: str, max_stat=100 * SCALE[0]) -> Item:
    name = ITEM_ABB.get(name.lower(), name.lower())
    
    # these stats vary according to max_stat
    variable = {
        "block", "absorb", "heal", "tramp", "damage",
        "self_damage", "crush", "revenge", "lich_revenge"
    }
    ret = deepcopy(ITEMS[name])
    for attr in ret.model_extra:
        if attr in variable:
            ret.model_extra[attr] = round(ret.model_extra[attr] * max_stat / 100)
    return ret


ITEM_ABB: dict[str, str] = load_json("item_abbreviations")
raw_items = load_json("items")
ITEMS: dict[str, Item] = {}
for n, i in raw_items.items():
    ITEMS[n] = Item(**i)
