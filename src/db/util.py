from .models import *


def get_deck(uid: int, slot: int = 0) -> list[Card]:
    player = Player.get_by_id(uid)
    slot = player.deck if slot == 0 else slot
    return list(
        Card.select()
        .join(DeckCard)
        .join(Deck)
        .where((Deck.owner == player.id) & (Deck.slot == slot))
    )
