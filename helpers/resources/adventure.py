import dataclasses

from pydantic import root_validator
from pydantic.dataclasses import dataclass

from helpers.json_loader import load_json


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


raw_adventures = load_json("adventure")
ADVENTURES: dict[str, dict[str, dict[str, list[AdventureNode]]]] = {}
for loc, adv in raw_adventures.items():
    ADVENTURES[loc] = {}
    for sec in adv:
        ADVENTURES[loc][sec] = {}
        for subsec in adv[sec]:
            ADVENTURES[loc][sec][subsec] = []
            for v, option in enumerate(adv[sec][subsec]):
                ADVENTURES[loc][sec][subsec].append(AdventureNode(**option))
