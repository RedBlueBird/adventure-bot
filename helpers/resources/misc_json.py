from helpers.json_loader import load_json

# these don't need any validation, just load them in & you're done
ADMINS: set[int] = set(load_json("admins"))
ICON: dict[str, str] = load_json("icons")
LEVELS: list[str] = load_json("levels")
TUTORIAL = load_json("tutorial", True)

I_CONVERT = {
    i: ICON[i[:4]] for i in [
        "poison",
        "recover",
        "curse",
        "stun",
        "bullseye",
        "berserk",
        "freeze",
        "chill",
        "restore",
        "seriate",
        "feeble"
    ]
}
