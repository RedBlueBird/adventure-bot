from pydantic.dataclasses import dataclass

from .loader import load_json

HTOWN = load_json("hometown")


@dataclass
class HometownChoice:
    next_node: str
    state: str


@dataclass
class HometownNode:
    description: str
    coordinate: tuple[int, int]
    choices: dict[str, HometownChoice]


for name, node in HTOWN.items():
    HTOWN[name] = HometownNode(**node)
