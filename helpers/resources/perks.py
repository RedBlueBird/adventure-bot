from pydantic.dataclasses import dataclass

from helpers.json_loader import load_json


@dataclass
class Perk:
    name: str
    description: str
    multiplier: tuple[int, int, int, int, int]


raw_perks = load_json("perks")
PERKS: dict[str, Perk] = {}
for name, perk in raw_perks.items():
    PERKS[name] = Perk(**perk)
