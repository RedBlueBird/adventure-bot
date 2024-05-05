from pydantic import BaseModel

from resources.json_loader import load_json


class Minigame(BaseModel):
    rules: list[str]
    img: str | None = None


MINIGAMES: dict[str, Minigame] = {}
raw_minigames = load_json("minigames")
for name, game in raw_minigames.items():
    MINIGAMES[name] = Minigame(**game)
