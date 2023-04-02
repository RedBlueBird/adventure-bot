import typing as t
from dataclasses import field
from copy import deepcopy

from pydantic import validator, root_validator, ConfigDict, Extra
from pydantic.dataclasses import dataclass

from helpers.json_loader import load_json
from .constants import SCALE


@dataclass(config=ConfigDict(extra=Extra.allow))
class Item:
    name: str
    description: str
    brief: str
    rarity: t.Literal["NA", "C", "R", "E", "L"]

    attacks: int
    acc: int
    crit: int
    eff_acc: int
    one_use: bool
    in_battle: bool
    abb: str
    sta_gain: int

    weight: int
    sell: int
    buy: int | None = None

    extra: dict[str, t.Any] = field(default_factory=dict)

    @validator("name")
    def name_lower(cls, v: str):
        return v.lower()

    @root_validator
    def abb_matches(cls, v):
        assert ITEM_ABB.get(v["abb"], v["name"]) == v["name"]
        return v

    @root_validator(pre=True)
    def build_extra(cls, values: dict[str, t.Any]) -> dict[str, t.Any]:
        """https://stackoverflow.com/a/69618110/12128483"""
        req_fields = {
            field.alias for field in cls.__pydantic_model__.__fields__.values()
        }  # to support alias

        extra = {}
        for field_name in list(values):
            if field_name not in req_fields:
                extra[field_name] = values.pop(field_name)
        values["extra"] = extra
        return values


def item(name: str, max_stat=100 * SCALE[0]) -> Item:
    name = ITEM_ABB.get(name.lower(), name.lower())
    
    # these stats vary according to max_stat
    variable = {
        "block", "absorb", "heal", "tramp", "damage",
        "self_damage", "crush", "revenge", "lich_revenge"
    }
    ret = deepcopy(ITEMS[name])
    for attr in ret.extra:
        if attr in variable:
            ret.extra[attr] = round(ret.extra[attr] * max_stat / 100)
    return ret


ITEM_ABB: dict[str, str] = load_json("item_abbreviations")
raw_items = load_json("items")
ITEMS: dict[str, Item] = {}
for n, i in raw_items.items():
    ITEMS[n] = Item(**i)
