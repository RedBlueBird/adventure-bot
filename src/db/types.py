from enum import Enum, auto
import helpers.resources as r


class QuestType(Enum):
    KILL_ENEMIES = 0
    GET_ITEMS = auto()
    TRAVEL_DIST = auto()
    WIN_PVP = auto()
    EARN_COINS = auto()
    EARN_MEDALS = auto()
    MERGE_CARDS = auto()
    CATCH_FISH = auto()


class QuestRarity(Enum):
    C = 0
    R = auto()
    E = auto()
    L = auto()
    EX = auto()


class RewardType(Enum):
    COINS = 0
    GEMS = auto()

    def emoji(self):
        match self:
            case self.COINS:
                return r.ICONS["coin"]
            case self.GEMS:
                return r.ICONS["gem"]
