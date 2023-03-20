from pydantic.dataclasses import dataclass

from .loader import load_json

FISH = load_json("fish")


@dataclass
class Fish:
    fish: list[str]
    base_wait: int
    rwd_bonus: float
    chance: float


for name, node in FISH.items():
    FISH[name] = Fish(**node)
