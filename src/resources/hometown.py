from pydantic import model_validator, BaseModel

from resources.json_loader import load_json


class HometownChoice(BaseModel):
    pos: str
    action: str

    @model_validator(mode="before")
    @classmethod
    def parse_list(cls, vals):
        if isinstance(vals, list):
            return {k: v for k, v in zip(["pos", "action"], vals)}
        return vals


class HometownNode(BaseModel):
    description: str
    coordinate: tuple[int, int]
    choices: dict[str, HometownChoice]


htown_raw = load_json("hometown")
HTOWN: dict[str, HometownNode] = {}
for name, node in htown_raw.items():
    HTOWN[name] = HometownNode(**node)
