import random
import math
from functools import reduce
from typing import List

import discord

import util as u
from util import cards_dict, cards_dict_temp, items_dict, rarity_cost
from helpers import db_manager as dm

class Card:
    def __init__(self, level: int, name: str):
        self.level = level
        self.name = name
        self.display_name = f"[{rarity_cost(name)}] {name} lv: {level}"
        self.card = cards_dict_temp(level, name)
    
    def get_energy_cost(self):
        return self.card["cost"]


class Player:
    def __init__(self, level: int = 1, user: discord.Member = None, team: int = 0, id: int = 0, deck: list[Card] = None):
        self.team = team
        self.id = id
        self.user = user
        self.level = level
        self.hp = u.level_hp(level)
        self.max_hp = u.level_hp(level)
        self.stamina = 30
        self.stored_energy = 3
        self.deck = deck
        self.hand_size = 4
        self.dialogue = ""
        self.dead = False
        self.flee = False 
        self.skip = False

class BattleData2:
    """
    Contains the battling functions that are at the CORE of this bot.
    """

    def __init__(self, players: list[Player]):
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

        self.players = players
        self.round = 1
        self.turn = 1
        self.game_end = False

        self.team_orders = list(range(1, 7))
        random.shuffle(self.team_orders)
        self.pps = dict(zip(self.team_orders, [u.ICON['ppr'], u.ICON['ppp'], u.ICON['ppw'], u.ICON['ppb'], u.ICON['ppo'], u.ICON['ppg']]))

    def set_up(self) -> discord.Embed:
        embed = discord.Embed(title="Loading...", description=u.ICON['load'])
        return embed

    def player_selector(self, uid: int) -> Player:
        player = Player()
        for p in self.players:
            if p.user.id == uid:
                player = p
                break
        return player

    def show_stats(self) -> discord.Embed:
        embed = discord.Embed(title=None,
                              description=f"• {self.players[self.turn-1].user.name}'s turn")
        
        for player in self.players:
            embed.add_field(
                name=f"__**#{player.id}**__{self.pps[player.team]}{player.user.name}:",
                value=f"**{u.ICON['hp']} {player.hp}/{player.max_hp}** \n" + \
                      f"**{u.ICON['sta']} {player.stamina} " + \
                      f"{u.ICON['engy']} {player.stored_energy}** \n" + \
                      f"{player.dialogue}"
                )
        embed.set_footer(text=f"Round {self.round} (+{min(math.ceil(self.round / 1),12)} energy/round)")

        return embed

    def show_deck(self, uid: int) -> discord.Embed:
        player = self.player_selector(uid)
        if player == Player():
            return discord.Embed(title=None, description="Only the alive users battling can interact with this message!")

        embed = discord.Embed(title=None,
                              description=f"• `{u.PREF}move (card number1)(target number1)` to use card(s)")
        embed.add_field(
            name=f"{player.user.name}'s deck",
            value="\n".join([f"{i[0]}. **{i[1].display_name}**" for i in list(zip(range(1,player.hand_size+1),player.deck[:player.hand_size]))] + [f"Next: {player.deck[player.hand_size].display_name}"])
            )
        if player.hand_size < 6:
            embed.set_footer(text=f"Currently {player.hand_size}/6 cards in hand")
        else:
            embed.set_footer(text="Reached Max Hand")

        return embed

    def show_finish(self, uid: int) -> str:
        player = self.player_selector(uid)
        if player.id != self.turn:
            return f"{player.user.mention} It is currently {self.players[self.turn-1].user.name}'s turn right now!"

        player.dialogue = ""
        error_msg = ""
        moves = dm.get_user_battle_command(player.user.id).split(" ")
        dm.set_user_battle_command(player.user.id, "")
        energy_cost = 0
        if moves == [""]:
            moves = []
            player.skip = True
            player.dialogue = f"{u.ICON['ski']}{u.ICON['kip']}"
        for move in moves:
            if move == "flee":
                player.flee = True
                player.dialogue = f"{u.ICON['fle']}{u.ICON['lee']}"
                break
            if len(move) != 2:
                error_msg = "Make sure your input is correct!"
                break
            if not (1 <= int(move[0]) <= player.hand_size):
                error_msg = "Make sure the card you chose is in your hand!"
                break
            if not (1 <= int(move[1]) <= len (self.players)):
                error_msg = "Make sure the target you choose is valid!"
                break
            energy_cost += player.deck[move[0]].get_energy_cost()
        
        if error_msg != "":
            error_msg += f" E.g. `{u.PREF}move 12` to play the 1st card in your hand on player #2."
        elif energy_cost > player.stored_energy:
            error_msg = f"Make sure to have enough energy to use the cards! The selected cards cost {energy_cost} energy."
        
        if error_msg != "":
            return f"{player.user.mention} {error_msg}"
        else:
            while self.turn >= len(self.players) or self.players[self.turn].dead or self.players[self.turn].flee:
                if self.turn >= len(self.players):
                    alive_teams = [0,0,0,0,0,0]
                    for player in self.players:
                        if player.dead or player.flee:
                            continue
                        player.stored_energy = min(12, player.stored_energy + math.ceil(self.round / 1))
                        player.hand_size = min(6, player.hand_size - len(moves) + 1)
                        player.skip = False
                        alive_teams[player.team-1] = 1
                    self.round += 1
                    if sum(alive_teams) <= 1:
                        self.game_end = True
                    self.turn = -1
                self.turn += 1
            self.turn += 1
            return None