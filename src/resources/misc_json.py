from resources.json_loader import load_json

# these don't need any validation, just load them in & you're done
ADMINS: set[int] = set(load_json("admins"))
LEVELS: list[str] = load_json("levels")
TUTORIAL = load_json("tutorial", True)

CARDS = load_json("cards_temp")
CARDS_TEMP = load_json("cards_temp")
CARD_LIST = load_json("card_list", True)
