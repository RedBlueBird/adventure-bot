import random
from enum import Enum

import discord
import discord.ui as ui

import db
from ..template import InteractionCheckMixin, Exit


class Bet(Enum):
    HEADS = 0
    TAILS = 1
    EDGE = 2

    @classmethod
    def flip(cls, edge_factor: int = 1000):
        start = edge_factor % 2
        flip = random.randint(start, edge_factor)
        if flip == edge_factor:
            return cls.EDGE
        return Bet(flip % 2)

    def __str__(self):
        match self:
            case self.HEADS:
                return "heads"
            case self.TAILS:
                return "tails"
            case self.EDGE:
                return "its edge"


async def bet(
    i: discord.Interaction,
    user: discord.Member,
    outcome: Bet,
    bet_amt: int,
    edge_factor: int = 1000,
):
    player = db.Player.get_by_id(user.id)
    if player.coins < bet_amt:
        await i.response.send_message("You don't have enough coins to place a bet!", ephemeral=True)

    flip = Bet.flip(edge_factor)
    if flip == outcome:
        inc = bet_amt
        if outcome == Bet.EDGE:
            inc *= edge_factor

        descr = f"The coin landed on {flip} and you got {inc} coins!"
        if outcome == Bet.EDGE:
            descr = descr.upper()

        embed = discord.Embed(title="You won!", description=descr, color=discord.Color.green())
    else:
        inc = -bet_amt
        embed = discord.Embed(
            title="You lost...",
            description=f"The coin landed on {flip} and you lost {bet_amt} coins...",
            color=discord.Color.red(),
        )

    embeds = i.message.embeds
    if len(embeds) < 2:
        embeds.append(embed)
    else:
        embeds[1] = embed

    await i.response.edit_message(embeds=embeds)
    player.coins += inc
    player.save()


class CoinFlip(ui.View, InteractionCheckMixin):
    def __init__(self, user: discord.Member, bet_amt: int = 50, edge_factor: int = 1000):
        super().__init__()
        self.user = user
        self.bet_amt = bet_amt
        self.edge_factor = edge_factor
        self.add_item(Exit())

    @ui.button(label="Bet heads", style=discord.ButtonStyle.blurple)
    async def heads(self, i: discord.Interaction, button: discord.Button):
        await bet(i, self.user, Bet.HEADS, self.bet_amt, self.edge_factor)

    @ui.button(label="Bet tails", style=discord.ButtonStyle.blurple)
    async def tails(self, i: discord.Interaction, button: discord.Button):
        await bet(i, self.user, Bet.TAILS, self.bet_amt, self.edge_factor)

    @ui.button(label="Bet on the edge", style=discord.ButtonStyle.blurple)
    async def edge(self, i: discord.Interaction, button: discord.Button):
        await bet(i, self.user, Bet.EDGE, self.bet_amt, self.edge_factor)
