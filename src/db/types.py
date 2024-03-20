from enum import Enum, auto


class QuestType(Enum):
    KILL_ENEMIES = 0
    GET_ITEMS = auto()
    TRAVEL_DIST = auto()
    WIN_PVP = auto()
    EARN_COINS = auto()
    EARN_MEDALS = auto()
    MERGE_CARDS = auto()
    CATCH_FISH = auto()


class RewardType(Enum):
    COINS = 0
    GEMS = auto()
