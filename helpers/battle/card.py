import random
from helpers import resources as r
from helpers.battle import Player
from helpers.util import cards_dict_temp, rarity_cost

basic_attributes = [["block","block"],["damage","dmg"], ["absorb","absorb"], ["self_damage", "dmg"],
                    ["heal", "heal"], ["revenge", "dmg"], ["clear_eff_all", ""], ["draw", "book"]]
effect_attributes = ["eff", "eff_app", "spawn"]

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
            target: Player, crit: bool = False, is_icon: bool = True
    ):
        icon_name = icon_attribute
        if is_icon:
            icon_name = r.ICON[icon_attribute]

        self.owner.dialogue.append(
            f"• {card_attribute} "
            f"{icon_name}{r.ICON['crit'] if crit else ''}"
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

            amount = self.card[curr_attribute]
            if attribute == "revenge":
                amount = round(amount * (1 - side_target.hp / side_target.max_hp) ** 2)
                attribute = "damage"
            if attribute == "clear_eff_all":
                side_target.dialogue.append("• All effects cleared")
                continue

            self.write_attribute(card_attribute=amount, icon_attribute=icon_name, target=side_target, crit=crit)

    def use_basics(self, side_target: Player, attribute: str, amount: int):
        worked = False
        if attribute == "damage":
            side_target.hp += min(amount, side_target.absorb)
            side_target.hp -= max(0, amount - (side_target.block + side_target.absorb))
            side_target.hp = min(side_target.hp, side_target.max_hp)
            if amount > side_target.block + side_target.absorb:
                worked = True
        if attribute == "block":
            side_target.block += amount
            worked = True
        if attribute == "absorb":
            side_target.absorb += amount
            worked = True
        if attribute == "heal":
            side_target.hp += max(side_target.hp + amount, side_target.max_hp)
            worked = True
        if attribute == "draw":
            side_target.hand_size = min(6, side_target.hand_size + amount)
        return worked
            
    def get_basics_used(self, target: Player, crit: bool = False):
        worked = False
        used_any = False
        for attribute, icon_name in basic_attributes:
            curr_attribute = f"{'c' if crit else ''}{attribute}"
            if curr_attribute not in self.card:
                curr_attribute = attribute
            if curr_attribute not in self.card:
                continue
            used_any = True

            side_target = target 
            if attribute.startswith("self_"):
                side_target = self.owner
                attribute = attribute[len("self_"):]

            amount = self.card[curr_attribute]
            if attribute == "revenge":
                amount = round(amount * (1 - side_target.hp / side_target.max_hp) ** 2)
                attribute = "damage"
            if attribute == "clear_eff_all":
                for effect in side_target.effects:
                    side_target.effects[effect] = 0

            worked = self.use_basics(side_target, attribute, amount)
        return worked or (worked == used_any)

    def get_effects_written(self, target: Player, crit: bool = False):
        for attribute in effect_attributes:
            curr_attribute = f"{'c' if crit else ''}{attribute}"
            if curr_attribute not in self.card:
                curr_attribute = attribute
            if curr_attribute not in self.card:
                continue

            for side in self.card[curr_attribute]:
                for effect in self.card[curr_attribute][side]:
                    side_target = target if side == "target" else self.owner
                    effect_dir = self.card[curr_attribute][side][effect]
                    
                    if attribute == "eff":
                        self.write_attribute(effect_dir, effect, side_target, crit)
                    if attribute == "eff_app":
                        effect_count = min(target.effects[effect], effect_dir["cap"])
                        self.write_attribute(effect_dir["damage"]*effect_count, effect, side_target, crit)
                        if effect_dir["clear"]:
                             self.write_attribute(-effect_count, effect, side_target, crit)
                    if attribute == "spawn":
                        self.write_attribute(effect_dir[effect], Card(self.level, effect, side_target).display_name, side_target, crit, False)

    def get_effects_used(self, target: Player, crit: bool = False):
        for attribute in effect_attributes:
            curr_attribute = f"{'c' if crit else ''}{attribute}"
            if curr_attribute not in self.card:
                curr_attribute = attribute
            if curr_attribute not in self.card:
                continue

            for side in self.card[curr_attribute]:
                for effect in self.card[curr_attribute][side]:
                    side_target = target if side == "target" else self.owner
                    effect_dir = self.card[curr_attribute][side][effect]   

                    if attribute == "eff":
                        # Effects applied this turn should not decrease by 1 at end of turn cuz they arent used yet
                        # Use negative sign to mark effects that are just applied
                        if effect not in side_target.effects:
                            side_target.effects[effect] = 0

                        if side_target.effects[effect] > 0:
                            side_target.effects[effect] += effect_dir   
                        else:
                            side_target.effects[effect] -= effect_dir
                    if attribute == "eff_app":
                        effect_count = min(target.effects[effect], effect_dir["cap"])
                        self.use_basics(side_target, "damage", effect_dir["damage"]*effect_count)
                        if effect_dir["clear"]:
                            side_target.effects[effect] -= effect_count
                    if attribute == "spawn":
                        self.insert(random.randint(side_target.hand_size, len(side_target.deck)), Card(self.level, effect, side_target))

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
        if "berserk" in self.owner.effects and self.owner.effects["berserk"] > 0:
            self.owner.crit += 25
            self.write_attribute("25%", "Crit", self.owner, False, False)
        for i in range(self.card[f"{'c' if is_crit else ''}attacks"]):
            self.get_basics_written(target, is_crit)
            self.get_effects_written(target, is_crit)

    def use(self, target: Player, crit: bool = False):
        if self.get_basics_used(target, crit):
            self.get_effects_used(target, crit)

    def crit_use(self, target: Player, crit: bool = True):
        self.use(target, crit)
