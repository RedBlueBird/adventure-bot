from pydantic import BaseModel, constr

from helpers.json_loader import load_json


class Effect(BaseModel):
    name: constr(to_lower=True)
    description: str


raw_effx = load_json("effects")
EFFX: dict[str, Effect] = {}
for n, eff in raw_effx.items():
    EFFX[n] = Effect(**eff)
