import copy

from ..resources import ITEMS, ITEM_ABB
from ..resources import SCALE, CARDS, CARDS_TEMP


def cards_dict(lvl: str | int, name: str):
    level = int(lvl)
    lvl = SCALE[1] ** (level - 1) * SCALE[0]
    inverse_level = 1.01 ** (level * -1 + 1) * SCALE[0]

    if name.lower() not in CARDS:
        return {
            "name": "Glitched", "cost": 0, "rarity": "NA",
            "self_damage": 4500, "eff_acc": 100, "attacks": 10,
            "acc": 100, "crit": 100,
            "mod": {}, "description": "None", "requirement": "None",
            "brief": "Created from this bot's glitches."
        }

    card = copy.deepcopy(CARDS[name.lower()])
    basics = ["block", "absorb", "heal", "tramp", "damage", "self_damage", "crush", "revenge", "lich_revenge"]
    for i in card:
        if i in basics:
            card[i] = round(card[i] * lvl)
        elif i.startswith("eff_app"):
            for side in card[i]:
                for effect in card[i][side]:
                    for attr in card[i][side][effect]:
                        if attr in basics:
                            card[i][side][effect][attr] = round( card[i][side][effect][attr] * lvl)
            # c_attr = "_".split(i[len("eff_app"):])
            # card[i][c_attr[0]][c_attr[1]][c_attr[2]] = round(card[i][c_attr[0]][c_attr[1]][c_attr[2]] * lvl)
        elif i == "inverse_damage":
            card[i] = round(card[i] * inverse_level)
        elif i == "on_hand":
            for k in card[i]:
                if k in ["block", "absorb", "heal", "tramp", "damage",
                         "self_damage", "crush", "revenge", "lich_revenge"]:
                    card[i][k] = round(card[i][k] * lvl)
                elif k == "eff_app":
                    card[i][k][0] = round(card[i][k][0] * lvl)
    return card


def cards_dict_temp(lvl: int, name: str):
    if name.lower() not in CARDS_TEMP:
        return {
            "name": "Glitched", "cost": 0, "rarity": "NA",
            "self_damage": 4500, "eff_acc": 100, "attacks": 10,
            "acc": 100, "crit": 100,
            "mod": {}, "description": "None", "requirement": "None",
            "brief": "Created from this bot's glitches."
        }

    card = copy.deepcopy(CARDS_TEMP[name.lower()])
    attributes = ["dmg", "cdmg"]
    for attribute in attributes:
        if attribute in card:
            card[attribute] = card[attribute] * lvl
    return card


def items_dict(name: str, max_stat=100 * SCALE[0]):
    name = ITEM_ABB.get(name.lower(), name.lower())
    item = copy.deepcopy(ITEMS[name])
    for i in item:
        if i in ["block", "absorb", "heal", "tramp", "damage", "self_damage", "crush", "revenge", "lich_revenge"]:
            item[i] = round(item[i] * max_stat / 100)
    return item
