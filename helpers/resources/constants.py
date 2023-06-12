from helpers.json_loader import load_json

PREF = "a."
SCALE = 50, 1.05

DECK_LVL_REQ = {1: 0, 2: 0, 3: 6, 4: 15, 5: 21, 6: 29}
MAX_CARDS = 500
BP_CAP = 100

CARDS = load_json("cards_temp")
CARDS_TEMP = load_json("cards_temp")
CARD_LIST = load_json("card_list", True)
