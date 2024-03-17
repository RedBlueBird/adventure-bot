from pydantic import BaseModel

from helpers.json_loader import load_json


class Effect(BaseModel):
    name: str
    description: str


raw_effx = load_json("effects")
EFFX: dict[str, Effect] = {}
for n, eff in raw_effx.items():
    EFFX[n] = Effect(**eff)
