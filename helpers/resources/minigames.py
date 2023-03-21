import dataclasses

from pydantic.dataclasses import dataclass

from helpers.json_loader import load_json

MINIGAMES = load_json("minigames")


@dataclass
class Minigame:
    rules: list[str]
    img: str | None = dataclasses.field(default=None)


for name, game in MINIGAMES.items():
    MINIGAMES[name] = Minigame(**game)
