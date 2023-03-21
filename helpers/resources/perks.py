from pydantic.dataclasses import dataclass

from helpers.json_loader import load_json

PERKS = load_json("perks")


@dataclass
class Perk:
    name: str
    description: str
    multiplier: tuple[int, int, int, int, int]


for name, perk in PERKS.items():
    PERKS[name] = Perk(**perk)
