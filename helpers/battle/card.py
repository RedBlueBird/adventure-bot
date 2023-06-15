from helpers import resources as r
from helpers.battle import Player
from helpers.util import cards_dict_temp, rarity_cost

basic_attributes = [["block","block"],["damage","dmg"], ["absorb","absorb"], ["self_damage", "dmg"],
                    ["heal", "heal"]]

class Card:
    def __init__(self, level: int, name: str, owner: Player = None):
        self.owner = owner
        self.level = level
        self.display_name = f"**[{rarity_cost(name)}] {name}** lv: {level}"
        self.card = cards_dict_temp(level, name)

    def get_energy_cost(self):
        return self.card["cost"]

    def write_attribute(
            self,
            card_attribute: str, icon_attribute: str,
            target: Player, crit: bool = False
    ):
        self.owner.dialogue.append(
            f"• {card_attribute} "
            f"{r.ICON[icon_attribute]}{r.ICON['crit'] if crit else ''}"
            f"» #{target.id} {target.icon}"
        )

    def get_basics_written(self, target: Player, crit: bool = False):
        for attribute, icon_name in basic_attributes:
            # If cdamage field doesn't exist in the cards json, use damage field instead cdamage even if crit = true
            curr_attribute = attribute
            curr_attribute = f"{'c' if crit else ''}{curr_attribute}"
            if curr_attribute not in self.card:
                curr_attribute = attribute
            if curr_attribute not in self.card:
                continue

            side_target = target
            if attribute.startswith("self_"):
                side_target = self.owner

            self.write_attribute(card_attribute=self.card[curr_attribute], icon_attribute=icon_name, target=side_target, crit=crit)

    def get_basics_used(self, target: Player, crit: bool = False):
        worked = False
        for attribute, icon_name in basic_attributes:
            curr_attribute = attribute
            curr_attribute = f"{'c' if crit else ''}{curr_attribute}"
            if curr_attribute not in self.card:
                curr_attribute = attribute
            if curr_attribute not in self.card:
                continue
            
            side_target = target 
            if attribute.startswith("self_"):
                side_target = self.owner
                attribute = attribute[len("self_"):]

            if attribute == "damage":
                side_target.hp += min(self.card[curr_attribute], side_target.absorb)
                side_target.hp -= max(0, self.card[curr_attribute] - (side_target.block + side_target.absorb))
                side_target.hp = min(side_target.hp, side_target.max_hp)
                if self.card[curr_attribute] > side_target.block + side_target.absorb:
                    worked = True
            if attribute == "block":
                side_target.block += self.card[curr_attribute]
                worked = True
            if attribute == "absorb":
                side_target.absorb += self.card[curr_attribute]
                worked = True
            if attribute == "heal":
                side_target.hp += max(side_target.hp + self.card[curr_attribute], side_target.max_hp)
                worked = True
        return True

    def get_effects_written(self, target: Player, crit: bool = False):
        eff = f"{'c' if crit else ''}eff"
        if eff not in self.card:
            crit = False
            eff = "eff"
        if eff not in self.card:
            return
        for side in self.card[eff]:
            for effect in self.card[eff][side]:
                side_target = target if side == "target" else self.owner
                if side == "target":
                    self.write_attribute(self.card[eff][side][effect], effect, side_target, crit)

    def get_effects_used(self, target: Player, crit: bool = False):
        eff = f"{'c' if crit else ''}eff"
        if eff not in self.card:
            crit = False
            eff = "eff"
        if eff not in self.card:
            return
        for side in self.card[eff]:
            for effect in self.card[eff][side]:
                side_target = target if side == "target" else self.owner
                if effect not in side_target.effects:
                    side_target.effects[effect] = 0
                # Effects applied this turn should not decrease by 1 at end of turn cuz they arent used yet
                # Use negative sign to mark effects that are just applied
                if side_target.effects[effect] > 0:
                    side_target.effects[effect] += self.card[eff][side][effect]    
                else:
                    side_target.effects[effect] -= self.card[eff][side][effect] 

    def write(self, target: Player):
        is_crit = False
        if self.owner.crit >= 100:
            is_crit = True
            self.owner.crit -= 100
        if "ccrit" not in self.card and is_crit:
            self.owner.crit += self.card["crit"]
        else:
            self.owner.crit += self.card[f"{'c' if is_crit else ''}crit"]
        target.inbox[self.card[f"{'c' if is_crit else ''}priority"]].append(self.crit_use if is_crit else self.use)

        self.owner.dialogue.append(f"» {self.display_name}")
        self.get_basics_written(target, is_crit)
        self.get_effects_written(target, is_crit)

    def use(self, target: Player, crit: bool = False):
        if self.get_basics_used(target, crit):
            self.get_effects_used(target, crit)

    def crit_use(self, target: Player, crit: bool = True):
        self.use(target, crit)
