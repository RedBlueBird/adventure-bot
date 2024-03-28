_cmds: dict[int, str] = {}


def set_bat_cmd(uid: int, cmd: str):
    _cmds[uid] = cmd


def get_bat_cmd(uid: int):
    return _cmds.get(uid, "")
