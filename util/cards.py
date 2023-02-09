import random
import math
from string import Template

from .constants import *
from .assets import cards_dict
from .general import log_level_gen


def fill_args(card, level):
    all_param = [
        "block", "absorb", "heal", "tramp", "damage", "self_damage", "crush",
        "revenge", "lich_revenge", "eff_app", "inverse_damage", "on_hand_block",
        "on_hand_absorb", "on_hand_heal", "on_hand_tramp", "on_hand_damage",
        "on_hand_self_damage", "on_hand_crush", "on_hand_revenge",
        "on_hand_lich_revenge", "on_hand_eff_app", "on_hand_inverse_damage"
    ]
    param = [
        "block", "absorb", "heal", "tramp", "damage", "self_damage",
        "crush", "revenge", "lich_revenge", "eff_app",
        "inverse_damage"
    ]

    args = {"level": level}
    for i in card:
        if i in param:
            args[all_param[param.index(i)]] = card[i]
            if i == "eff_app":
                args[all_param[param.index(i)]] = card[i][0]
        if i == "on_hand":
            for k in card[i]:
                if k in param:
                    args[all_param[param.index(k) + 11]] = card[i][k]
                    if k == "eff_app":
                        args[all_param[param.index(k) + 11]] = card[i][k][0]

    return Template(card["description"]).safe_substitute(args)


def add_a_card(player_lvl):
    energy_cost = log_level_gen(
        random.randint(2 ** (max(0, 5 - (player_lvl // 4))),
                       2 ** (10 - math.floor(player_lvl / 10)))
    )
    return f"{energy_cost}.{random_card(energy_cost, 'normal')}"


def random_card(energy: int, edition: str) -> str:
    """
    Returns a random card for the enemy AI.
    :param energy: The amount of energy the enemy has, as to not overspend.
    :param edition: The type of card which to choose.
    :return: The name of the card which the enemy is to play.
    """
    cards = CARD_LIST["cards"]
    fire = CARD_LIST["fire"]
    evil = CARD_LIST["evil"]
    electric = CARD_LIST["electric"]
    defensive = CARD_LIST["defensive"]
    monster = CARD_LIST["monster"]

    finished = False
    if edition == "fire":
        for x in fire:
            if not finished and random.randint(1, 2) == 1 and energy >= int(x):
                return random.choice(fire[x])
    elif edition == "evil":
        for x in evil:
            if not finished and random.randint(1, 2) == 1 and energy >= int(x):
                return random.choice(evil[x])
    elif edition == "electric":
        for x in electric:
            if not finished and random.randint(1, 2) == 1 and energy >= int(x):
                return random.choice(electric[x])
    elif edition == "defensive":
        for x in defensive:
            if not finished and random.randint(1, 2) == 1 and energy >= int(x):
                return random.choice(defensive[x])
    elif edition == "monster":
        return random.choice(monster["1"])

    for x in cards:
        if not finished and random.randint(1, 4) == 1 and energy >= int(x):
            return random.choice(cards[x])
    if not finished:
        return random.choice(cards["1"])


def order_by_cost(cards, direction: int):
    cards_by_cost = {}
    for x in cards:
        if cards_dict(x[4], x[3])["cost"] not in cards_by_cost:
            cards_by_cost[cards_dict(x[4], x[3])["cost"]] = []
        cards_by_cost[cards_dict(x[4], x[3])["cost"]].append(x)

    cards = []
    cost_order = list(cards_by_cost.keys())
    if direction == 0:
        cost_order.sort()
    else:
        cost_order.sort(reverse=True)
    for x in cost_order:
        cards += cards_by_cost[x]

    return cards


def order_by_rarity(cards, direction):
    cards_by_rarity = {r: [] for r in ["EX", "L", "E", "R", "C", "M", "NA"]}
    for x in cards:
        cards_by_rarity[cards_dict(x[4], x[3])["rarity"]].append(x)
    cards = []
    rarity_order = list(cards_by_rarity.keys())
    if direction == 0:
        rarity_order.reverse()
    for x in rarity_order:
        cards += cards_by_rarity[x]
    return cards


def rarity_cost(card_name):
    card = cards_dict(1, str(card_name))
    return f"{card['rarity']}/{card['cost']}"


def price_factor(card_name):
    return {
        r: v + 2 for v, r in enumerate(["R", "E", "L", "EX"])
    }.get(cards_dict(1, card_name)["rarity"], 1)

def compute_card_cost(card_name, card_level) -> int:
    return int(1.6 ** card_level * 50 * price_factor(card_name))
