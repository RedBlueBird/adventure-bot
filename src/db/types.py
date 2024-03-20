from enum import Enum


QuestType = Enum(
    "QuestType",
    [
        "KILL_ENEMIES",
        "GET_ITEMS",
        "TRAVEL_DIST",
        "WIN_PVP",
        "EARN_COINS",
        "EARN_MEDALS",
        "MERGE_CARDS",
        "CATCH_FISH",
    ],
    start=0,
)

RewardType = Enum("RewardType", ["COINS", "GEMS"], start=0)
