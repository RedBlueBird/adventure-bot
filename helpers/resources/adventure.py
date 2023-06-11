from dataclasses import field

from pydantic import validator, root_validator, PositiveInt
from pydantic.dataclasses import dataclass

from helpers.json_loader import load_json


@dataclass
class ItemReq:
    name: str
    amt: PositiveInt
    taken: bool  # After use, will this item disappear?

    @validator("name")
    def lower_name(cls, name: str):
        return name.lower()


@dataclass
class AdventureChoice:
    section: str
    subsec: str
    action: str | None = None
    reqs: list[ItemReq] = field(default_factory=list)


@dataclass
class SpawnRange:
    lb: int
    ub: int
    weight: float


@dataclass
class Instant:
    trap: str | None = None

    @root_validator
    def only_one(cls, vals):
        assert sum(i is not None for i in vals.values()) == 1
        return vals


@dataclass
class AdventureNode:
    description: str
    spawns: list[SpawnRange]

    instant: Instant | None = None
    choices: dict[str, AdventureChoice] | None = None
    to: AdventureChoice | None = None

    encounters: dict[str, list[float]] = field(default_factory=dict)
    item: tuple[str, tuple[int, int]] | None = None

    @root_validator
    def choices_or_to_not_both(cls, vals):
        assert vals["choices"] is None or vals["to"] is None
        return vals

    @validator("encounters")
    def valid_encounter_probs(cls, e: dict[str, list[float]]):
        assert all(all(0 <= float(p) <= 1 for p in e) for e in e.values())
        return e

    @validator("item")
    def valid_item_ranges(cls, item: tuple[str, tuple[int, int]] | None):
        if item is None:
            return item

        lb, ub = item[1]
        assert lb <= ub
        return item


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