import random
import math

import discord

from helpers import db_manager as dm, resources as r
from .player import Player


class BattleData2:
    """Contains the battling functions that are the CORE of this bot."""

    def __init__(self, players: list[Player]):
        """Sets up the initial battlefield."""
        self.players = players
        self.round = 1
        self.turn = 1
        self.game_end = False

        self.team_orders = list(range(1, 7))
        random.shuffle(self.team_orders)

        icons = [r.ICON[i] for i in ["ppr", "ppp", "ppw", "ppb", "ppo", "ppg"]]
        pps = dict(zip(self.team_orders, icons))
        for player in players:
            player.icon = pps[player.id]

    def set_up(self) -> discord.Embed:
        for player in self.players:
            dm.set_user_battle_command(player.user.id, "")

        embed = discord.Embed(title="Loading...", description=r.ICON["load"])
        return embed

    def player_selector(self, uid: int) -> Player:
        player = Player()
        for p in self.players:
            if p.user.id == uid:
                player = p
                break
        return player

    def show_stats(self) -> discord.Embed:
        p = self.players[self.turn - 1]
        p.skip = False
        p.stored_energy = min(12, p.stored_energy + math.ceil(self.round / 1))

        turn_msg = ""
        if self.turn > len(self.players):
            turn_msg = "Everyone is dead!"
        else:
            turn_msg = f"• {self.players[self.turn - 1].user.name}'s turn"
        embed = discord.Embed(title=None, description=turn_msg)

        for player in self.players:
            player_dialogue = "\n".join(player.dialogue[:])
            embed.add_field(
                name=f"__**#{player.id}**__{player.icon}{player.user.name}:",
                value=f"**{r.ICON['hp']} {player.hp}/{player.max_hp}**\n"
                      f"**{r.ICON['sta']} {player.stamina} "
                      f"{r.ICON['engy']} {player.stored_energy}**\n"
                      f"{player_dialogue}"
            )
        embed.set_footer(text=f"Round {self.round} (+{min(math.ceil(self.round / 1), 12)} energy/round)")

        return embed

    def show_deck(self, uid: int) -> discord.Embed:
        player = self.player_selector(uid)
        if player == Player():
            return discord.Embed(description="Only the alive users battling can interact with this message!")

        hand = [
            f"{v + 1}. {i.display_name}" for v, i in
            enumerate(player.deck[:player.hand_size])
        ]
        hand.append(f"Next: {player.deck[player.hand_size].display_name}")

        embed = discord.Embed(description=f"• `{r.PREF}move (card number1)(target number1)` to use card(s)")
        embed.add_field(
            name=f"{player.user.name}'s deck",
            value="\n".join(hand)
        )
        if player.hand_size < 6:
            embed.set_footer(text=f"{player.hand_size}/6 cards in hand")
        else:
            embed.set_footer(text="Reached Max Hand")

        return embed

    def show_finish(self, uid: int) -> str | None:
        p = self.player_selector(uid)
        if p.id != self.turn:
            return f"{p.user.mention} It is currently {self.players[self.turn - 1].user.name}'s turn!"

        p.dialogue = []
        error_msg = ""
        moves = dm.get_user_battle_command(p.user.id).split(" ")
        dm.set_user_battle_command(p.user.id, "")
        energy_cost = 0

        #region processing non-card move responses
        if moves == [""]:
            moves = []
            p.skip = True
            p.dialogue = [f"{r.ICON['ski']}{r.ICON['kip']}"]
        for move in moves:
            if move == "flee":
                p.flee = True
                p.dialogue = [f"{r.ICON['fle']}{r.ICON['lee']}"]
                break
            if len(move) != 2:
                error_msg = "Make sure your input is correct!"
                break
            if not (1 <= int(move[0]) <= p.hand_size):
                error_msg = "Make sure the card you chose is in your hand!"
                break
            if not (1 <= int(move[1]) <= len(self.players)):
                error_msg = "Make sure the target you choose is valid!"
                break

            energy_cost += p.deck[int(move[0])].get_energy_cost()

        if error_msg != "":
            error_msg += f" e.g. `{r.PREF}move 12` to play the 1st card in your hand on player #2."
        elif energy_cost > p.stored_energy:
            error_msg = f"You don't have enough energy ({energy_cost} energy) to use those cards!"

        if error_msg != "":
            return f"{p.user.mention} {error_msg}"
        #endregion

        #region updating player status
        for effect in p.effects:
            if p.effects[effect] <= 0:
                continue
            p.dialogue.append(f"• {p.effects[effect]}{r.I_CONVERT[effect]}")
        if "stun" in p.effects and p.effects["stun"] > 0:
            p.crit -= 50
        if "burn" in p.effects and p.effects["burn"] > 0:
            p.hp = max(0, round(p.hp - p.max_hp * 0.04))
        if "recover" in p.effects and p.effects["recover"] > 0:
            p.hp = min(p.max_hp, round(p.max_hp * 0.04))
        if "poison" in p.effects and p.effects["poison"] > 0:
            p.stamina = max(0, p.stamina - 1)
            
        for move in moves:
            if move == "flee":
                break
            target = self.players[int(move[1]) - 1]
            selection = int(move[0]) - 1
            p.deck[selection].write(target=target)
            if not "stay" in p.deck[selection].card:
                if p.deck[selection].card["rarity"] != "NA":
                    p.deck.append(p.deck[selection])
        p.hand_size -= len(moves)
        moves.sort()
        for i in range(len(moves)-1, -1, -1):
            if move == "flee":
                break
            p.deck.pop(int(moves[i][0])-1)
        p.hand_size = min(6, p.hand_size + 1)

        for priority in range(3,0,-1):
            for use_card in p.inbox[priority]:
                use_card(target=p)

        if p.hp <= 0:
            p.hp = 0
            p.dead = True
            p.dialogue = [r.ICON['dead']]
        for effect in p.effects:
            if effect != "curse" and p.effects[effect] > 0:
                p.effects[effect] -= 1
            elif p.effects[effect] < 0:
                p.effects[effect] *= -1
        p.inbox = {1:[],2:[],3:[]}
        p.block = 0
        p.absorb = 0
        p.crit = 0
        #endregion

        #region cleansing dead players from the board
        while self.turn >= len(self.players) or self.players[self.turn].dead or self.players[self.turn].flee:
            if self.turn >= len(self.players):
                if self.game_end:
                    break
                alive_teams = [0, 0, 0, 0, 0, 0]
                for p in self.players:
                    if p.dead or p.flee:
                        continue
                    alive_teams[p.team - 1] = 1
                self.round += 1
                if sum(alive_teams) <= 1:
                    self.game_end = True
                self.turn = -1
            self.turn += 1
        self.turn += 1
        #endregion
        return None
