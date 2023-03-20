from pydantic.dataclasses import dataclass

from .loader import load_json

EFFX = load_json("effects")


@dataclass
class Effect:
    name: str
    description: str


for name, eff in EFFX.items():
    EFFX[name] = Effect(**eff)
