import copy

from resources import CARDS, CARDS_TEMP, SCALE


def cards_dict(lvl: str | int, name: str):
    level = int(lvl)
    lvl = SCALE[1] ** (level - 1) * SCALE[0]
    inverse_level = 1.01 ** (level * -1 + 1) * SCALE[0]

    name = name.lower()
    if name not in CARDS:
        return None

    card = copy.deepcopy(CARDS[name])
    param = [
        "block",
        "absorb",
        "heal",
        "tramp",
        "damage",
        "self_damage",
        "pierce_damage",
        "crush",
        "revenge",
        "lich_revenge",
    ]
    for i in card:
        if i in param:
            card[i] = round(card[i] * lvl)
        elif i in ["c" + j for j in param]:
            card[i] = round(card[i] * lvl)
        elif i.startswith("eff_app"):
            for side in card[i]:
                for effect in card[i][side]:
                    for attr in card[i][side][effect]:
                        if attr in param:
                            card[i][side][effect][attr] = round(card[i][side][effect][attr] * lvl)
        elif i == "inverse_damage":
            card[i] = round(card[i] * inverse_level)
        elif i == "on_hand":
            for k in card[i]:
                if k in [
                    "block",
                    "absorb",
                    "heal",
                    "tramp",
                    "damage",
                    "self_damage",
                    "crush",
                    "revenge",
                    "lich_revenge",
                ]:
                    card[i][k] = round(card[i][k] * lvl)
                elif k == "eff_app":
                    card[i][k][0] = round(card[i][k][0] * lvl)
    return card


def cards_dict_temp(lvl: int, name: str):
    if name.lower() not in CARDS_TEMP:
        return None

    card = copy.deepcopy(CARDS_TEMP[name.lower()])
    attributes = ["dmg", "cdmg"]
    for attribute in attributes:
        if attribute in card:
            card[attribute] = card[attribute] * lvl
    return card
