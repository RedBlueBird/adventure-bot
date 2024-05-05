from pydantic import BaseModel

from resources.json_loader import load_json


class Fish(BaseModel):
    fish: list[str]
    base_wait: int
    rwd_bonus: float
    chance: float


raw_fish = load_json("fish")
FISH: dict[str, Fish] = {}
for name, node in raw_fish.items():
    FISH[name] = Fish(**node)
