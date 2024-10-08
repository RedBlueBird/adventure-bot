import discord

from resources import BP_CAP, item


def bp_weight(bp: dict[str, int]):
    return sum(item(i).weight * bp[i] for i in bp)


def chest_storage(level: int):
    storage = {7: 100, 13: 150, 19: 175, 25: 200, 30: 225, 100: 250}
    for lvl, space in storage.items():
        if level < lvl:
            return space


def container_embed(store: dict, container: str = "Backpack", lvl: int = 1) -> discord.Embed | str:
    inv = container_str(store, container, lvl)
    return discord.Embed().add_field(name=f"Your {container}:", value=f"```{inv}```")


def container_str(store: dict, container: str = "Backpack", lvl: int = 1):
    ret = []
    if not store:
        ret.append("Nothing, it seems...")
    else:
        for i in store:
            if store[i] <= 0:
                continue
            descr = f"[{item(i).rarity}/{item(i).weight}]"
            ret.append(f"{descr} {i.title()} - {store[i]}")

    capacity = BP_CAP if container == "Backpack" else chest_storage(lvl)
    ret.append(f"Storage used - {bp_weight(store)}/{capacity}")

    return "\n".join(ret)
