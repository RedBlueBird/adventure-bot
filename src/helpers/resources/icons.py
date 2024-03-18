from pydantic import BaseModel, constr

from helpers.json_loader import load_json


class Icon(BaseModel):
    name: constr(to_lower=True)
    id: int
    animated: bool

    def emoji(self):
        return f"<{'a' if self.animated else ''}:{self.name}:{self.id}>"


raw_icons = load_json("icons")
ICONS = {}
for n, i in raw_icons.items():
    n = n.lower()
    icon = Icon(**i, name=n)
    ICONS[n] = icon
    if "abb" in i:
        ICONS[i["abb"]] = icon
