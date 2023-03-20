import typing as t

import discord

from .assets import items_dict
from .raw_constants import BP_CAP


def bp_weight(bp: dict[str, int]):
    return sum(items_dict(i)["weight"] * bp[i] for i in bp)


def cleared_bp(bp: dict[str, int]):
    return {i: amt for i, amt in bp.items() if amt > 0}


def req_check(
        reqs: dict[str, tuple[int, t.Literal["keep", "taken"]]],
        inv: dict[str, int]
) -> tuple[bool, str]:
    for r, (amt, take) in reqs.items():
        if amt > inv.get(r, 0):
            return False, "You don't have the items required!"
        if take == "taken":
            inv[r] -= amt

    return True, ""


def chest_storage(lvl: int):
    storage = {7: 100, 13: 150, 19: 175, 25: 200, 30: 225, 100: 250}
    for l, space in storage.items():
        if lvl < l:
            return space


def container_embed(
        store: dict,
        container: str = "Backpack",
        lvl: int = 1
) -> discord.Embed | str:
    inv = container_str(store, container, lvl)
    return discord.Embed() \
        .add_field(name=f"Your {container}:", value=f"```{inv}```")


def container_str(store: dict, container: str = "Backpack", lvl: int = 1):
    inv = []
    if not store:
        inv.append("Nothing, it seems...")
    else:
        for i in store:
            descr = f"[{items_dict(i)['rarity']}/{items_dict(i)['weight']}]"
            inv.append(f"{descr} {i.title()} - {store[i]}")

    capacity = BP_CAP if container == "Backpack" else chest_storage(lvl)
    inv.append(f"Storage used - {bp_weight(store)}/{capacity}")

    return "\n".join(inv)
