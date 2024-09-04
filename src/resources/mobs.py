import typing as t
from copy import deepcopy
from dataclasses import field

from pydantic import BaseModel, ConfigDict, Extra, field_validator

from resources.json_loader import load_json

from .constants import SCALE


class DeathReward(BaseModel):
    model_config = ConfigDict(extra=Extra.allow)

    coins: tuple[int, int] | int
    exps: tuple[int, int] | int
    gems: tuple[int, int] | int = (0, 0)

    mats: dict[str, int | tuple[int, int]] = field(default_factory=dict)


class Trade(BaseModel):
    reqs: list[tuple[str, int]]
    prob: float = 1

    @field_validator("prob")
    @classmethod
    def valid_prob(cls, val: float):
        assert 0 <= val <= 1
        return val


class Mob(BaseModel):
    name: str
    brief: str

    rarity: t.Literal["C", "R", "E", "L"]
    health: int
    energy_lag: int
    stamina: int
    death_rwd: DeathReward

    deck: list[str]
    trades: dict[str, Trade] | None = None
    dialogue: str = ""  # default arguments have to follow so


def mob(name: str, lvl: int = 1) -> Mob | None:
    name = " ".join(name.lower().replace("_", " ").split())
    if name not in MOBS:
        return None

    mob = deepcopy(MOBS[name])
    hp_scale = SCALE[1] ** (lvl - 1) * SCALE[0]
    mob.health = round(mob.health * hp_scale)

    return mob


raw_mobs = load_json("mobs")
MOBS: dict[str, Mob] = {}
for n, m in raw_mobs.items():
    MOBS[n] = Mob(**m)
