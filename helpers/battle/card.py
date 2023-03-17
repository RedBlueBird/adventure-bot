from helpers import util as u
from helpers.battle import Player
from helpers.util import cards_dict_temp, rarity_cost


class Card:
    def __init__(self, level: int, name: str, owner: Player = None):
        self.owner = owner
        self.level = level
        self.display_name = f"**[{rarity_cost(name)}] {name}** lv: {level}"
        self.card = cards_dict_temp(level, name)

    def get_energy_cost(self):
        return self.card["cost"]

    def get_attribute_written(
            self,
            card_attribute: str, icon_attribute: str,
            target: Player, crit: bool = False
    ):
        if card_attribute in self.card:
            self.owner.dialogue.append(
                f"• {self.card[card_attribute]} "
                f"{u.ICON[icon_attribute]}{u.ICON['crit'] if crit else ''}"
                f"» #{target.id} {target.icon}"
            )

    def write(self, target: Player):
        self.owner.dialogue.append(f"» {self.display_name}")
        self.owner.crit += self.card["crit"]
        if self.owner.crit - self.card["crit"] >= 100:
            self.crit_write(target=target)
            return

        target.inbox.append(self.use)
        self.get_attribute_written(card_attribute="dmg", icon_attribute="dmg", target=target)

    def crit_write(self, target: Player):
        self.owner.crit -= 100

        target.inbox.append(self.crit_use)
        self.get_attribute_written(card_attribute="cdmg", icon_attribute="dmg", target=target, crit=True)

    def use(self, target: Player):
        if "dmg" in self.card:
            target.hp -= self.card["dmg"]

    def crit_use(self, target: Player):
        if "cdmg" in self.card:
            target.hp -= self.card["cdmg"]
