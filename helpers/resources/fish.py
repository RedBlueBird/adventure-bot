from pydantic.dataclasses import dataclass

from helpers.json_loader import load_json


@dataclass
class Fish:
    fish: list[str]
    base_wait: int
    rwd_bonus: float
    chance: float


raw_fish = load_json("fish")
FISH: dict[str, Fish] = {}
for name, node in raw_fish.items():
    FISH[name] = Fish(**node)
