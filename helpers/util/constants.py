import json
import os

dirname = os.path.join(os.path.dirname(__file__), "../..", "resources/json")

PREF = "a."
SCALE = 50, 1.05

DECK_LVL_REQ = {1: 0, 2: 0, 3: 6, 4: 15, 5: 21, 6: 29}
MAX_CARDS = 500
BP_CAP = 100

with open(os.path.join(dirname, "cards.json")) as json_file:
    CARDS = json.load(json_file)
with open(os.path.join(dirname, "cards_temp.json")) as json_file:
    CARDS_TEMP = json.load(json_file)
