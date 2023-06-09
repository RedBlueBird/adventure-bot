from pydantic.dataclasses import dataclass

from helpers.json_loader import load_json


@dataclass
class Effect:
    name: str
    description: str


def effect(name: str) -> Effect:
    return EFFX[name]


raw_effx = load_json("effects")
EFFX: dict[str, Effect] = {}
for n, eff in raw_effx.items():
    EFFX[n] = Effect(**eff)
