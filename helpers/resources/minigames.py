import dataclasses

from pydantic.dataclasses import dataclass

from helpers.json_loader import load_json

raw_minigames = load_json("minigames")


@dataclass
class Minigame:
    rules: list[str]
    img: str | None = dataclasses.field(default=None)


MINIGAMES: dict[str, Minigame] = {}
for name, game in raw_minigames.items():
    MINIGAMES[name] = Minigame(**game)
