from helpers.json_loader import load_json

# these don't need any validation, just load them in & you're done
ADMINS: set[int] = set(load_json("admins"))
ICON: dict[str, str] = load_json("icons")
LEVELS: list[str] = load_json("levels")
TUTORIAL = load_json("tutorial", True)

I_CONVERT = {
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
