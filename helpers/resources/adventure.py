import dataclasses

from pydantic import validator, root_validator, PositiveInt
from pydantic.dataclasses import dataclass

from helpers.json_loader import load_json


@dataclass
class ItemReq:
    name: str
    amt: PositiveInt
    taken: bool  # After use, will this item disappear?


@dataclass
class AdventureChoice:
    section: str
    subsec: str
    action: str | None = dataclasses.field(default=None)
    reqs: list[ItemReq] = dataclasses.field(default_factory=list)


@dataclass
class SpawnRange:
    lb: int
    ub: int
    prob: float

    @validator("prob")
    def valid_prob(cls, prob):
        assert 0 <= prob <= 1
        return prob


@dataclass
class AdventureNode:
    description: str
    spawns: list[SpawnRange]

    choices: dict[str, AdventureChoice] | None = dataclasses.field(default=None)
    to: AdventureChoice | None = dataclasses.field(default=None)
    encounters: dict[str, list[float]] = dataclasses.field(default_factory=dict)

    @root_validator
    def choices_or_to_not_both(cls, vals):
        assert vals["choices"] is None or vals["to"] is None
        return vals

    @validator("encounters")
    def valid_encounter_probs(cls, vals):
        assert all(all(0 <= float(p) <= 1 for p in e) for e in vals.values())
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
