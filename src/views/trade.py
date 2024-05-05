import discord
import discord.ui as ui
from discord import Interaction

import db
import resources as r


class CoinModal(ui.Modal, title="Offer some coins!"):
    coins = ui.TextInput(label="Coins", placeholder="How many coins do you want to offer?")
    coin_amt = None

    async def on_submit(self, i: discord.Interaction):
        coins = self.coins.value
        if not coins.isdigit() or int(coins) <= 0:
            await i.response.send_message("That's an invalid amount to offer!", ephemeral=True)
            return

        coins = int(coins)
        if coins > db.Player.get_by_id(i.user.id).coins:
            await i.response.send_message("You don't have that many coins!", ephemeral=True)
            return
        self.coin_amt = coins
        await i.response.defer()


class CardModal(ui.Modal, title="Offer a card!"):
    card = ui.TextInput(label="Card", placeholder="What card ID do you want to give?")
    db_card = None

    async def on_submit(self, i: discord.Interaction) -> None:
        cid = self.card.value
        if not cid.isdigit() or int(cid) <= 0:
            await i.response.send_message("That's an invalid card ID!", ephemeral=True)
            return

        cid = int(cid)
        card = db.Card.get_or_none((db.Card.id == cid) & (db.Card.owner == i.user.id))
        if card is None:
            await i.response.send_message("You don't have that card!", ephemeral=True)
            return
        self.db_card = card
        await i.response.defer()


class UserTrade(ui.View):
    def __init__(self, user1: discord.Member, user2: discord.Member):
        super().__init__()
        self.user1 = user1
        self.user1_acc = False
        self.user1_coins = 0
        self.user1_cards: list[db.Card] = []

        self.user2 = user2
        self.user2_acc = False
        self.user2_coins = 0
        self.user2_cards: list[db.Card] = []

        self.went_through = None

    @ui.button(label="Offer Coins", style=discord.ButtonStyle.blurple)
    async def coins(self, i: discord.Interaction, button: ui.Button):
        modal = CoinModal()
        await i.response.send_modal(modal)
        await modal.wait()
        if modal.coin_amt is None:
            await i.response.defer()

        if i.user.id == self.user1.id:
            self.user1_coins = modal.coin_amt
        elif i.user.id == self.user2.id:
            self.user2_coins = modal.coin_amt

        await i.message.edit(embed=self.trade_embed())

    @ui.button(label="Offer Cards", style=discord.ButtonStyle.blurple)
    async def cards(self, i: discord.Interaction, button: ui.Button):
        modal = CardModal()
        await i.response.send_modal(modal)
        await modal.wait()

        if modal.db_card is None:
            await i.response.defer()

        if i.user.id == self.user1.id:
            if modal.db_card not in self.user1_cards:
                self.user1_cards.append(modal.db_card)
        elif i.user.id == self.user2.id:
            if modal.db_card not in self.user2_cards:
                self.user2_cards.append(modal.db_card)

        await i.message.edit(embed=self.trade_embed())

    @ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, i: discord.Interaction, button: ui.Button):
        if i.user.id == self.user1.id:
            self.user1_acc = True
        elif i.user.id == self.user2.id:
            self.user2_acc = True
        await i.response.edit_message(embed=self.trade_embed())

        if self.user1_acc and self.user2_acc:
            self.went_through = True
            self.stop()

    @ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, i: discord.Interaction, button: ui.Button):
        self.went_through = False
        await i.response.defer()
        self.stop()

    def trade_embed(self):
        user1_cards = [f"{r.card(c.name)} lv: {c.level}" for c in self.user1_cards]
        user2_cards = [f"{r.card(c.name)} lv: {c.level}" for c in self.user2_cards]
        card_msg1 = "\n".join(user1_cards) if user1_cards else "No cards."
        card_msg2 = "\n".join(user2_cards) if user2_cards else "No cards."

        user1_offer = f"**Coins:** {self.user1_coins}\n**Cards:**\n{card_msg1}"
        user2_offer = f"**Coins:** {self.user2_coins}\n**Cards:**\n{card_msg2}"

        embed = (
            discord.Embed(
                title=f"Trade between {self.user1.display_name} and {self.user2.display_name}",
                color=discord.Color.gold(),
            )
            .add_field(
                name=self.user1.display_name + (" ✅" if self.user1_acc else ""),
                value=user1_offer,
            )
            .add_field(
                name=self.user2.display_name + (" ✅" if self.user2_acc else ""),
                value=user2_offer,
            )
            .set_footer(text="Both users must accept the offer for the trade to go through.")
        )
        return embed

    async def interaction_check(self, i: Interaction):
        if i.user.id not in [self.user1.id, self.user2.id]:
            await i.response.send_message("You aren't the one trading here!", ephemeral=True)
            return False
        return True
