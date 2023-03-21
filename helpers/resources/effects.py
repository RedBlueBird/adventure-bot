from pydantic.dataclasses import dataclass

from .loader import load_json

EFFX = load_json("effects")


@dataclass
class Effect:
    name: str
    description: str


def effect(name: str) -> Effect:
    return EFFX[name]


for n, eff in EFFX.items():
    EFFX[n] = Effect(**eff)
