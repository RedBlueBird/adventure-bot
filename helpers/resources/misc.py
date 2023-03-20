from .loader import load_json

# these don't need any validation, just load them in & you're done
ADMINS = set(load_json("admins"))
ICONS = load_json("icons")
LEVELS = load_json("levels")
TUTORIAL = load_json("tutorial", True)
