import json
import typing as t
import os

dirname = os.path.join(os.path.dirname(__file__), "..", "resources/text")

PREF: t.Final = "a."
SCALE: t.Final = 50, 1.05

DECK_LVL_REQ: t.Final = {1: 0, 2: 0, 3: 6, 4: 15, 5: 21, 6: 29}
MAX_CARDS = 500

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

# Loads in all the necessary JSON files
with open(os.path.join(dirname, "icons.json")) as json_file:
    ICON: t.Final = json.load(json_file)
with open(os.path.join(dirname, "admins.json")) as json_file:
    ADMINS: t.Final = set(json.load(json_file))
with open(os.path.join(dirname, "cards.json")) as json_file:
    CARDS: t.Final = json.load(json_file)
with open(os.path.join(dirname, "item_abbreviations.json")) as json_file:
    ITEM_ABB: t.Final = json.load(json_file)
with open(os.path.join(dirname, "items.json")) as json_file:
    ITEMS: t.Final = json.load(json_file)
with open(os.path.join(dirname, "mobs.json")) as json_file:
    MOBS: t.Final = json.load(json_file)
with open(os.path.join(dirname, "effects.json")) as json_file:
    EFFX: t.Final = json.load(json_file)
with open(os.path.join(dirname, "card_list.json")) as json_file:
    CARD_LIST: t.Final = json.load(json_file)
with open(os.path.join(dirname, "levels.json")) as json_file:
    LEVELS: t.Final = json.load(json_file)
with open(os.path.join(dirname, "hometown.json")) as json_file:
    HTOWN = json.load(json_file)
with open(os.path.join(dirname, "adventure.json")) as json_file:
    ADVENTURES = json.load(json_file)
with open(os.path.join(dirname, "minigames.json")) as json_file:
    MINIGAMES = json.load(json_file)
with open(os.path.join(dirname, "perks.json")) as json_file:
    PERKS = json.load(json_file)
with open(os.path.join(dirname, "tutorial.json")) as json_file:
    TUTORIAL = json.load(
        json_file,
        object_pairs_hook=lambda x: {int(k) if k.isdigit() else k: v for k, v in x},
    )

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
