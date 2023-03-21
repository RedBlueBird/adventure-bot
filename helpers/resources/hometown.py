from pydantic.dataclasses import dataclass

from helpers.json_loader import load_json


@dataclass
class HometownChoice:
    pos: str
    action: str


@dataclass
class HometownNode:
    description: str
    coordinate: tuple[int, int]
    choices: dict[str, HometownChoice]


htown_raw = load_json("hometown")
HTOWN: dict[str, HometownNode] = {}
for name, node in htown_raw.items():
    HTOWN[name] = HometownNode(**node)
