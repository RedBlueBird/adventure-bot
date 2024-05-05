import typing as t
from copy import deepcopy

from pydantic import model_validator, ConfigDict, Extra, BaseModel

from resources.json_loader import load_json
from .constants import SCALE


class Item(BaseModel):
    model_config = ConfigDict(extra=Extra.allow)

    id: str
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

    @model_validator(mode="after")
    def abb_matches(self):
        assert ITEM_ABB.get(self.abb, self.id) == self.id
        return self

    def __str__(self):
        return f"[{self.rarity}/{self.weight}] {self.name}"


def item(name: str, max_stat=100 * SCALE[0]) -> Item | None:
    name = ITEM_ABB.get(name.lower(), name.lower())
    if name not in ITEMS:
        return None

    # these stats vary according to max_stat
    variable = {
        "block",
        "absorb",
        "heal",
        "tramp",
        "damage",
        "self_damage",
        "crush",
        "revenge",
        "lich_revenge",
    }
    ret = deepcopy(ITEMS[name])
    for attr in ret.model_extra:
        if attr in variable:
            ret.model_extra[attr] = round(ret.model_extra[attr] * max_stat / 100)
    return ret


ITEM_ABB: dict[str, str] = load_json("item_abbreviations")
raw_items = load_json("items")
ITEMS: dict[str, Item] = {}
for id_, i in raw_items.items():
    ITEMS[id_] = Item(**i, id=id_)
