import typing as t
from dataclasses import field
from copy import deepcopy

from pydantic import validator, root_validator, ConfigDict, Extra
from pydantic.dataclasses import dataclass

from helpers.json_loader import load_json
from .constants import SCALE


@dataclass(config=ConfigDict(extra=Extra.allow))
class DeathReward:
    coins: tuple[int, int] | int
    exps: tuple[int, int] | int
    gems: tuple[int, int] | int = field(default=(0, 0))

    mats: dict[str, int | tuple[int, int]] = field(default_factory=dict)

    @root_validator(pre=True)
    def build_extra(cls, values: dict[str, t.Any]) -> dict[str, t.Any]:
        """https://stackoverflow.com/a/69618110/12128483"""
        req_fields = {
            field.alias for field in cls.__pydantic_model__.__fields__.values()
        }  # to support alias

        mats = {}
        for field_name in list(values):
            if field_name not in req_fields:
                mats[field_name] = values.pop(field_name)
        values["mats"] = mats
        return values


@dataclass
class Trade:
    prob: float
    reqs: list[tuple[str, int]]

    @validator("prob")
    def valid_prob(cls, val: float):
        assert 0 <= val <= 1
        return val


@dataclass
class Mob:
    name: str
    brief: str

    rarity: t.Literal["C", "R", "E", "L"]
    health: int
    energy_lag: int
    stamina: int
    death_rwd: DeathReward

    deck: list[str]
    trades: dict[str, Trade] | None = field(default=None)


def mob(name: str, lvl: int) -> Mob:
    lvl = SCALE[1] ** (lvl - 1) * SCALE[0]
    ret = deepcopy(MOBS[name.lower()])
    ret.health = round(ret.health * lvl)
    return ret


raw_mobs = load_json("mobs")
MOBS: dict[str, Mob] = {}
for n, m in raw_mobs.items():
    MOBS[n] = Mob(**m)
