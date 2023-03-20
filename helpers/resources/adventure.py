import dataclasses

from pydantic import root_validator
from pydantic.dataclasses import dataclass

from .loader import load_json

ADVENTURES = load_json("adventure")


@dataclass
class AdventureChoice:
    section: str
    subsec: str
    action: str


@dataclass
class AdventureNode:
    description: str
    ranges: list[tuple[int, int]]
    prob: list[float]

    choices: dict[str, AdventureChoice] | None = dataclasses.field(default=None)
    encounters: dict[str, list[int]] | None = dataclasses.field(default=None)

    @root_validator
    def range_prob_same_len(cls, vals):
        assert len(vals["ranges"]) == len(vals["prob"])
        return vals


for loc, adv in ADVENTURES.items():
    for sec in adv:
        for subsec in adv[sec]:
            for v, option in enumerate(adv[sec][subsec]):
                adv[sec][subsec][v] = AdventureNode(**option)
