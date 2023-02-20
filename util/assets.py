import copy

from .constants import *


def cards_dict(card_level, card_name):
    level = int(card_level)
    card_level = SCALE[1] ** (level - 1) * SCALE[0]
    inverse_level = 1.01 ** (level * -1 + 1) * SCALE[0]

    if card_name.lower() not in CARDS:
        return {
            "name": "Glitched", "cost": 0, "rarity": "NA", "self_damage": 4500, "eff_acc": 100, "attacks": 10,
            "acc": 100, "crit": 100, "mod": {}, "description": "None", "requirement": "None",
            "brief": "Created from this bot's glitches."
        }

    card = copy.deepcopy(CARDS[card_name.lower()])
    for i in card:
        if i in ["block", "absorb", "heal", "tramp", "damage", "self_damage", "crush", "revenge", "lich_revenge"]:
            card[i] = round(card[i] * card_level)
        elif i == "eff_app":
            card[i][0] = round(card[i][0] * card_level)
        elif i == "inverse_damage":
            card[i] = round(card[i] * inverse_level)
        elif i == "on_hand":
            for k in card[i]:
                if k in ["block", "absorb", "heal", "tramp", "damage",
                         "self_damage", "crush", "revenge", "lich_revenge"]:
                    card[i][k] = round(card[i][k] * card_level)
                elif k == "eff_app":
                    card[i][k][0] = round(card[i][k][0] * card_level)
    return card


def items_dict(item_name, max_stat=100 * SCALE[0]):
    item_name = ITEM_ABB.get(item_name.lower(), item_name.lower())
    if item_name not in ITEMS:
        return {
            "name": "Glitching", "rarity": "NA", "weight": 0, "attacks": 1, "acc": 100, "crit": 0, "eff_acc": 100,
            "one_use": "False", "in_battle": "False", "abb": "glitching", "sta_gain": 1, "mod": {},
            "description": "None", "brief": "Summons a black hole, ending all life on this planet."
        }

    item = copy.deepcopy(ITEMS[item_name])
    for i in item:
        if i in ["block", "absorb", "heal", "tramp", "damage", "self_damage", "crush", "revenge", "lich_revenge"]:
            item[i] = round(item[i] * max_stat / 100)
        elif i == "eff_app":
            item[i][0] = round(item[i][0] * max_stat / 100)
    return item


def mobs_dict(mob_level: str | int, mob_name: str):
    mob_level = int(mob_level)
    mob_level = SCALE[1] ** (int(mob_level) - 1) * SCALE[0]

    if mob_name.lower() not in MOBS:
        return {
            "name": "Glitcher", "rarity": "NA", "health": -1, "energy_lag": 0, "stamina": -1,
            "death reward": {"coins": 0, "exps": 0},
            "deck": ["Glitched" for _ in range(10)],
            "brief": "Oh no. Whatever this is, it's probably bad."
        }
    mob = copy.deepcopy(MOBS[mob_name.lower()])
    mob["health"] = round(mob["health"] * mob_level)
    return mob


def fx_dict(eff_name: str):
    if eff_name.lower() not in EFFX:
        return {
            "name": "Glitch",
            "description": "This effect oH NO HE COMES"
        }
    return copy.deepcopy(EFFX[eff_name.lower()])


def quest_index(index: str) -> list[str | int]:
    """
    Returns the information for a quest given an index.
    :param index: The quest to get in the form of a string
    :return: A list of strings and ints representing the info about this quest
    """
    indices = index.split(".")[:2]
    all_indices = {
        "1": [5, 10, 20, 50],  # Kill mobs
        "2": [10, 20, 40, 60],  # Collect items
        "3": [500, 1000, 2000, 5000],  # Travel a certain distance
        "4": [1, 3, 5, 10],  # Battle
        "5": [100, 200, 500, 1000],  # Collect coins
        "6": [5, 10, 25, 50],  # Collect medals
        "7": [1, 2, 5, 10],  # Merge cards
        "8": [3, 5, 10, 20]  # Catch fish
    }
    all_rewards = {
        "1": [200, 500, 1000, 2500],
        "2": [0, 1, 2, 4]
    }
    reward_units = {"1": ICON["coin"], "2": ICON["gem"]}
    exp_rewards = {"0": 25, "1": 50, "2": 100, "3": 200, "4": 250}
    all_rarities = {"0": "{C}", "1": "{R}", "2": "{E}", "3": "{L}", "4": "{EX}"}

    return [
        all_indices[indices[1]][int(indices[0][0])],  # requirement
        str(all_rewards[indices[0][1]][int(indices[0][0])]),  # reward amt
        all_rarities[indices[0][0]],  # rarity
        reward_units[indices[0][1]],  # reward unit
        exp_rewards[indices[0][0]]  # exp reward
    ]


def quest_str_rep(quest_type: str | int, amt: str | int):
    """
    Gives a string representation of a quest given the type and the extend to do it to.
    :param quest_type: The type of quest. (types can be found in quest_index's docstring)
    :param amt: The extent to do it to
    :return: A string representation of the quest.
    """
    return {
        1: f"Kill {amt} opponents while adventuring",
        2: f"Accumulate items of weight over {amt} while adventuring",
        3: f"Travel {amt} meters while adventuring",
        4: f"Win {amt} non-friendly PvP battles",
        5: f"Earn {amt} golden coins while adventuring",
        6: f"Earn {amt} medals in PvP battles",
        7: f"Merge {amt} pairs of cards",
        8: f"Catch {amt} fish in the fishing mini-game"
    }[int(quest_type)]
