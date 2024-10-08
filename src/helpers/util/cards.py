import math
import random

from resources import CARD_LIST

from .assets import cards_dict
from .general import log_level_gen


def deal_card(lvl: int):
    """Generates a random card for the shop based on the player level."""
    level = log_level_gen(
        random.randint(2 ** (max(0, 5 - (lvl // 4))), 2 ** (10 - math.floor(lvl / 10)))
    )
    return {"level": level, "card": random_card(level, "normal")}


def random_card(energy: int, type_: str) -> str:
    """
    Returns a random card based on type and energy upper bound.
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


def rarity_cost(name: str):
    card = cards_dict(1, str(name))
    return f"{card['rarity']}/{card['cost']}"


def price_factor(name: str) -> int:
    return {r: v + 2 for v, r in enumerate(["R", "E", "L", "EX"])}.get(
        cards_dict(1, name)["rarity"], 1
    )


def card_coin_cost(name: str, lvl: int) -> int:
    return int(1.6**lvl * 50 * price_factor(name))
