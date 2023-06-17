import random
from helpers import resources as r
from helpers.battle import Player
from helpers.util import cards_dict, rarity_cost

BASIC_ATTRS = [
    ["block","block"],
    ["damage","dmg"],
    ["absorb","absorb"],
    ["self_damage", "dmg"],
    ["heal", "heal"],
    ["revenge", "dmg"],
    ["clear_eff_all", ""],
    ["draw", "book"]
]
EFF_ATTRS = ["eff", "eff_app", "spawn"]


class Card:
    def __init__(self, lvl: int, name: str, owner: Player = None):
        self.owner = owner
        self.lvl = lvl
        self.display_name = f"**[{rarity_cost(name)}] {name}** lv: {lvl}"
        self.card = cards_dict(lvl, name)

    def get_energy_cost(self):
        return self.card["cost"]

    def write_attr(
            self,
            card_attr: str, icon_attr: str,
            target: Player, crit: bool = False, is_icon: bool = True, is_dotted = False
    ):
        icon_name = icon_attr
        if is_icon:
            if icon_attr in r.ICON:
                icon_name = r.ICON[icon_attr]
            elif icon_attr in r.I_CONVERT:
                icon_name = r.I_CONVERT[icon_attr]

        self.owner.dialogue.append(
            f"{'•' if is_dotted else '‎ ‎ '} {card_attr} "
            f"{icon_name}{r.ICON['crit'] if crit else ''}"
            f"» #{target.id}{target.icon}"
        )

    def get_basics_written(self, target: Player, crit: bool = False):
        used_any = False
        is_dotted = False
        for attr, icon_name in BASIC_ATTRS:
            # If cdamage field doesn't exist in the cards json, use damage field instead cdamage even if crit = true
            curr_attr = attr
            curr_attr = f"{'c' if crit else ''}{curr_attr}"
            if curr_attr not in self.card:
                curr_attr = attr
            if curr_attr not in self.card:
                continue
            is_dotted = False
            if used_any == False:
                used_any = True
                is_dotted = True

            side_target = target
            if attr.startswith("self_"):
                side_target = self.owner

            amt = self.card[curr_attr]
            if attr == "revenge":
                amt = round(amt * (1 - side_target.hp / side_target.max_hp) ** 2)
                attr = "damage"
            if attr == "clear_eff_all":
                side_target.dialogue.append("• All effects cleared")
                continue

            self.write_attr(card_attr=amt, icon_attr=icon_name, target=side_target, crit=crit, is_dotted=is_dotted)

    def use_basics(self, side_target: Player, attr: str, amt: int):
        worked = False
        if attr == "damage":
            side_target.hp += min(amt, side_target.absorb)
            side_target.hp -= max(0, amt - (side_target.block + side_target.absorb))
            side_target.hp = min(side_target.hp, side_target.max_hp)
            if amt > side_target.block + side_target.absorb:
                worked = True
        
        if attr == "block":
            side_target.block += amt
            worked = True
        
        if attr == "absorb":
            side_target.absorb += amt
            worked = True
        
        if attr == "heal":
            side_target.hp = min(side_target.hp + amt, side_target.max_hp)
            worked = True
        
        if attr == "draw":
            side_target.hand_size = min(6, side_target.hand_size + amt)
        
        return worked
            
    def get_basics_used(self, target: Player, crit: bool = False):
        worked = False
        used_any = False
        for attr, icon_name in BASIC_ATTRS:
            curr_attr = f"{'c' if crit else ''}{attr}"
            if curr_attr not in self.card:
                curr_attr = attr
            if curr_attr not in self.card:
                continue
            used_any = True

            side_target = target 
            if attr.startswith("self_"):
                side_target = self.owner
                attr = attr[len("self_"):]

            amt = self.card[curr_attr]
            if attr == "revenge":
                amt = round(amt * (1 - side_target.hp / side_target.max_hp) ** 2)
                attr = "damage"
            if attr == "clear_eff_all":
                for effect in side_target.effects:
                    side_target.effects[effect] = 0

            worked = self.use_basics(side_target, attr, amt)
        return worked or (worked == used_any)

    def get_effects_written(self, target: Player, crit: bool = False):
        for attr in EFF_ATTRS:
            curr_attr = f"{'c' if crit else ''}{attr}"
            if curr_attr not in self.card:
                curr_attr = attr
            if curr_attr not in self.card:
                continue

            for side in self.card[curr_attr]:
                for effect in self.card[curr_attr][side]:
                    side_target = target if side == "target" else self.owner
                    effect_dir = self.card[curr_attr][side][effect]
                    
                    if attr == "eff":
                        self.write_attr(effect_dir, effect, side_target, crit)
                    
                    if attr == "eff_app":
                        effect_count = min(target.effects[effect], effect_dir["cap"])
                        self.write_attr(effect_dir["damage"]*effect_count, effect, side_target, crit)
                        if effect_dir["clear"]:
                             self.write_attr(-effect_count, effect, side_target, crit)
                    
                    if attr == "spawn":
                        self.write_attr(effect_dir[effect], Card(self.lvl, effect, side_target).display_name, side_target, crit, False)

    def get_effects_used(self, target: Player, crit: bool = False):
        for attr in EFF_ATTRS:
            curr_attr = f"{'c' if crit else ''}{attr}"
            if curr_attr not in self.card:
                curr_attr = attr
            if curr_attr not in self.card:
                continue

            for side in self.card[curr_attr]:
                for effect in self.card[curr_attr][side]:
                    side_target = target if side == "target" else self.owner
                    effect_dir = self.card[curr_attr][side][effect]   

                    if attr == "eff":
                        # Effects applied this turn should not decrease by 1 at end of turn cuz they arent used yet
                        # Use negative sign to mark effects that are just applied
                        if effect not in side_target.effects:
                            side_target.effects[effect] = 0

                        if side_target.effects[effect] > 0:
                            side_target.effects[effect] += effect_dir   
                        else:
                            side_target.effects[effect] -= effect_dir
                    
                    if attr == "eff_app":
                        effect_count = max(0, min(target.effects[effect], effect_dir["cap"]))
                        self.use_basics(side_target, "damage", effect_dir["damage"]*effect_count)
                        if effect_dir["clear"]:
                            side_target.effects[effect] -= effect_count

                    if attr == "spawn":
                        self.insert(random.randint(side_target.hand_size, len(side_target.deck)), Card(self.lvl, effect, side_target))

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
            self.write_attr("25%", "Crit", self.owner, False, False)
        for i in range(self.card[f"{'c' if is_crit else ''}attacks"]):
            self.get_basics_written(target, is_crit)
            self.get_effects_written(target, is_crit)

        print(self.owner.level)

    def use(self, target: Player, crit: bool = False):
        for i in range(self.card[f"{'c' if crit else ''}attacks"]):
            if self.get_basics_used(target, crit):
                self.get_effects_used(target, crit)

    def crit_use(self, target: Player, crit: bool = True):
        self.use(target, crit)
