import typing as t
import discord
from util.poker import Value, Deck, Card

BJ: t.Final = 21


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


class Blackjack(discord.ui.View):
    def __init__(self):
        super().__init__()

        self.deck = Deck()
        self.deck.shuffle()

        self.player = self.deck.draw_n(2)
        self.dealer = self.deck.draw_n(2)

    def deck_size(self) -> int:
        return len(self.deck)

    def player_vals(self) -> tuple[list[Card], int]:
        return self.player, bj_val(self.player)

    def dealer_vals(self) -> tuple[list[Card], int]:
        return self.dealer, bj_val(self.dealer)

    async def win(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.colour = discord.Colour.green()
        embed.add_field(name="Result", value="You win!", inline=False)
        await interaction.edit_original_response(embed=embed)
        self.stop()

    async def lose(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.colour = discord.Colour.red()
        embed.add_field(name="Result", value="You lose...", inline=False)
        await interaction.edit_original_response(embed=embed)
        self.stop()

    async def draw(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.colour = discord.Colour.orange()
        embed.add_field(name="Result", value="Draw!", inline=False)
        await interaction.edit_original_response(embed=embed)
        self.stop()

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player.append(self.deck.draw())
        val = bj_val(self.player)

        board = interaction.message.embeds[0]
        board.set_field_at(0, name="Cards Left", value=len(self.deck), inline=False)
        p_new = f"**Value**: {val}\n```{' '.join(str(i) for i in self.player)}```"
        board.set_field_at(1, name="Player", value=p_new)

        await interaction.response.defer()
        await interaction.edit_original_response(embed=board)

        if val == BJ:
            await self.win(interaction)
        elif val > BJ:
            await self.lose(interaction)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        while bj_val(self.dealer) < 17:
            self.dealer.append(self.deck.draw())

        board = interaction.message.embeds[0]
        board.set_field_at(0, name="Cards Left", value=len(self.deck), inline=False)

        p_val = bj_val(self.player)
        d_val = bj_val(self.dealer)
        d_new = f"**Value**: {d_val}\n```{' '.join(str(i) for i in self.dealer)}```"
        board.set_field_at(2, name="Dealer", value=d_new)

        await interaction.response.defer()
        await interaction.edit_original_response(embed=board)

        if d_val == BJ and len(self.dealer) == 2:
            await self.lose(interaction)
        elif d_val > BJ or BJ - p_val < BJ - d_val:
            await self.win(interaction)
        elif BJ - p_val == BJ - d_val:
            await self.draw(interaction)
        else:
            await self.lose(interaction)

    @discord.ui.button(label="Help", style=discord.ButtonStyle.blurple)
    async def help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Rules of Blackjack", color=discord.Colour.purple()) \
            .add_field(name="Hit", value="Draw a card and add it to your hand.", inline=False) \
            .add_field(name="Stand", value="Stop drawing cards. The dealer will then reveal their second card "
                                           "and draw until they reach or exceed a value of 17, at which point "
                                           "the player & dealer's hands will be compared.", inline=False) \
            .add_field(name="Win Conditions", value="Whoever's closer to 21 without exceeding it wins.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)