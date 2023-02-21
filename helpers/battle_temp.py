import random
import math
from functools import reduce
from typing import List

import discord

import util as u
from util import cards_dict, items_dict, rarity_cost

class Card:
    def __init__(self, level: int):
        self.level = level

class Player:
    def __init__(self, level: int, user: discord.Member, team: int, id: int, deck: list[Card]):
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

        team_orders = list(range(1, 7))
        random.shuffle(team_orders)
        self.pps = dict(zip(team_orders, [u.ICON['ppr'], u.ICON['ppp'], u.ICON['ppw'], u.ICON['ppb'], u.ICON['ppo'], u.ICON['ppg']]))

    def set_up(self) -> discord.Embed:
        embed = discord.Embed(title="Loading...", description=u.ICON['load'])
        return embed

    def show_hand(self) -> discord.Embed:
        embed = discord.Embed(title=None,
                              description=f"• Type `{u.PREF}(card number1)(target number1)` to use card(s)\n" + \
                                          f"• {self.players[self.turn-1].user.name}'s turn")
        
        for player in self.players:
            embed.add_field(
                name=f"__**#{player.id}**__{self.pps[player.team]}{player.user.name}:",
                value=f"**{u.ICON['hp']} {player.hp}/{player.max_hp}** \n" + \
                      f"**{u.ICON['sta']} {player.stamina} " + \
                      f"{u.ICON['engy']} {player.stamina}** \n" + \
                      f"{player.dialogue}"
                )
        embed.set_footer(text=f"Round {self.round} (+{math.ceil(self.round / 4)} energy/round)")

        return embed