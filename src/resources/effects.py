from pydantic import BaseModel, constr

from resources.json_loader import load_json


class Effect(BaseModel):
    name: constr(to_lower=True)
    description: str


def effect(name: str) -> Effect | None:
    name = " ".join(name.lower().replace("_", " ").split())
    return EFFX.get(name, None)


raw_effx = load_json("effects")
EFFX: dict[str, Effect] = {}
for n, eff in raw_effx.items():
    EFFX[n] = Effect(**eff)
