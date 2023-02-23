import json
import os

dirname = os.path.join(os.path.dirname(__file__), "..", "resources/text")

PREF = "c."
SCALE = 50, 1.05

DECK_LVL_REQ = {1: 0, 2: 0, 3: 6, 4: 15, 5: 21, 6: 29}
MAX_CARDS = 500
BP_CAP = 100

# JSON automatically converts int keys to string so this is to reverse that
def keys_to_int(x):
    return {int(k) if k.isdigit() else k: v for k, v in x}

# Loads in all the necessary JSON files
with open(os.path.join(dirname, "icons.json")) as json_file:
    ICON = json.load(json_file)
with open(os.path.join(dirname, "admins.json")) as json_file:
    ADMINS = set(json.load(json_file))
with open(os.path.join(dirname, "cards.json")) as json_file:
    CARDS = json.load(json_file)
with open(os.path.join(dirname, "cards_temp.json")) as json_file:
    CARDS_TEMP = json.load(json_file)
with open(os.path.join(dirname, "item_abbreviations.json")) as json_file:
    ITEM_ABB = json.load(json_file)
with open(os.path.join(dirname, "items.json")) as json_file:
    ITEMS = json.load(json_file)
with open(os.path.join(dirname, "mobs.json")) as json_file:
    MOBS = json.load(json_file)
with open(os.path.join(dirname, "effects.json")) as json_file:
    EFFX = json.load(json_file)
with open(os.path.join(dirname, "card_list.json")) as json_file:
    CARD_LIST = json.load(json_file, object_pairs_hook=keys_to_int)
with open(os.path.join(dirname, "levels.json")) as json_file:
    LEVELS = json.load(json_file)
with open(os.path.join(dirname, "hometown.json")) as json_file:
    HTOWN = json.load(json_file)
with open(os.path.join(dirname, "adventure.json")) as json_file:
    ADVENTURES = json.load(json_file)
with open(os.path.join(dirname, "minigames.json")) as json_file:
    MINIGAMES = json.load(json_file)
with open(os.path.join(dirname, "perks.json")) as json_file:
    PERKS = json.load(json_file)
with open(os.path.join(dirname, "tutorial.json")) as json_file:
    TUTORIAL = json.load(json_file, object_pairs_hook=keys_to_int)

CONVERT = {
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
