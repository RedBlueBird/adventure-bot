import discord
import discord.ui as ui

import db
from helpers.util.poker import Value, Deck, Card
from ..template import InteractionCheckMixin, Exit

BJ = 21
BET = 50


def bj_val(cards: list[Card]) -> int:
    total = 0
    ace_num = 0
    for c in cards:
        total += c.val.bj_value()
        if c.val == Value.A:
            ace_num += 1

    while total > BJ and ace_num > 0:
        ace_num -= 1
        total -= 10

    return total


class BlackjackBoard(ui.View, InteractionCheckMixin):
    def __init__(self, user: discord.Member):
        super().__init__()
        self.user = user
        self.db_user = db.Player.get_by_id(user.id)
        self.deck = Deck()
        self.deck.shuffle()

        self.player = self.deck.draw_n(2)
        self.dealer = self.deck.draw_n(2)
        self.result = None

    def deck_size(self) -> int:
        return len(self.deck)

    def player_vals(self) -> tuple[list[Card], int]:
        return self.player, bj_val(self.player)

    def dealer_vals(self) -> tuple[list[Card], int]:
        return self.dealer, bj_val(self.dealer)

    async def win(self, i: discord.Interaction):
        embed = i.message.embeds[0]
        embed.colour = discord.Colour.green()
        embed.add_field(name="Result", value=f"You won {BET} coins!", inline=False)
        self.db_user.coins += BET
        self.db_user.save()
        await self.send_result(i, embed)

    async def lose(self, i: discord.Interaction):
        embed = i.message.embeds[0]
        embed.colour = discord.Colour.red()
        embed.add_field(name="Result", value=f"You lost {BET} coins...", inline=False)
        self.db_user.coins += BET
        self.db_user.save()
        await self.send_result(i, embed)

    async def draw(self, i: discord.Interaction):
        embed = i.message.embeds[0]
        embed.colour = discord.Colour.orange()
        embed.add_field(name="Result", value="Draw! No one got anything!", inline=False)
        await self.send_result(i, embed)

    async def send_result(self, i: discord.Interaction, embed: discord.Embed):
        delay = 10
        embed.set_footer(text=f"This message will be deleted in {delay} seconds.")
        await i.edit_original_response(embed=embed, view=None)
        await i.message.delete(delay=delay)
        self.stop()

    @ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, i: discord.Interaction, button: ui.Button):
        self.player.append(self.deck.draw())
        val = bj_val(self.player)

        board = i.message.embeds[0]
        board.set_field_at(0, name="Cards Left", value=len(self.deck), inline=False)
        p_new = f"**Value**: {val}\n```{' '.join(str(i) for i in self.player)}```"
        board.set_field_at(1, name="Player", value=p_new)

        await i.response.edit_message(embed=board)

        if val == BJ:
            await self.win(i)
        elif val > BJ:
            await self.lose(i)

    @ui.button(label="Stand", style=discord.ButtonStyle.red)
    async def stand(self, i: discord.Interaction, button: ui.Button):
        p_val = bj_val(self.player)
        if p_val == BJ:
            await self.win(i)
            return

        while bj_val(self.dealer) < 17:
            self.dealer.append(self.deck.draw())

        board = i.message.embeds[0]
        board.set_field_at(0, name="Cards Left", value=len(self.deck), inline=False)

        d_val = bj_val(self.dealer)
        d_new = f"**Value**: {d_val}\n```{' '.join(str(i) for i in self.dealer)}```"
        board.set_field_at(2, name="Dealer", value=d_new)

        await i.response.edit_message(embed=board)

        if d_val == BJ and len(self.dealer) == 2:
            await self.lose(i)
        elif d_val > BJ or BJ - p_val < BJ - d_val:
            await self.win(i)
        elif BJ - p_val == BJ - d_val:
            await self.draw(i)
        else:
            await self.lose(i)

    def board_embed(self) -> discord.Embed:
        board = discord.Embed(title="Blackjack")

        board.add_field(name="Cards Left", value=self.deck_size(), inline=False)

        p_hand, p_val = self.player_vals()
        player = f"**Value**: {p_val}\n```{' '.join(str(i) for i in p_hand)}```"
        board.add_field(name="Your Hand", value=player)

        d_hand, d_val = self.dealer_vals()
        dealer = f"**Value**: ?\n```{d_hand[0]} ?```"
        board.add_field(name="Dealer Hand", value=dealer)
        board.colour = discord.Colour.teal()
        return board


class Blackjack(ui.View, InteractionCheckMixin):
    def __init__(self, user: discord.Member):
        super().__init__()
        self.user = user
        self.add_item(Exit())

    @ui.button(label="Play a round!", style=discord.ButtonStyle.blurple)
    async def play(self, i: discord.Interaction, button: ui.Button):
        if db.Player.get_by_id(self.user.id).coins < BET:
            await i.response.send_message(f"You need at least {BET} to buy bait!", ephemeral=True)
            return

        view = BlackjackBoard(self.user)
        await i.response.send_message(embed=view.board_embed(), view=view)

        button.disabled = True
        await i.message.edit(view=self)

        await view.wait()
        button.disabled = False
        await i.message.edit(view=self)
