import random
import math
from functools import reduce
from typing import List

import discord

import util as u
from util import cards_dict, items_dict, rarity_cost


class Classify:
    """
    Only has an info field containing everything about the given in a single dict.
    Indices start at 1, not 0.
    """
    def __init__(self, given: list):
        self.info = {i + 1: given[i] for i in range(len(list(given)))}


class BattleData:
    """
    Contains the battling functions that are at the CORE of this bot.
    """

    def __init__(self, teams, players, p_ids, decks, backpacks, hps, stamina, counts):
        """
        Setups up the initial battlefield.
        :param teams: The teams on the battlefield that will pitted against each other.
        :param players: The actual players that make up each team
        :param p_ids: The entity ids (enemies have an id of 123)
        :param decks: The decks of each entity
        :param backpacks: The backpacks of each entity
        :param hps: How much health each entity has
        :param stamina: How much stamina each entity has
        :param counts: Total amount of users in the current battle field
        """

        self.teams = teams
        self.inv_teams = {i: k for k, v in teams.items() for i in v}
        self.temporary_cards = ["Distraction", "Virus", "Haunted",
                                "Dark Resurrection"]  # , "Seed", "Sprout", "Sapling"]
        self.neutral_cards = ["Absorb", "Heavy Shield", "Stab", "Shield", "Strike", "Heal", "Multi Punches", "Punch",
                              "Slash", "Terminate", "Distraction", "Beatdown"]
        self.players = Classify(players)
        self.p_ids = Classify(p_ids)
        self.decks = Classify(decks)
        self.backpacks = Classify(backpacks)
        self.hps = Classify(hps)
        self.staminas = Classify(stamina)
        self.stored_energies = Classify([6 for _ in range(counts)])
        self.hand_sizes = Classify([4 for _ in range(counts)])
        self.item_used = Classify([["None", 1] for _ in range(counts)])
        self.descriptions = Classify([[] for _ in range(counts)])
        self.total_damages = Classify([0 for _ in range(counts)])
        self.multipliers = Classify([[0, 0, 0, 0, 0] for _ in range(counts)]) # [damage buff/shield buff/acc buff/crit buff/eff buff]
        self.used_cards = Classify([[] for _ in range(counts)])
        self.effects = Classify([{} for _ in range(counts)])
        self.freeze_skips = Classify([False for _ in range(counts)])
        self.move_numbers = Classify([1 for _ in range(counts)])
        self.turns = 1
        self.afk = 0

        player_orders = list(range(1, 7))
        random.shuffle(player_orders)
        self.pps = dict(zip(player_orders, [u.ICON['ppr'], u.ICON['ppp'], u.ICON['ppw'], u.ICON['ppb'], u.ICON['ppo'], u.ICON['ppg']]))

    def new_line(self, caster):
        """Line breaker for debugging & formatting"""
        self.descriptions.info[caster].append(" \n")

    def eff_to_icon(self, effect):
        converter = {"burn": u.ICON['burn'],
                     "poison": u.ICON['pois'],
                     "recover": u.ICON['rec'],
                     "curse": u.ICON['curs'],
                     "stun": u.ICON['stun'],
                     "bullseye": u.ICON['eye'],
                     "berserk": u.ICON['bers'],
                     "freeze": u.ICON['frez'],
                     "chill": u.ICON['chil'],
                     "restore": u.ICON["rest"],
                     "seriate": u.ICON['seri'],
                     "feeble": u.ICON['feeb']}
        try:
            return converter[effect.lower()]
        except:
            return "null"

    def apply_effects(self, effect, result, caster, target, extra_msg=None):
        if extra_msg is None:
            extra_msg = ""
        if effect in result:
            if result[effect][1] == "self":
                if effect in self.effects.info[caster]:
                    if self.effects.info[caster][effect] < 0:
                        self.effects.info[caster][effect] -= result[effect][0]
                    else:
                        self.effects.info[caster][effect] += result[effect][0]
                else:
                    self.effects.info[caster][effect] = result[effect][0] * -1
                self.descriptions.info[caster].append(f"{u.ICON['alpha']}{extra_msg}{result[effect][0]} "
                                                      f"{self.eff_to_icon(effect)}» "
                                                      f"#{caster}{self.pps[self.inv_teams[caster]]}")
            elif result[effect][1] == "target":
                if effect in self.effects.info[target]:
                    if self.effects.info[target][effect] < 0:
                        self.effects.info[target][effect] -= result[effect][0]
                    else:
                        self.effects.info[target][effect] += result[effect][0]
                else:
                    self.effects.info[target][effect] = result[effect][0] * -1
                self.descriptions.info[caster].append(f"{u.ICON['alpha']}{extra_msg}{result[effect][0]} "
                                                      f"{self.eff_to_icon(effect)}» "
                                                      f"#{target}{self.pps[self.inv_teams[target]]}")

    def execute_effects(self, target):
        """
        Actually applies the effects to the user
        :param target: The user whose effects are on
        """
        ready_to_del = []

        def fire_ice_cancel(user):
            if "chill" in self.effects.info[user] and "burn" in self.effects.info[user]:
                if abs(self.effects.info[user]["chill"]) > abs(self.effects.info[user]["burn"]):
                    self.descriptions.info[user].append(
                        f"{abs(self.effects.info[user]['burn'])}{u.ICON['burn']} {abs(self.effects.info[user]['chill'])}{u.ICON['chil']} canceled out! \n{int(abs(self.effects.info[user]['chill'] - abs(self.effects.info[user]['burn']) * self.effects.info[user]['chill'] / abs(self.effects.info[user]['chill'])))}{u.ICON['chil']} remain")
                    self.effects.info[user]["chill"] -= int(abs(self.effects.info[user]["burn"]) *
                                                            self.effects.info[user]["chill"] /
                                                            abs(self.effects.info[user]["chill"]))
                    del self.effects.info[user]["burn"]

                elif abs(self.effects.info[user]["chill"]) < abs(self.effects.info[user]["burn"]):
                    self.descriptions.info[user].append(
                        f"{abs(self.effects.info[user]['burn'])}{u.ICON['burn']} {abs(self.effects.info[user]['chill'])}{u.ICON['chil']} canceled out! \n{int(abs(self.effects.info[user]['burn'] - abs(self.effects.info[user]['chill']) * self.effects.info[user]['burn'] / abs(self.effects.info[user]['burn'])))}{u.ICON['burn']} remain")
                    self.effects.info[user]["burn"] -= int(abs(self.effects.info[user]["chill"]) *
                                                           self.effects.info[user]["burn"] /
                                                           abs(self.effects.info[user]["burn"]))
                    del self.effects.info[user]["chill"]

                else:
                    self.descriptions.info[user].append(
                        f"{abs(self.effects.info[user]['burn'])}{u.ICON['burn']} "
                        f"{abs(self.effects.info[user]['chill'])}{u.ICON['chil']} canceled out!")
                    del self.effects.info[user]["chill"]
                    del self.effects.info[user]["burn"]

        def deletion_check(eff: str):
            if self.effects.info[target][eff] > 1:
                self.effects.info[target][effect] -= 1
            else:
                ready_to_del.append(eff)

        if not self.effects.info[target]:
            return

        fire_ice_cancel(target)
        for effect in self.effects.info[target]:
            if effect == "burn":
                if not str(self.effects.info[target]["burn"])[0] == "-":
                    self.hps.info[target][0] -= math.ceil(self.hps.info[target][2] / 100 * 4)
                    self.descriptions.info[target].append(f"{self.effects.info[target][effect]} "
                                                          f"{u.ICON['burn']}» -"
                                                          f"{math.ceil(self.hps.info[target][2] / 100 * 4)} "
                                                          f"{u.ICON['hp']}")
                    deletion_check(effect)
                else:
                    self.effects.info[target][effect] = abs(self.effects.info[target][effect])

            elif effect == "poison":
                if str(self.effects.info[target]["poison"])[0] != "-":
                    self.staminas.info[target] -= 1
                    self.descriptions.info[target].append(f"{self.effects.info[target][effect]} "
                                                          f"{u.ICON['pois']}» -1 {u.ICON['sta']}")
                    deletion_check(effect)
                else:
                    self.effects.info[target][effect] = abs(self.effects.info[target][effect])

            elif effect == "feeble":
                if str(self.effects.info[target]["feeble"])[0] != "-":
                    self.descriptions.info[target].append(f"{self.effects.info[target][effect]} "
                                                          f"{u.ICON['feeb']}» "
                                                          f"{round(1.1 ** (self.effects.info[target][effect] * -1) * 100)}% "
                                                          f"{u.ICON['dmg']}")
                    deletion_check(effect)
                else:
                    self.effects.info[target][effect] = abs(self.effects.info[target][effect])

            elif effect == "recover" and self.hps.info[target][0] > 0 and self.hps.info[target][0] > 0:
                if str(self.effects.info[target]["recover"])[0] != "-":
                    if self.hps.info[target][0] + math.ceil(self.hps.info[target][2] / 100 * 4) <= self.hps.info[target][2]:
                        self.hps.info[target][0] += math.ceil(self.hps.info[target][2] / 100 * 4)
                        self.descriptions.info[target].append(f"{self.effects.info[target][effect]} {u.ICON['rec']}» {math.ceil(self.hps.info[target][2] / 100 * 4)} {u.ICON['hp']}")
                    else:
                        self.descriptions.info[target].insert(len(self.descriptions.info[target]),
                                                              f"{self.effects.info[target][effect]} "
                                                              f"{u.ICON['rec']}» "
                                                              f"{self.hps.info[target][2] - self.hps.info[target][0]} "
                                                              f"{u.ICON['hp']}")
                        self.hps.info[target][0] = self.hps.info[target][2]
                    deletion_check(effect)
                else:
                    self.effects.info[target][effect] = abs(self.effects.info[target][effect])

            elif effect == "restore":
                if str(self.effects.info[target]["restore"])[0] != "-":
                    if self.stored_energies.info[target] < 12:
                        self.stored_energies.info[target] += 1
                    self.descriptions.info[target].append(f"{self.effects.info[target][effect]} "
                                                          f"{u.ICON['rest']}» 1 {u.ICON['engy']}")
                    deletion_check(effect)
                else:
                    self.effects.info[target][effect] = abs(self.effects.info[target][effect])

            elif effect == "curse":
                if str(self.effects.info[target]["curse"])[0] != "-":
                    self.descriptions.info[target].append(f"{self.effects.info[target][effect]} "
                                                          f"{u.ICON['curs']}»")
                else:
                    self.effects.info[target][effect] = abs(self.effects.info[target][effect])

            elif effect == "stun":
                if str(self.effects.info[target]["stun"])[0] != "-":
                    self.descriptions.info[target].append(
                        f"{self.effects.info[target][effect]} {u.ICON['stun']}» -20% acc")
                    deletion_check(effect)
                else:
                    self.effects.info[target][effect] = abs(self.effects.info[target][effect])

            elif effect == "bullseye":
                if str(self.effects.info[target]["bullseye"])[0] != "-":
                    self.descriptions.info[target].append(f"{self.effects.info[target][effect]} "
                                                          f"{u.ICON['eye']}» 30% acc")
                    deletion_check(effect)
                else:
                    self.effects.info[target][effect] = abs(self.effects.info[target][effect])

            elif effect == "berserk":
                if str(self.effects.info[target]["berserk"])[0] != "-":
                    self.descriptions.info[target].append(f"{self.effects.info[target][effect]} "
                                                          f"{u.ICON['bers']}» "
                                                          f"{self.effects.info[target][effect] * 20}% "
                                                          f"{u.ICON['dmg']}")
                    deletion_check(effect)
                else:
                    self.effects.info[target][effect] = abs(self.effects.info[target][effect])

            elif effect == "seriate":
                if str(self.effects.info[target]["seriate"])[0] != "-":
                    self.descriptions.info[target].append(
                        f"{self.effects.info[target][effect]} {u.ICON['seri']}» {self.effects.info[target][effect] * 2}% {u.ICON['dmg']}")
                else:
                    self.effects.info[target][effect] = abs(self.effects.info[target][effect])

            elif effect == "freeze":
                if str(self.effects.info[target]["freeze"])[0] == "-":
                    self.effects.info[target][effect] = abs(self.effects.info[target][effect])
                if self.effects.info[target]["freeze"] != 0:
                    self.descriptions.info[target].append(f"{self.effects.info[target][effect]} {u.ICON['frez']}» Frozen")
                deletion_check(effect)

            elif effect == "chill":
                if str(self.effects.info[target]["chill"])[0] != "-":
                    if self.effects.info[target][effect] >= 7:
                        self.apply_effects("freeze",
                                           {"freeze": [math.floor(self.effects.info[target][effect] / 7),
                                                       "self"]},
                                           target, target,
                                           f"{math.floor(self.effects.info[target][effect] / 7) * 7} {u.ICON['chil']}» ")
                        self.effects.info[target][effect] = self.effects.info[target][effect] % 7
                    # self.new_line(effect_user)
                    if self.effects.info[target][effect] != 0:
                        self.descriptions.info[target].append(
                            f"{self.effects.info[target][effect]} {u.ICON['chil']}»")

                    if self.effects.info[target][effect] > 1:
                        if "freeze" not in self.effects.info[target]:
                            self.effects.info[target][effect] -= 1
                    else:
                        ready_to_del.insert(len(ready_to_del), effect)
                else:
                    self.effects.info[target][effect] = abs(self.effects.info[target][effect])

        for x in ready_to_del:
            del self.effects.info[target][x]

    def effects_applier(self, result, caster, blocked, target):
        """
        Applies the effects to the users from the cards that are still in their hand.
        """
        if random.randint(1, 100) <= round(result["eff_acc"]) + self.multipliers.info[caster][4]:  # / accuracy_factor):
            to_apply = ["curse", "seriate"]  # these effects will always be applied
            if not blocked:
                to_apply.extend(["burn", "recover", "stun", "bullseye", "poison", "poison",
                                 "berserk", "chill", "restore", "feeble"])
            for e in to_apply:
                self.apply_effects(e, result, caster, target)

    def execute_card_defense(self, c_level: int, c_name: str, caster, target, activation=None):
        """
        Sets up the defensive parts of the card.
        :param c_level: The level of the card for number crunching
        :param c_name: The name of the card that is being used
        :param caster: The user of the card
        :param target: The entity the card is being used on
        """
        if c_name is None or c_level is None:
            return

        result = cards_dict(c_level, c_name)
        if result["name"] == "Glitched":
            self.staminas.info[caster] -= 1
            result = items_dict(c_name, self.hps.info[target][2])
        if activation is not None:
            result = result[activation]
        def_factor = 1 + self.multipliers.info[caster][1]
        accuracy_factor = self.multipliers.info[caster][2]
        crit_factor = self.multipliers.info[caster][3] if result['crit'] != 0 else 0
        crit_multiplier = 1.5
        stats_factor = 1
        if c_level != -1:
            self.descriptions.info[caster].append(f"**{c_name}** lv: {c_level}")
        else:
            self.descriptions.info[caster].append(f"**{c_name.title()}**")
        if "stun" in self.effects.info[caster]:
            if self.effects.info[caster]["stun"] > 0:
                accuracy_factor -= 20

        if "bullseye" in self.effects.info[caster]:
            if self.effects.info[caster]["bullseye"] > 0:
                accuracy_factor += 30

        if "seriate" in self.effects.info[caster] and result['name'] in self.neutral_cards:
            stats_factor += 0.02 * self.effects.info[caster]['seriate']
            result['seriate'] = [1, "self"]
            self.apply_effects("seriate", result, caster, caster)
            del result['seriate']
        print(self.effects.info[caster])

        if "sta_gain" in result:
            if random.randint(1, 100) <= round(result["acc"] + accuracy_factor):
                print(result)
                print(self.staminas.info[caster])
                print(result["sta_gain"])
                self.staminas.info[caster] += result["sta_gain"]
                if not result["sta_gain"] == 1:
                    self.descriptions.info[caster].append(f"• {result['sta_gain'] - 1} {u.ICON['sta']}")
        # self.new_line(caster)
        if "energy_gain" in result:
            if random.randint(1, 100) <= round(result["acc"] + accuracy_factor):
                self.stored_energies.info[caster] += result["energy_gain"] \
                    if result["energy_gain"] + self.stored_energies.info[caster] < 12 else 12 - self.stored_energies.info[caster]
                self.descriptions.info[caster].append(f"• {result['energy_gain']} {u.ICON['engy']}")
        # self.new_line(caster)
        if "block" in result:
            if random.randint(1, 100) <= round(result["acc"] + accuracy_factor):
                if random.randint(1, 100) <= round(result["crit"] + crit_factor):  # / accuracy_factor):
                    self.hps.info[target][3] += round(result["block"] * crit_multiplier * stats_factor * def_factor)
                    self.descriptions.info[caster].append(f"• {round(result['block'] * crit_multiplier * stats_factor * def_factor)} "
                                                          f"{u.ICON['block']}{u.ICON['crit']}» #{target}"
                                                          f"{self.pps[self.inv_teams[target]]}")
                else:
                    self.hps.info[target][3] += round(result["block"] * stats_factor * def_factor)
                    self.descriptions.info[caster].append(f"• {round(result['block'] * stats_factor * def_factor)} "
                                                          f"{u.ICON['block']}» #{target}"
                                                          f"{self.pps[self.inv_teams[target]]}")
                self.effects_applier(result, caster, False, target)
            else:
                self.descriptions.info[caster].append(f"• {u.ICON['mi']}{u.ICON['ss']}")
        # self.new_line(caster)
        if "absorb" in result:
            if random.randint(1, 100) <= round(result["acc"] + accuracy_factor):
                if random.randint(1, 100) <= round(result["crit"] + crit_factor):  # / accuracy_factor):
                    self.hps.info[target][4] += round(result["absorb"] * crit_multiplier * stats_factor * def_factor)
                    self.descriptions.info[caster].append(f"• {round(result['absorb'] * crit_multiplier * stats_factor * def_factor)} "
                                                          f"{u.ICON['absorb']}{u.ICON['crit']}» #{target}"
                                                          f"{self.pps[self.inv_teams[target]]}")
                else:
                    self.hps.info[target][4] += round(result["absorb"] * stats_factor * def_factor)
                    self.descriptions.info[caster].append(f"• {round(result['absorb'] * stats_factor * def_factor)} "
                                                          f"{u.ICON['absorb']}» #{target}"
                                                          f"{self.pps[self.inv_teams[target]]}")
                self.effects_applier(result, caster, False, target)
            else:
                self.descriptions.info[caster].append(f"• {u.ICON['mi']}{u.ICON['ss']}")
        # self.new_line(caster)
        if "heal" in result:
            for y in range(result["attacks"]):
                if random.randint(1, 100) <= round(result["acc"] + accuracy_factor):
                    if random.randint(1, 100) <= round(result["crit"] + crit_factor):  # / accuracy_factor):
                        if self.hps.info[target][0] > 0 and self.staminas.info[target] > 0:
                            self.total_damages.info[target] -= round(
                                result["heal"] * crit_multiplier * stats_factor)
                        self.descriptions.info[caster].append(
                            f"• {round(result['heal'] * crit_multiplier * stats_factor)} "
                            f"{u.ICON['heal']}{u.ICON['crit']}» "
                            f"#{target}{self.pps[self.inv_teams[target]]}")
                    else:
                        if self.hps.info[target][0] > 0 and self.staminas.info[target] > 0:
                            self.total_damages.info[target] -= round(result["heal"] * stats_factor)
                        self.descriptions.info[caster].append(
                            f"• {round(result['heal'] * stats_factor)} {u.ICON['heal']}» #{target}{self.pps[self.inv_teams[target]]}")
                    self.effects_applier(result, caster, False, target)
                else:
                    self.descriptions.info[caster].append(f"• {u.ICON['mi']}{u.ICON['ss']}")
            # self.new_line(caster)

    def execute_card_offense(self, c_level: int, c_name: str, caster, target, activation=None):
        """
        Sets up the offensive parts of a card.
        :param c_level: The level of the card for number crunching
        :param c_name: The name of the card
        :param caster: The user of the given card
        :param target: The entity that the card is being used on
        """
        if c_name is None or c_level is None:
            return

        result = cards_dict(c_level, c_name)
        if result["name"] == "Glitched":
            result = items_dict(c_name, self.hps.info[target][2])
        if activation is not None:
            result = result[activation]
            self.descriptions.info[caster].append(f"**{c_name}** lv: {c_level} ")
        accuracy_factor = self.multipliers.info[caster][2]
        damage_factor = 1 + self.multipliers.info[caster][0]
        crit_factor = self.multipliers.info[caster][3] if result["crit"] != 0 else 0
        crit_multiplier = 1.5
        extras = True

        if "stun" in self.effects.info[caster]:
            if self.effects.info[caster]["stun"] > 0:
                accuracy_factor -= 20

        if "bullseye" in self.effects.info[caster]:
            if self.effects.info[caster]["bullseye"] > 0:
                accuracy_factor += 30

        if "berserk" in self.effects.info[caster]:
            if self.effects.info[caster]["berserk"] > 0:
                damage_factor += 0.15 * self.effects.info[caster]["berserk"]

        if "seriate" in self.effects.info[caster] and result['name'] in self.neutral_cards:
            damage_factor += 0.02 * self.effects.info[caster]['seriate']

        if "feeble" in self.effects.info[caster]:
            damage_factor *= 1.1 ** (self.effects.info[caster]['feeble'] * -1)

        if "on_eff" in result["mod"] and "freeze" in result["mod"]["on_eff"] and "freeze" in self.effects.info[target]:
            if "acc_gain" in result["mod"]["on_eff"]["freeze"]:
                accuracy_factor += result["mod"]["on_eff"]["freeze"]["acc_gain"]
            if "dmg_gain" in result["mod"]["on_eff"]["freeze"]:
                damage_factor += result["mod"]["on_eff"]["freeze"]["dmg_gain"]

        if "tramp" in result:
            extras = False
            for y in range(result["attacks"]):
                if random.randint(1, 100) <= round(result["acc"] + accuracy_factor):
                    blocked = False
                    if random.randint(1, 100) <= round(result["crit"] + crit_factor):
                        if self.hps.info[target][3] > round(result["tramp"] * crit_multiplier):
                            self.hps.info[target][3] -= round(result["tramp"] * crit_multiplier)
                            self.descriptions.info[caster].append(
                                f"• -{round(result['tramp'] * crit_multiplier)} {u.ICON['block']}» #{target}{self.pps[self.inv_teams[target]]}")
                        elif self.hps.info[target][4] > round(result["tramp"] * crit_multiplier):
                            self.hps.info[target][4] -= round(result["tramp"] * crit_multiplier)
                            self.descriptions.info[caster].append(
                                f"• -{round(result['tramp'] * crit_multiplier)} {u.ICON['absorb']}» #{target}{self.pps[self.inv_teams[target]]}")
                        else:
                            if 0 < self.hps.info[target][3] < round(result["tramp"] * crit_multiplier):
                                self.descriptions.info[caster].append(
                                    f"• -{self.hps.info[target][3]} {u.ICON['block']}")
                                self.hps.info[target][3] = 0
                            elif 0 < self.hps.info[target][4] < round(result["tramp"] * crit_multiplier):
                                self.descriptions.info[caster].append(
                                    f"• -{self.hps.info[target][4]} {u.ICON['absorb']}")
                                self.hps.info[target][4] = 0

                    else:
                        if self.hps.info[target][3] > round(result["tramp"]):
                            self.hps.info[target][3] -= round(result["tramp"])
                            self.descriptions.info[caster].append(
                                f"• -{round(result['tramp'])} {u.ICON['block']}» #{target}{self.pps[self.inv_teams[target]]}")
                        elif self.hps.info[target][4] > round(result["tramp"]):
                            self.hps.info[target][4] -= round(result["tramp"])
                            self.descriptions.info[caster].append(
                                f"• -{round(result['tramp'])} {u.ICON['absorb']}» #{target}{self.pps[self.inv_teams[target]]}")
                        else:
                            if 0 < self.hps.info[target][3] < round(result["tramp"]):
                                self.descriptions.info[caster].append(
                                    f"• -{self.hps.info[target][3]} {u.ICON['block']}» #{target}{self.pps[self.inv_teams[target]]}")
                                self.hps.info[target][3] = 0
                            elif 0 < self.hps.info[target][4] < round(result["tramp"]):
                                self.descriptions.info[caster].append(
                                    f"• -{self.hps.info[target][4]} {u.ICON['absorb']}» #{target}{self.pps[self.inv_teams[target]]}")
                                self.hps.info[target][4] = 0
                    self.effects_applier(result, caster, blocked, target)
                else:
                    self.descriptions.info[caster].append(f"• {u.ICON['mi']}{u.ICON['ss']}")
            # self.new_line(caster)
        if "damage" in result:
            extras = result["damage"] == 0
            for y in range(result["attacks"]):
                if random.randint(1, 100) <= round(result["acc"] + accuracy_factor):
                    blocked = False
                    if random.randint(1, 100) <= round(result["crit"] + crit_factor) and result["damage"] != 0:
                        if (self.hps.info[target][3] < round(
                                result["damage"] * crit_multiplier * damage_factor)
                            and self.hps.info[target][4] < round(
                                    result["damage"] * crit_multiplier * damage_factor)) \
                                or "crit_prc" in result["mod"]:
                            if self.hps.info[target][3] > 0 and not "crit_prc" in result["mod"]:
                                self.total_damages.info[target] += round(
                                    result["damage"] * crit_multiplier * damage_factor -
                                    self.hps.info[target][3])
                            elif self.hps.info[target][4] > 0 and not "crit_prc" in result["mod"]:
                                self.total_damages.info[target] += round(
                                    result["damage"] * crit_multiplier * damage_factor -
                                    self.hps.info[target][4]) - self.hps.info[target][4]
                                if self.hps.info[target][2] < self.hps.info[target][0]:
                                    self.hps.info[target][0] = self.hps.info[target][2]
                            else:
                                self.total_damages.info[target] += round(
                                    result["damage"] * crit_multiplier * damage_factor)
                            if not (self.hps.info[target][3] == 0 and self.hps.info[target][
                                4] == 0) and "crit_prc" not in result["mod"]:
                                if self.hps.info[target][3] > 0:
                                    self.descriptions.info[caster].append(
                                        f"• {round(result['damage'] * crit_multiplier * damage_factor - self.hps.info[target][3])} {u.ICON['dmg']}{u.ICON['crit']} ({self.hps.info[target][3]} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                                elif self.hps.info[target][4] > 0:
                                    self.descriptions.info[caster].append(
                                        f"• {round(result['damage'] * crit_multiplier * damage_factor - self.hps.info[target][4])} {u.ICON['dmg']}{u.ICON['crit']} ({self.hps.info[target][4]} {u.ICON['absorb']})» #{target}{self.pps[self.inv_teams[target]]}")
                            else:
                                if "crit_prc" in result["mod"]:
                                    self.descriptions.info[caster].append(
                                        f"• {round(result['damage'] * crit_multiplier * damage_factor)} {u.ICON['pdmg']}{u.ICON['crit']}» #{target}{self.pps[self.inv_teams[target]]}")
                                else:
                                    self.descriptions.info[caster].append(
                                        f"• {round(result['damage'] * crit_multiplier * damage_factor)} {u.ICON['dmg']}{u.ICON['crit']}» #{target}{self.pps[self.inv_teams[target]]}")
                        else:
                            if self.hps.info[target][3] > 0:
                                blocked = True
                                self.descriptions.info[caster].append(
                                    f"• 0 {u.ICON['dmg']}{u.ICON['crit']} ({self.hps.info[target][3]} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                            elif self.hps.info[target][4] > 0:
                                self.total_damages.info[target] -= round(
                                    result["damage"] * crit_multiplier * damage_factor)
                                if self.hps.info[target][2] < self.hps.info[target][0]:
                                    self.hps.info[target][0] = self.hps.info[target][2]
                                self.descriptions.info[caster].append(
                                    f"• 0 {u.ICON['dmg']}{u.ICON['crit']} ({round(result['damage'] * crit_multiplier * damage_factor)} {u.ICON['absorb']})» #{target}{self.pps[self.inv_teams[target]]}")
                        if "self_damage" in result:
                            self.total_damages.info[caster] += result["self_damage"] * crit_multiplier
                            self.descriptions.info[caster].append(
                                f" {int(result['self_damage'] * crit_multiplier)} {u.ICON['dmg']}{u.ICON['crit']}» #{caster}{self.pps[self.inv_teams[caster]]}")

                    elif result["damage"] != 0:
                        if (self.hps.info[target][3] < round(result["damage"] * damage_factor) and
                            self.hps.info[target][4] < round(
                                    result["damage"] * damage_factor)) or "norm_prc" in result["mod"]:
                            if self.hps.info[target][3] > 0 and not "norm_prc" in result["mod"]:
                                self.total_damages.info[target] += round(
                                    result["damage"] * damage_factor - self.hps.info[target][3])
                            elif self.hps.info[target][4] > 0 and not "norm_prc" in result["mod"]:
                                self.total_damages.info[target] += round(result["damage"] * damage_factor -
                                                                         self.hps.info[target][4]) - \
                                                                   self.hps.info[target][4]
                                if self.hps.info[target][2] < self.hps.info[target][0]:
                                    self.hps.info[target][0] = self.hps.info[target][2]
                            else:
                                self.total_damages.info[target] += round(result["damage"] * damage_factor)

                            if not (self.hps.info[target][3] == 0 and self.hps.info[target][4] == 0) \
                                    and "norm_prc" not in result["mod"]:
                                if self.hps.info[target][3] > 0:
                                    self.descriptions.info[caster].append(
                                        f"• {round(result['damage'] * damage_factor - self.hps.info[target][3])} {u.ICON['dmg']} ({self.hps.info[target][3]} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                                elif self.hps.info[target][4] > 0:
                                    self.descriptions.info[caster].append(
                                        f"• {round(result['damage'] * damage_factor - self.hps.info[target][4])} {u.ICON['dmg']} ({self.hps.info[target][4]} {u.ICON['absorb']})» #{target}{self.pps[self.inv_teams[target]]}")
                            else:
                                if "norm_prc" in result["mod"]:
                                    self.descriptions.info[caster].append(
                                        f"• {round(result['damage'] * damage_factor)} {u.ICON['pdmg']}» #{target}{self.pps[self.inv_teams[target]]}")
                                else:
                                    self.descriptions.info[caster].append(
                                        f"• {round(result['damage'] * damage_factor)} {u.ICON['dmg']}» #{target}{self.pps[self.inv_teams[target]]}")

                        else:
                            if self.hps.info[target][3] > 0:
                                blocked = True
                                self.descriptions.info[caster].append(
                                    f"• 0 {u.ICON['dmg']} ({self.hps.info[target][3]} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                            elif self.hps.info[target][4] > 0:
                                self.total_damages.info[target] -= round(result["damage"] * damage_factor)
                                if self.hps.info[target][2] < self.hps.info[target][0]:
                                    self.hps.info[target][0] = self.hps.info[target][2]
                                self.descriptions.info[caster].append(
                                    f"• 0 {u.ICON['dmg']} ({round(result['damage'] * damage_factor)} {u.ICON['absorb']})» #{target}{self.pps[self.inv_teams[target]]}")
                        if "self_damage" in result:
                            self.total_damages.info[caster] += result["self_damage"]
                            self.descriptions.info[caster].append(
                                f" {int(result['self_damage'])} {u.ICON['dmg']}» #{caster}{self.pps[self.inv_teams[caster]]}")
                    self.effects_applier(result, caster, blocked, target)
                else:
                    self.descriptions.info[caster].append(f"• {u.ICON['mi']}{u.ICON['ss']}")

        if "crush" in result:
            extras = False
            for y in range(result["attacks"]):
                if self.hps.info[target][3] > 0 or self.hps.info[target][4] > 0:
                    accuracy_factor += 15

                if random.randint(1, 100) <= round(result["acc"] + accuracy_factor):
                    blocked = False
                    if random.randint(1, 100) <= round(result["crit"] + crit_factor):
                        if self.hps.info[target][3] > 0:
                            self.total_damages.info[target] += round(
                                result["crush"] * crit_multiplier * damage_factor +
                                self.hps.info[target][3] * crit_multiplier)
                        elif self.hps.info[target][4] > 0:
                            self.total_damages.info[target] += round(
                                result["crush"] * crit_multiplier * damage_factor +
                                self.hps.info[target][4] * crit_multiplier)
                        else:
                            self.total_damages.info[target] += round(
                                result["crush"] * crit_multiplier * damage_factor)
                        if self.hps.info[target][3] + self.hps.info[target][4] == 0:
                            if self.hps.info[target][3] > 0:
                                self.descriptions.info[caster].append(
                                    f"• {round(result['crush'] * crit_multiplier * damage_factor + self.hps.info[target][3] * crit_multiplier)}{u.ICON['dmg']}{u.ICON['crit']} ({self.hps.info[target][3] * crit_multiplier} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                            elif self.hps.info[target][4] > 0:
                                self.descriptions.info[caster].append(
                                    f"• {round(result['crush'] * crit_multiplier * damage_factor + self.hps.info[target][4] * crit_multiplier)}{u.ICON['dmg']}{u.ICON['crit']} ({self.hps.info[target][4] * crit_multiplier} {u.ICON['absorb']})» #{target}{self.pps[self.inv_teams[target]]}")
                        else:
                            self.descriptions.info[caster].append(
                                f"• {result['crush'] * crit_multiplier * damage_factor}{u.ICON['dmg']}{u.ICON['crit']}» #{target}{self.pps[self.inv_teams[target]]}")
                    else:
                        if self.hps.info[target][3] > 0:
                            self.total_damages.info[target] += round(result["crush"] * damage_factor +
                                                                     self.hps.info[target][3])
                        elif self.hps.info[target][4] > 0:
                            self.total_damages.info[target] += round(result["crush"] * damage_factor +
                                                                     self.hps.info[target][4])
                        else:
                            self.total_damages.info[target] += round(result["crush"] * damage_factor)
                        if self.hps.info[target][3] + self.hps.info[target][4] != 0:
                            if self.hps.info[target][3] > 0:
                                self.descriptions.info[caster].append(
                                    f"• {round(result['crush'] * damage_factor + self.hps.info[target][3])}{u.ICON['dmg']} ({round(self.hps.info[target][3] * crit_multiplier)} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                            elif self.hps.info[target][4] > 0:
                                self.descriptions.info[caster].append(
                                    f"• {round(result['crush'] * damage_factor + self.hps.info[target][4])}{u.ICON['dmg']} ({round(self.hps.info[target][4] * crit_multiplier)} {u.ICON['absorb']})» #{target}{self.pps[self.inv_teams[target]]}")
                        else:
                            self.descriptions.info[caster].append(
                                f"• {round(result['crush'] * damage_factor)}{u.ICON['dmg']}» #{target}{self.pps[self.inv_teams[target]]}")
                    self.effects_applier(result, caster, blocked, target)
                else:
                    self.descriptions.info[caster].append(f"• {u.ICON['mi']}{u.ICON['ss']}")

        if "revenge" in result:
            extras = False
            for y in range(result["attacks"]):
                if random.randint(1, 100) <= round(result["acc"] + accuracy_factor):
                    blocked = False
                    round_hp = self.hps.info[caster][0] - self.total_damages.info[caster] if \
                        self.hps.info[caster][0] > self.total_damages.info[caster] else 0
                    revenge_damage = round(((1 - round_hp / self.hps.info[caster][2]) ** 2) * result["revenge"])
                    if self.hps.info[target][3] < revenge_damage and self.hps.info[target][4] < revenge_damage:
                        if self.hps.info[target][3] > 0:
                            self.total_damages.info[target] += (revenge_damage - self.hps.info[target][3])
                        elif self.hps.info[target][4] > 0:
                            self.total_damages.info[target] += (revenge_damage - self.hps.info[target][4]) \
                                                               - self.hps.info[target][4]
                            if self.hps.info[target][2] < self.hps.info[target][0]:
                                self.hps.info[target][0] = self.hps.info[target][2]
                        else:
                            self.total_damages.info[target] += revenge_damage

                        if not (self.hps.info[target][3] == 0 and self.hps.info[target][4] == 0):
                            if self.hps.info[target][3] > 0:
                                self.descriptions.info[caster].append(
                                    f"• {revenge_damage - self.hps.info[target][3]} {u.ICON['dmg']} ({self.hps.info[target][3]} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                            elif self.hps.info[target][4] > 0:
                                self.descriptions.info[caster].append(
                                    f"• {revenge_damage - self.hps.info[target][4]} {u.ICON['dmg']} ({self.hps.info[target][4]} {u.ICON['absorb']})» #{target}{self.pps[self.inv_teams[target]]}")
                        else:
                            self.descriptions.info[caster].append(
                                f"• {revenge_damage} {u.ICON['dmg']}» #{target}{self.pps[self.inv_teams[target]]}")

                    else:
                        if self.hps.info[target][3] > 0:
                            blocked = True
                            self.descriptions.info[caster].append(
                                f"• 0 {u.ICON['dmg']} ({revenge_damage} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                        elif self.hps.info[target][4] > 0:
                            self.total_damages.info[target] -= revenge_damage
                            if self.hps.info[target][2] < self.hps.info[target][0]:
                                self.hps.info[target][0] = self.hps.info[target][2]
                            self.descriptions.info[caster].append(
                                f"• 0 {u.ICON['dmg']} ({revenge_damage} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                else:
                    self.descriptions.info[caster].append(f"• {u.ICON['mi']}{u.ICON['ss']}")
            # self.new_line(caster)
        if "lich_revenge" in result:
            extras = False
            for y in range(result["attacks"]):
                if random.randint(1, 100) <= round(result["acc"] + accuracy_factor):
                    blocked = False
                    round_hp = self.hps.info[caster][0] - self.total_damages.info[caster] if \
                        self.hps.info[caster][0] > self.total_damages.info[caster] else 0
                    revenge_damage = round((round_hp / self.hps.info[caster][2]) ** 50 * result["lich_revenge"])
                    if self.hps.info[target][3] < revenge_damage and self.hps.info[target][4] < revenge_damage:
                        if self.hps.info[target][3] > 0:
                            self.total_damages.info[target] += (revenge_damage - self.hps.info[target][3])
                        elif self.hps.info[target][4] > 0:
                            self.total_damages.info[target] += (revenge_damage - self.hps.info[target][
                                4]) - self.hps.info[target][4]
                            if self.hps.info[target][2] < self.hps.info[target][0]:
                                self.hps.info[target][0] = self.hps.info[target][2]
                        else:
                            self.total_damages.info[target] += revenge_damage
                        if not (self.hps.info[target][3] == 0 and self.hps.info[target][4] == 0):
                            if self.hps.info[target][3] > 0:
                                self.descriptions.info[caster].append(
                                    f"• {revenge_damage - self.hps.info[target][3]} {u.ICON['dmg']} ({self.hps.info[target][3]} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                            elif self.hps.info[target][4] > 0:
                                self.descriptions.info[caster].append(
                                    f"• {revenge_damage - self.hps.info[target][4]} {u.ICON['dmg']} ({self.hps.info[target][4]} {u.ICON['absorb']})» #{target}{self.pps[self.inv_teams[target]]}")
                        else:
                            self.descriptions.info[caster].append(
                                f"• {revenge_damage} {u.ICON['dmg']}» #{target}{self.pps[self.inv_teams[target]]}")
                        self.effects_applier(result, caster, blocked, target)
                    else:
                        if self.hps.info[target][3] > 0:
                            blocked = True
                            self.descriptions.info[caster].append(
                                f"• 0 {u.ICON['dmg']} ({revenge_damage} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                        elif self.hps.info[target][4] > 0:
                            self.total_damages.info[target] -= revenge_damage
                            if self.hps.info[target][2] < self.hps.info[target][0]:
                                self.hps.info[target][0] = self.hps.info[target][2]
                            self.descriptions.info[caster].append(
                                f"• 0 {u.ICON['dmg']} ({revenge_damage} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                else:
                    self.descriptions.info[caster].append(f"• {u.ICON['mi']}{u.ICON['ss']}")
            # self.new_line(caster)
        if "eff_app" in result:
            extras = False
            for y in range(result["attacks"]):
                if random.randint(1, 100) <= round(result["acc"] + accuracy_factor):
                    n_effects = 0
                    if result["eff_app"][4] == "target":
                        if result["eff_app"][1] in self.effects.info[target]:
                            n_effects = self.effects.info[target][result["eff_app"][1]]
                    else:
                        if result["eff_app"][1] in self.effects.info[caster]:
                            n_effects = self.effects.info[caster][result["eff_app"][1]]
                    n_effects = n_effects if n_effects <= result["eff_app"][6] else result["eff_app"][6]
                    if random.randint(1, 100) <= round(result["crit"]):  # accuracy_factor):
                        if result["eff_app"][3] == "regular" and result["eff_app"][5] == "damage":
                            if self.hps.info[target][3] < result["eff_app"][0] * crit_multiplier * abs(n_effects) \
                                    and self.hps.info[target][4] < result["eff_app"][0] * crit_multiplier * abs(
                                n_effects):
                                if self.hps.info[target][3] > 0:
                                    self.total_damages.info[target] += (
                                            result["eff_app"][0] * crit_multiplier * abs(n_effects) -
                                            self.hps.info[target][3])
                                elif self.hps.info[target][4] > 0:
                                    self.total_damages.info[target] += (result["eff_app"][0] * crit_multiplier *
                                                                        abs(n_effects) - self.hps.info[target][4]) \
                                                                       - self.hps.info[target][4]
                                    if self.hps.info[target][2] < self.hps.info[target][0]:
                                        self.hps.info[target][0] = self.hps.info[target][2]
                                else:
                                    self.total_damages.info[target] += result["eff_app"][
                                                                           0] * crit_multiplier * abs(
                                        n_effects)
                                if not (self.hps.info[target][3] == 0 and self.hps.info[target][4] == 0):
                                    if self.hps.info[target][3] > 0:
                                        self.descriptions.info[caster].append(
                                            f"• {round(result['eff_app'][0] * crit_multiplier * abs(n_effects) - self.hps.info[target][3])} {u.ICON['dmg']}{u.ICON['crit']} ({self.hps.info[target][3]} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                                    elif self.hps.info[target][4] > 0:
                                        self.descriptions.info[caster].append(
                                            f"• {round(result['eff_app'][0] * crit_multiplier * abs(n_effects) - self.hps.info[target][4])} {u.ICON['dmg']}{u.ICON['crit']} ({self.hps.info[target][4]} {u.ICON['absorb']})» #{target}{self.pps[self.inv_teams[target]]}")
                                else:
                                    self.descriptions.info[caster].append(
                                        f"• {round(result['eff_app'][0] * crit_multiplier * abs(n_effects))} {u.ICON['dmg']}{u.ICON['crit']}» #{target}{self.pps[self.inv_teams[target]]}")
                            else:
                                if self.hps.info[target][3] > 0:
                                    self.descriptions.info[caster].append(
                                        f"• 0 {u.ICON['dmg']}{u.ICON['crit']} ({self.hps.info[target][3]} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                                elif self.hps.info[target][4] > 0:
                                    self.total_damages.info[target] -= result["eff_app"][
                                                                           0] * crit_multiplier * abs(
                                        n_effects)
                                    if self.hps.info[target][2] < self.hps.info[target][0]:
                                        self.hps.info[target][0] = self.hps.info[target][2]
                                    self.descriptions.info[caster].append(
                                        f"• 0 {u.ICON['dmg']}{u.ICON['crit']} ({result['eff_app'][0] * crit_multiplier * abs(n_effects)} {u.ICON['absorb']})» #{target}{self.pps[self.inv_teams[target]]}")
                        elif result["eff_app"][3] == "pierce" and result["eff_app"][5] == "damage":
                            self.total_damages.info[target] += result["eff_app"][0] * crit_multiplier * abs(
                                n_effects)
                            self.descriptions.info[caster].append(
                                f"• {round(result['eff_app'][0] * crit_multiplier * abs(n_effects))} {u.ICON['pdmg']}{u.ICON['crit']}» #{target}{self.pps[self.inv_teams[target]]}")
                        elif result['eff_app'][5] == "heal":
                            self.total_damages.info[caster] -= round(
                                result["eff_app"][0] * crit_multiplier * damage_factor * n_effects)
                            self.descriptions.info[caster].append(
                                f"• {round(result['eff_app'][0] * crit_multiplier * damage_factor * n_effects)} {u.ICON['heal']}{u.ICON['crit']}» #{caster}{self.pps[self.inv_teams[caster]]}")
                        if "self_damage" in result:
                            self.total_damages.info[caster] += result["self_damage"] * crit_multiplier
                            self.descriptions.info[caster].append(
                                f"• {int(result['self_damage'] * crit_multiplier)} {u.ICON['dmg']}{u.ICON['crit']}» #{caster}{self.pps[self.inv_teams[caster]]}")

                    else:
                        if result["eff_app"][3] == "regular" and result["eff_app"][5] == "damage":
                            if self.hps.info[target][3] < result["eff_app"][0] * abs(n_effects) and \
                                    self.hps.info[target][4] < result["eff_app"][0] * abs(n_effects):
                                if self.hps.info[target][3] > 0:
                                    self.hps.info[target][0] = self.hps.info[target][0] - \
                                                               (result["eff_app"][0] * abs(n_effects) -
                                                                self.hps.info[target][3])
                                elif self.hps.info[target][4] > 0:
                                    self.hps.info[target][0] = self.hps.info[target][0] - (
                                            result["eff_app"][0] * abs(n_effects) - self.hps.info[target][4]) \
                                                               + self.hps.info[target][4]
                                    if self.hps.info[target][2] < self.hps.info[target][0]:
                                        self.hps.info[target][0] = self.hps.info[target][2]
                                else:
                                    self.hps.info[target][0] = self.hps.info[target][0] - \
                                                               result["eff_app"][0] * abs(n_effects)
                                    if self.hps.info[target][2] < self.hps.info[target][0]:
                                        self.hps.info[target][0] = self.hps.info[target][2]
                                if not (self.hps.info[target][3] == 0 and self.hps.info[target][4] == 0):
                                    if self.hps.info[target][3] > 0:
                                        self.descriptions.info[caster].append(
                                            f"• {round(result['eff_app'][0] * abs(n_effects) - self.hps.info[target][3])} {u.ICON['dmg']} ({self.hps.info[target][3]} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                                    elif self.hps.info[target][4] > 0:
                                        self.descriptions.info[caster].append(
                                            f"• {round(result['eff_app'][0] * abs(n_effects) - self.hps.info[target][4])} {u.ICON['dmg']} ({self.hps.info[target][4]} {u.ICON['absorb']})» #{target}{self.pps[self.inv_teams[target]]}")
                                else:
                                    self.descriptions.info[caster].append(
                                        f"• {round(result['eff_app'][0] * abs(n_effects))} {u.ICON['dmg']}» #{target}{self.pps[self.inv_teams[target]]}")
                            else:
                                if self.hps.info[target][3] > 0:
                                    self.descriptions.info[caster].append(
                                        f"• 0 {u.ICON['dmg']} ({self.hps.info[target][3]} {u.ICON['block']})» #{target}{self.pps[self.inv_teams[target]]}")
                                elif self.hps.info[target][4] > 0:
                                    self.hps.info[target][0] = self.hps.info[target][0] + \
                                                               result["eff_app"][0] * abs(n_effects)
                                    if self.hps.info[target][2] < self.hps.info[target][0]:
                                        self.hps.info[target][0] = self.hps.info[target][2]
                                    self.descriptions.info[caster].append(
                                        f"• 0 {u.ICON['dmg']} ({result['eff_app'][0] * abs(n_effects)} {u.ICON['absorb']})» #{target}{self.pps[self.inv_teams[target]]}")
                        elif result["eff_app"][3] == "pierce" and result["eff_app"][5] == "damage":
                            self.hps.info[target][0] = self.hps.info[target][0] - result["eff_app"][
                                0] * abs(n_effects)
                            self.descriptions.info[caster].append(
                                f"• Dealt {round(result['eff_app'][0] * abs(n_effects))} {u.ICON['pdmg']}» #{target}{self.pps[self.inv_teams[target]]}")
                        elif result['eff_app'][5] == "heal":
                            self.total_damages.info[caster] -= round(
                                result["eff_app"][0] * damage_factor * n_effects)
                            self.descriptions.info[caster].append(
                                f"• {round(result['eff_app'][0] * damage_factor * n_effects)} {u.ICON['heal']}» #{caster}{self.pps[self.inv_teams[caster]]}")
                        if "self_damage" in result:
                            self.hp1[0] -= result["self_damage"]
                            self.descriptions.info[caster].append(
                                f"• Dealt {int(result['self_damage'])} {u.ICON['dmg']}» #{caster}{self.pps[self.inv_teams[caster]]}")
                    self.effects_applier(result, caster, False, target)

                    if result["eff_app"][2]:
                        if result["eff_app"][4] == "target":
                            if str(result["eff_app"][1]) in self.effects.info[target]:
                                if self.effects.info[target][result["eff_app"][1]] > result["eff_app"][6]:
                                    self.effects.info[target][result["eff_app"][1]] -= result["eff_app"][6]
                                else:
                                    del self.effects.info[target][str(result["eff_app"][1])]
                        else:
                            if str(result["eff_app"][1]) in self.effects.info[caster]:
                                if self.effects.info[caster][result["eff_app"][1]] > result["eff_app"][6]:
                                    self.effects.info[caster][result["eff_app"][1]] -= result["eff_app"][6]
                                else:
                                    del self.effects.info[caster][str(result["eff_app"][1])]
                else:
                    self.descriptions.info[caster].append(f"• {u.ICON['mi']}{u.ICON['ss']}")
            # self.new_line(caster)

        if extras:
            if "self_damage" in result:
                self_dmg = 0
                if "inverse_damage" in result:
                    self_dmg = result["inverse_damage"]
                else:
                    self_dmg = result["self_damage"]
                self.total_damages.info[caster] += self_dmg
                self.descriptions.info[caster].append(
                    f"• {self_dmg} {u.ICON['dmg']}» #{caster}{self.pps[self.inv_teams[caster]]}")
        # self.new_line(caster)

    def execute_card_special(self, c_level: int, c_name: str, caster, target):
        """
        Sets up the unique parts of a card
        :param c_level: The level of the card for number crunching
        :param c_name: The name of the card
        :param caster: The user of the card
        :param target: The entity the card is being used on
        """
        if c_name is None or c_level is None:
            return

        result = cards_dict(c_level, c_name)
        if result["name"] == "Glitched":
            result = items_dict(c_name, self.hps.info[target][2])

        if "spawn" in result:
            if result["spawn"][2] == "target" or result["spawn"][2] == "all":
                added_cards = 0
                for x in range(result["spawn"][1]):
                    if random.randint(1, 100) <= result["spawn"][3][1]:
                        added_cards += 1
                        self.decks.info[target].insert(
                            random.randint(self.hand_sizes.info[target], len(self.decks.info[target])),
                            str(c_level) + "." + result["spawn"][0])
                self.descriptions.info[caster].append(
                    f"• {added_cards} [{rarity_cost(result['spawn'][0])}] {result['spawn'][0]} lv: {c_level}» #{target}{self.pps[self.inv_teams[target]]}")
                if result["spawn"][2] == "all":
                    self.descriptions.info[caster].append("")
            if result["spawn"][2] == "self" or result["spawn"][2] == "all":
                added_cards = 0
                for x in range(result["spawn"][1]):
                    if random.randint(1, 100) <= result["spawn"][3][0]:
                        added_cards += 1
                        self.decks.info[caster].insert(
                            random.randint(self.hand_sizes.info[caster], len(self.decks.info[caster])),
                            str(c_level) + "." + result["spawn"][0])
                self.descriptions.info[caster].append(
                    f"• {added_cards} [{rarity_cost(result['spawn'][0])}] {result['spawn'][0]} lv: {c_level}» #{caster}{self.pps[self.inv_teams[caster]]}")
        # self.new_line(caster)
        if "clear_eff" in result:
            eff_clear_msg = []
            if result["clear_eff"][1] == "target" or result["clear_eff"][1] == "all":
                for x in result["clear_eff"][0]:
                    if x.lower() in self.effects.info[target]:
                        eff_clear_msg.append(str(self.effects.info[target][x]) + " " + self.eff_to_icon(x))
                        del self.effects.info[target][x]
                if "all" in result["clear_eff"][0]:
                    self.effects.info[target] = {}
                    eff_clear_msg = ["every"]
                if not eff_clear_msg:
                    eff_clear_msg.append("none")
                else:
                    self.descriptions.info[caster].append("Cleared " + ", ".join(
                        eff_clear_msg[:]) + f" effects» #{target}{self.pps[self.inv_teams[target]]}")
            if result["clear_eff"][1] == "self" or result["clear_eff"][1] == "all":
                for x in result["clear_eff"][0]:
                    if x.lower() in self.effects.info[caster]:
                        eff_clear_msg.append(str(self.effects.info[caster][x]) + " " + self.eff_to_icon(x))
                        del self.effects.info[caster][x]
                if "all" in result["clear_eff"][0]:
                    self.effects.info[caster] = {}
                    eff_clear_msg = ["every"]
                if not eff_clear_msg:
                    eff_clear_msg.append("none")
                else:
                    self.descriptions.info[caster].append("Cleared " + ", ".join(
                        eff_clear_msg[:]) + f" effects» #{caster}{self.pps[self.inv_teams[caster]]}")
        # self.new_line(caster)
        if "set_max_hp" in result:
            self.descriptions.info[caster].append(
                f"Max health {self.hps.info[caster][2]} » {self.hps.info[caster][2] * result['set_max_hp'] / 100}")
            self.hps.info[caster][2] = round(self.hps.info[caster][2] * result["set_max_hp"] / 100)
            self.hps.info[caster][0] = self.hps.info[caster][2] if self.hps.info[caster][0] > self.hps.info[caster][2] else \
                self.hps.info[caster][0]
        # self.new_line(caster)
        if "draw" in result:
            cards_drawn = result['draw']
            if self.hand_sizes.info[caster] + cards_drawn >= 6:
                cards_drawn = 6 - self.hand_sizes.info[caster]
            if cards_drawn < 0:
                cards_drawn = 0
            self.hand_sizes.info[caster] += cards_drawn
            self.descriptions.info[caster].append(f"Drawn {cards_drawn} cards")
        # self.new_line(caster)
        if "dmg_boost" in result:
            self.multipliers.info[caster][0] += result["dmg_boost"]
            self.descriptions.info[caster].append(f"•{u.ICON['efb']}» {int(round(result['dmg_boost'] * 100))}% {u.ICON['dmg']}")
        if "def_boost" in result:
            self.multipliers.info[caster][1] += result["def_boost"]
            self.descriptions.info[caster].append(f"•{u.ICON['efb']}» {int(round(result['def_boost'] * 100))}% {u.ICON['block']}")
        if "acc_boost" in result:
            self.multipliers.info[caster][2] += result["acc_boost"]
            self.descriptions.info[caster].append(f"•{u.ICON['efb']}» {int(round(result['acc_boost']))}% {u.ICON['eye']}")
        if "crit_boost" in result:
            self.multipliers.info[caster][3] += result["crit_boost"]
            self.descriptions.info[caster].append(f"•{u.ICON['efb']}» {int(round(result['crit_boost']))}% {u.ICON['crit']}")

    # self.new_line(caster)

    def show_stats(self) -> discord.Embed:
        """
        Displays everything that happened this turn
        :return: An embed containing a summary of things that happe
        """
        if not self.hps.info[1][3] == 1:
            embed = discord.Embed(title=None, description="**PlayBoard**")
        else:
            embed = discord.Embed(title="Sudden Death!", description="**PlayBoard**")
        for i in range(len(self.hps.info)):
            if self.hps.info[i + 1][0] < 0:
                self.hps.info[i + 1] = 0
        for i in range(len(self.descriptions.info)):
            if not len(self.descriptions.info[i + 1]) > 11:
                embed.add_field(name=f"#{i + 1}{self.pps[self.inv_teams[i + 1]]}{self.players.info[i + 1]}:",
                                value="»" + "\n".join(self.descriptions.info[i + 1][:]), inline=True)
            else:
                for ii in range(0, math.ceil(len(self.descriptions.info[i + 1]) / 11) * 11, 11):
                    if len(self.descriptions.info[i + 1]) > ii + 11:
                        embed.add_field(name=f"#{i + 1}{self.pps[self.inv_teams[i + 1]]}{self.players.info[i + 1]}:",
                                        value="»" + "\n".join(self.descriptions.info[i + 1][ii:ii + 11]), inline=True)
                    else:
                        embed.add_field(name=f"#{i + 1}{self.pps[self.inv_teams[i + 1]]}{self.players.info[i + 1]}:",
                                        value="»" + "\n".join(self.descriptions.info[i + 1][ii:]), inline=True)
        return embed

    def show_hand(self) -> discord.Embed:
        """
        Shows the cards that are in everyone's hand
        :return: An embed containing the cards that are in everyone's hand
        """
        expensive_card = [0, 0]
        for i in range(len(self.hand_sizes.info)):
            if self.hand_sizes.info[i + 1] > 6:
                self.hand_sizes.info[i + 1] = 6

        def display_hand(index):
            current_hand = []
            if self.hps.info[index][0] > 0 and self.staminas.info[index] > 0:
                for x in range(self.hand_sizes.info[index]):
                    y = self.decks.info[index][x].split(".")
                    if cards_dict(int(y[0]), y[1])["cost"] > self.stored_energies.info[index]:
                        expensive_card[0] += 1
                    current_hand.insert(len(current_hand),
                                        str(x + 1) + ". **[" + rarity_cost(y[1]) + "] " +
                                        str(y[1]) + "** lv: " + str(y[0]) + " \n")
                y = self.decks.info[index][self.hand_sizes.info[index]].split(".")
                current_hand.insert(len(current_hand),
                                    "Next: [" + rarity_cost(y[1]) + "] " + str(y[1]) + " lv: " + str(y[0]) + "\n")
                if self.hand_sizes.info[index] == 6:
                    current_hand.insert(len(current_hand), "Reached Max Hand")
            else:
                current_hand = ["**[Dead]**\n"]
            return current_hand

        # <:upward_arrow:529486588590424077>
        if not self.turns % 4 == 0:
            embed = discord.Embed(title=None,
                                  description=f"• Type `{u.PREF}(card number1)(target number1)` to use card(s)")
        else:
            embed = discord.Embed(title=None,
                                  description=f"• Type `{u.PREF}(card number1)(target number1)` to use card(s)\n***+{math.ceil(self.turns / 4)}   {u.ICON['engy']} gain per turn!***")
        for i in range(len(self.players.info)):
            embed.add_field(
                name=f"__**#{i + 1}**__{self.pps[self.inv_teams[i + 1]]}{self.players.info[i + 1]}'s hand:",
                value=f"**{u.ICON['hp']} {self.hps.info[i + 1][0]}/{self.hps.info[i + 1][2]}** \n**{u.ICON['sta']} {self.staminas.info[i + 1]} {u.ICON['engy']} {self.stored_energies.info[i + 1]}**\n" + \
                      "".join(display_hand(i + 1)))
        embed.set_footer(text=f"Turn {self.turns} - (+{math.ceil(self.turns / 4)} energy/turn)")
        # if expensive_card[0] < self.hand_size[0] and expensive_card[1] < self.hand_size[1] and not "freeze" in self.effect1 and not "freeze" in self.effect2:
        # embed.set_footer(text=f"{self.players.infos[1]} go first")
        # self.afk = 0
        return embed

    def interpret_message(self, msg, reply_author, user):
        """
        Interprets user input into something the bot can understand
        """
        msg = msg.split(" ")

        try:
            for i in msg:
                if items_dict(" ".join(i[:-1].lower().split("_")[:]))["name"].lower() in self.backpacks.info[user]:
                    if items_dict(" ".join(i[:-1].lower().split("_")[:]))["in_battle"]:
                        self.item_used.info[user] = [
                            items_dict(" ".join(i[:-1].lower().split("_")[:]))["name"].lower(), int(i[-1])]
                        msg.remove(i)
                        break
            move_numbers = reduce(lambda r, x: r + [x] if math.floor(x / 10) not in [math.floor(i / 10) for i in r] else r,
                                  [math.floor(abs(int(x)) + 1 - 1) for x in msg], [])
        except:
            self.item_used.info[user] = ["None", user]
            action = msg[0].lower()
            if action in ["skip", "skipped", "skipping", "sk", "s"]:
                return "skip"
            elif action in ["fleeing", "flee", "fle", "fl", "f"]:
                return "flee"
            elif action in ["refresh", "fresh", "refre", "re", "r"]:
                return "refresh"
            elif action in ["backpack", "backpacks", "backp", "back", "bp", "b", "bac", "ba", "pack", "pac", "pa"]:
                return "backpack"
            else:
                self.item_used.info[user] = ["None", user]
                return f"{reply_author}, what you put is invalid!"

        def valid_play(numbers):
            return all([0 < int(str(x)[0]) <= self.hand_sizes.info[user] and
                        len(str(x)) == 2 and 1 <= int(str(x)[1]) <= len(self.hand_sizes.info) for x in
                        numbers])

        if not valid_play(move_numbers):
            return (f"{reply_author} that's an invalid play! "
                    f"Type your play in the format `{u.PREF}card#target#`, "
                    f"eg. `{u.PREF}23` where 2 is your card number and 3 is your target number.")

        elif len(move_numbers) > 4:
            return f"{reply_author}, you can't play more than 4 cards a turn!"
        else:
            selected_card_energy_cost = sum([cards_dict(int(self.decks.info[user][int(str(x)[0]) - 1].split(".")[0]), self.decks.info[user][int(str(x)[0]) - 1].split(".")[1])["cost"] for x in move_numbers])
            soul_self = sum([1 if self.decks.info[user][int(str(x)[0]) - 1].split(".")[1].lower() == "soul drain" and int(str(x)[1]) in self.teams[self.inv_teams[user]] else 0 for x in move_numbers])

            if soul_self:
                return f"{reply_author}, you can't soul drain yourself!"
            if self.stored_energies.info[user] < selected_card_energy_cost:
                return f"{reply_author}, you don't have enough energy to use the selected card(s)!"
            else:
                if self.item_used.info[user][0] != "None" and items_dict(self.item_used.info[user][0])["one_use"]:
                    def backpack_clear():
                        inv_delete = []
                        for x in self.backpacks.info[user]:
                            if self.backpacks.info[user][x] == 0:
                                inv_delete.append(x)
                        for x in inv_delete:
                            del self.backpacks.info[user][x]

                    self.backpacks.info[user][self.item_used.info[user][0]] -= 1
                    backpack_clear()
                return move_numbers
