from enum import Enum, unique
from typing import NamedTuple
from random import shuffle


@unique
class Suit(Enum):
    Spade = "♠"
    Heart = "♥"
    Dimond = "♦"
    Club = "♣"

    def __str__(self):
        return self.value


@unique
class Value(Enum):
    N2 = 2
    N3 = 3
    N4 = 4
    N5 = 5
    N6 = 6
    N7 = 7
    N8 = 8
    N9 = 9
    N10 = 10
    J = 11
    Q = 12
    K = 13
    A = 14

    def bj_value(self) -> int:
        if self.value <= 10:
            return self.value
        if self == self.A:
            return 11
        return 11 if self == self.A else 10

    def __str__(self):
        if self.value <= 10:
            return str(self.value)
        return self.name


class Card(NamedTuple):
    suit: Suit
    val: Value

    def __str__(self):
        return str(self.val) + str(self.suit)


class Deck:
    def __init__(self, deck_num: int = 1):
        self.deck = []
        for _ in range(deck_num):
            for s in Suit:
                for v in Value:
                    self.deck.append(Card(s, v))

    def shuffle(self):
        shuffle(self.deck)

    def draw(self):
        return self.deck.pop()

    def draw_n(self, n: int):
        # probably not the most efficient way, but should work for now
        return [self.draw() for _ in range(n)]

    def __len__(self):
        return len(self.deck)
