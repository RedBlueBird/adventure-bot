from .models import Player, Deck, Card, DeckCard, Quest, Deal
from .types import QuestType, QuestRarity, RewardType
from .util import get_deck, sort_cards
from exceptions import UserPreoccupied

_actions: dict[int, tuple[str, str]] = {}


def lock_user(uid: int, cmd: str, action: str):
    if uid in _actions:
        raise UserPreoccupied(_actions[uid][1])
    _actions[uid] = cmd, action


def get_user_action(uid: int):
    return _actions[uid][1] if uid in _actions else None


def change_user_action(uid: int, new_action: str):
    _actions[uid] = _actions[uid][0], new_action


def unlock_user(uid: int, cmd: str):
    if uid in _actions and _actions[uid][0] == cmd:
        del _actions[uid]
