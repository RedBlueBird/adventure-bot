import json
import typing as t

with open("txts/icons.json") as json_file:
    ICON: t.Final = json.load(json_file)
with open("txts/admins.json") as json_file:
    ADMINS: t.Final = set(json.load(json_file))

CONVERT: t.Final = {
    "burn": ICON["burn"],
    "poison": ICON["pois"],
    "recover": ICON["rec"],
    "curse": ICON["curs"],
    "stun": ICON["stun"],
    "bullseye": ICON["eye"],
    "berserk": ICON["bers"],
    "freeze": ICON["frez"],
    "chill": ICON["chil"],
    "restore": ICON["rest"],
    "seriate": ICON["seri"],
    "feeble": ICON["feeb"]
}

DECK: t.Final = {
    "[♠ Ace]": 11, "[♠ Two]": 2, "[♠ Three]": 3, "[♠ Four]": 4, "[♠ Five]": 5,
    "[♠ Six]": 6, "[♠ Seven]": 7, "[♠ Eight]": 8, "[♠ Nine]": 9, "[♠ Ten]": 10,
    "[♠ Jack]": 10, "[♠ Queen]": 10, "[♠ King]": 10, "[♥ Ace]": 11, "[♥ Two]": 2,
    "[♥ Three]": 3, "[♥ Four]": 4, "[♥ Five]": 5, "[♥ Six]": 6, "[♥ Seven]": 7,
    "[♥ Eight]": 8, "[♥ Nine]": 9, "[♥ Ten]": 10, "[♥ Jack]": 10, "[♥ Queen]": 10,
    "[♥ King]": 10, "[♦ Ace]": 11, "[♦ Two]": 2, "[♦ Three]": 3, "[♦ Four]": 4,
    "[♦ Five]": 5, "[♦ Six]": 6, "[♦ Seven]": 7, "[♦ Eight]": 8, "[♦ Nine]": 9,
    "[♦ Ten]": 10, "[♦ Jack]": 10, "[♦ Queen]": 10, "[♦ King]": 10, "[♣ Ace]": 11,
    "[♣ Two]": 2, "[♣ Three]": 3, "[♣ Four]": 4, "[♣ Five]": 5, "[♣ Six]": 6,
    "[♣ Seven]": 7, "[♣ Eight]": 8, "[♣ Nine]": 9, "[♣ Ten]": 10, "[♣ Jack]": 10,
    "[♣ Queen]": 10, "[♣ King]": 10
}
ACES: t.Final = [f"[{s} Ace]" for s in ["♠", "♥", "♦", "♣"]]

SCALE: t.Final = 50, 1.05
PREF: t.Final = "a."

# Loads in all the necessary json files as dictionaries
with open("txts/cards.json") as json_file:
    CARDS: t.Final = json.load(json_file)
with open("txts/item_abbreviations.json") as json_file:
    ITEM_ABB: t.Final = json.load(json_file)
with open("txts/items.json") as json_file:
    ITEMS: t.Final = json.load(json_file)
with open("txts/mobs.json") as json_file:
    MOBS: t.Final = json.load(json_file)
with open("txts/effects.json") as json_file:
    EFFX: t.Final = json.load(json_file)

with open("txts/card_list.json") as json_file:
    CARD_LIST: t.Final = json.load(json_file)
