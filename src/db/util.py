from .models import *
import resources as r


def get_deck(uid: int, slot: int = 0) -> list[Card]:
    player = Player.get_by_id(uid)
    slot = player.deck if slot == 0 else slot
    return list(
        Card.select()
        .join(DeckCard)
        .join(Deck)
        .where((Deck.owner == player.id) & (Deck.slot == slot))
    )


def sort_cards(cards: list[Card], order: int):
    keys = [
        lambda c: c.level,
        lambda c: c.name,
        lambda c: c.id,
        lambda c: r.card(c.name).cost,
        lambda c: r.card(c.name).rarity,
    ]
    descending = order % 2 == 1
    cards.sort(key=keys[order // 2], reverse=descending)
