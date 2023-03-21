import typing as t
import dataclasses
from copy import deepcopy

from pydantic import validator, root_validator, ConfigDict, Extra
from pydantic.dataclasses import dataclass

from .loader import load_json
from ..util.constants import SCALE

ITEMS = load_json("items")
ITEM_ABB = load_json("item_abbreviations")


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
    buy: int | None = dataclasses.field(default=None)

    extra: dict[str, t.Any] = dataclasses.field(default_factory=dict)

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
    ret = deepcopy(ITEMS[name])

    variable = [
        "block", "absorb", "heal", "tramp", "damage",
        "self_damage", "crush", "revenge", "lich_revenge"
    ]
    for attr in ret.extra:
        if attr in variable:
            ret[attr] = round(ret[attr] * max_stat / 100)
    return ret


for abb, n in ITEM_ABB.items():
    ITEM_ABB[abb] = n.lower()
for n, i in ITEMS.items():
    ITEMS[n] = Item(**i)
