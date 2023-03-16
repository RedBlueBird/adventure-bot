import discord

from .assets import items_dict
from .constants import BP_CAP


def get_bp_weight(bp: dict[str, int]):
    return sum(items_dict(i)["weight"] for i in bp)


def clear_bp(bp: dict[str, int]):
    return {i: amt for i, amt in bp.items() if amt > 0}


def fulfill_requirement(i, p_inv):
    req_fulfill = True
    req_items_to_take = {}
    pre_message = None
    if len(i) == 4:
        for x in i[3]["req"]:
            if not req_fulfill:
                break
            if x == "item":
                for y in i[3]["req"][x]:
                    if y.lower() in p_inv:
                        if i[3]["req"][x][y][0] <= p_inv[y.lower()] and req_fulfill:
                            if i[3]["req"][x][y][1] == "taken":
                                req_items_to_take[y.lower()] = i[3]["req"][x][y][0]
                        else:
                            req_fulfill = False
                            break
                    else:
                        req_fulfill = False
                        break

    if req_fulfill:
        for x in req_items_to_take:
            p_inv[x] -= req_items_to_take[x]
        p_inv = clear_bp(p_inv)
    else:
        pre_message = "You don't have the items needed to do this!"

    return [req_fulfill, p_inv, pre_message]


def chest_storage(level):
    storage = {7: 100, 13: 150, 19: 175, 25: 200, 30: 225, 100: 250}
    for i in storage:
        if level < i:
            return storage[i]


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
            amt = store[i]
            inv.append(
                f"{descr} {i.title()} - {'∞' if amt == 'x' else amt}"
            )

    capacity = BP_CAP if container == "Backpack" else chest_storage(lvl)
    inv.append(f"Storage used - {get_bp_weight(store)}/{capacity}")

    return "\n".join(inv)
