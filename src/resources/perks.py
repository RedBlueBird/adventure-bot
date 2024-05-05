from pydantic import BaseModel

from resources.json_loader import load_json


class Perk(BaseModel):
    name: str
    description: str
    multiplier: tuple[float, float, float, float, float]


raw_perks = load_json("perks")
PERKS: dict[str, Perk] = {}
for name, perk in raw_perks.items():
    PERKS[name] = Perk(**perk)
