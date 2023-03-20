import random
import math

from .raw_constants import *
from .assets import cards_dict
from .general import log_level_gen


def deal_card(lvl: int):
    """Generates a random card for the shop based on the player level."""
    cost = log_level_gen(random.randint(
        2 ** (max(0, 5 - (lvl // 4))),
        2 ** (10 - math.floor(lvl / 10))
    ))
    return f"{cost}.{random_card(cost, 'normal')}"


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


def card_coin_cost(name: str, lvl: int) -> int:
    price_factor = {
        r: v + 2 for v, r in enumerate(["R", "E", "L", "EX"])
    }.get(cards_dict(1, name)["rarity"], 1)
    return int(1.6 ** lvl * 50 * price_factor)


def sort_cards(cards: list[tuple[int, str, int]], order: int):
    # Default order is card level descending, then alphabetical order
    cards.sort(key=lambda c: (-c[2], c[1]))

    if order in [1, 2]:  # Sort by card level
        cards.sort(key=lambda c: (c[2], c[1]))

    elif order in [3, 4]:  # Card name (alphabetical order)
        cards.sort(key=lambda c: c[1])

    elif order in [5, 6]:  # Card ID
        cards.sort(key=lambda c: c[0])

    elif order in [7, 8]:  # Energy cost
        cards.sort(key=lambda c: cards_dict(c[2], c[1])["cost"])

    elif order in [9, 10]:  # Rarity
        rarities = ["NA", "M", "C", "R", "E", "L", "EX"]
        weights = {r: i for i, r in enumerate(rarities)}
        cards.sort(key=lambda c: weights[cards_dict(c[2], c[1])["rarity"]])

    if order % 2 == 0:
        cards.reverse()
