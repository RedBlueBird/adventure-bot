import random
import math
from string import Template

from .constants import *
from .assets import cards_dict
from .general import log_level_gen


def fill_args(card, level: int):
    all_param = [
        "block", "absorb", "heal", "tramp", "damage", "self_damage", "crush",
        "revenge", "lich_revenge", "eff_app", "inverse_damage", "on_hand_block",
        "on_hand_absorb", "on_hand_heal", "on_hand_tramp", "on_hand_damage",
        "on_hand_self_damage", "on_hand_crush", "on_hand_revenge",
        "on_hand_lich_revenge", "on_hand_eff_app", "on_hand_inverse_damage"
    ]
    param = [
        "block", "absorb", "heal", "tramp", "damage", "self_damage", "crush",
        "revenge", "lich_revenge", "eff_app", "inverse_damage"
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


def deal_card(lvl: int):
    """Generates a random card for the shop based on the player level."""
    cost = log_level_gen(random.randint(
        2 ** (max(0, 5 - (lvl // 4))),
        2 ** (10 - math.floor(lvl / 10))
    ))
    return f"{cost}.{random_card(cost, 'normal')}"


def random_card(energy: int, type_: str) -> str:
    """
    Returns a random card based on type_ and energy upper bound.
    :param energy: The amount of energy the enemy has.
    :param type_: The type of card to choose.
    :return: The name of the card.
    """

    if type_ == "monster":
        cards = CARD_LIST["monster"]
        return random.choice(cards[1])
    
    if type_ in ["fire", "evil", "electric", "defensive"]:
        cards = CARD_LIST[type_]
        for cost in cards:
            if cost > energy:
                continue
            if random.randint(1, 2) == 1:
                return random.choice(cards[cost])
    
    cards = CARD_LIST["cards"]
    for cost in cards:
        if cost > energy:
            continue
        if random.randint(1, 4) == 1:
            return random.choice(cards[cost])

    return random.choice(cards[1])


def order_by_cost(cards: list[tuple[int, str, int]], reverse: bool = False):
    return sorted(
        cards,
        key=lambda c: cards_dict(c[2], c[1])["cost"],
        reverse=reverse
    )


def order_by_rarity(cards: list[tuple[int, str, int]], reverse: bool = False):
    rarities = ["EX", "L", "E", "R", "C", "M", "NA"]
    weights = {r: i for i, r in enumerate(rarities)}
    return sorted(
        cards,
        key=lambda c: weights[cards_dict(c[2], c[1])["rarity"]],
        reverse=reverse
    )


def rarity_cost(name: str):
    card = cards_dict(1, str(name))
    return f"{card['rarity']}/{card['cost']}"


def price_factor(name: str):
    return {
        r: v + 2 for v, r in enumerate(["R", "E", "L", "EX"])
    }.get(cards_dict(1, name)["rarity"], 1)


def card_coin_cost(name: str, lvl: int) -> int:
    return int(1.6 ** lvl * 50 * price_factor(name))
