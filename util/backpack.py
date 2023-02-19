import discord

from .assets import items_dict


def get_bp_weight(i):  # bp will stand for backpack
    storage = 0
    for x in i:
        if not i[x]["items"] == "x":
            storage += items_dict(x)["weight"] * i[x]["items"]
    return storage


def clear_bp(i):
    inv_delete = []
    for x in i:
        if i[x]["items"] == 0:
            inv_delete.append(x)
    for x in inv_delete:
        del i[x]
    return i


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
                        if i[3]["req"][x][y][0] <= p_inv[y.lower()]["items"] and req_fulfill:
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
            p_inv[x]["items"] -= req_items_to_take[x]
        p_inv = clear_bp(p_inv)
    else:
        pre_message = "You don't have the items needed to do this!"
    return [req_fulfill, p_inv, pre_message]


def chest_storage(level):
    storage = {7: 100, 13: 150, 19: 175, 25: 200, 30: 225, 100: 250}
    for i in storage:
        if level < i:
            return storage[i]


def display_backpack(
        store: dict,
        user: discord.User | discord.Member,
        container: str,
        padding=None,
        level=1
):
    inv = ["*" * 30]
    # [[f"{{{'-' * 28}}}"],  ["_" * 30]]   # <-- other possible markers
    capacity = 100 if container == "Backpack" else chest_storage(level)
    if not store:
        if padding is None:
            inv.insert(len(inv), f"Empty {container}!")
        else:
            inv.insert(len(inv), "You lost nothing!")
    else:
        for x in store:
            if store[x]["items"] != "x":
                inv.append(
                    f"[{items_dict(x)['rarity']}/{items_dict(x)['weight']}] {x.title()} - {store[x]['items']} "
                )
            else:
                inv.append(
                    f"[{items_dict(x)['rarity']}/{items_dict(x)['weight']}] {x.title()} - ∞ "
                )

    inv.insert(len(inv), "------------------------------")
    inv.insert(len(inv), f"{container} Storage used - {get_bp_weight(store)}/{capacity}")
    inv.insert(len(inv), "******************************")
    embed = discord.Embed(title=f"Your {container}:", description="```" + "\n".join(inv) + "```")
    embed.set_thumbnail(url=user.avatar.url)

    if padding is None:
        return embed
    else:
        return "\n".join(inv[padding[0]:padding[1]])
