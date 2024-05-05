import typing as t

import discord
import discord.ui as ui

import db
from helpers import util as u
import resources as r
from views.adventure.template import Exit, Backpack, InteractionCheckMixin


class BuyForm(ui.Modal, title="Buy something!"):
    item = ui.TextInput(label="Item", placeholder="What do you want to buy?")
    amt = ui.TextInput(label="Amount", placeholder="How much do you want to buy?")

    def __init__(self, offers: t.Collection[str]):
        super().__init__()
        self.offers = {o.lower() for o in offers}

    async def on_submit(self, i: discord.Interaction):
        amt = self.amt.value
        if not amt.isdigit() or int(amt) <= 0:
            await i.response.send_message("That's an invalid amount to buy!", ephemeral=True)
            return
        amt = int(amt)

        item = r.item(self.item.value.lower())
        name = item.name.lower() if item is not None else None
        if name not in self.offers:
            await i.response.send_message("Sorry, I don't have that item!", ephemeral=True)
            return

        player = db.Player.get_by_id(i.user.id)
        inv = player.inventory
        if item.weight * amt > r.BP_CAP - u.bp_weight(inv):
            await i.response.send_message(
                "You don't have enough space in your backpack for these items!",
                ephemeral=True,
            )
            return

        if item.buy * amt > player.coins:
            await i.response.send_message("You can't afford that much stuff!", ephemeral=True)
            return

        player.coins -= item.buy * amt
        if name not in inv:
            inv[name] = 0
        inv[name] += amt

        player.save()
        await i.response.send_message(
            "You just bought "
            f"**[{item.rarity}/{item.weight}] {name.title()} x{amt}** "
            f"for {item.buy * amt} {r.ICONS['coin']}!",
            ephemeral=True,
        )


class Shop(InteractionCheckMixin, ui.View):
    def __init__(self, user: discord.Member, offers: t.Collection[str]):
        super().__init__(user)
        self.db_user = db.Player.get_by_id(user.id)
        self.add_item(Backpack())
        self.add_item(Exit())
        self.items = offers

    @ui.button(label="Purchase", style=discord.ButtonStyle.blurple)
    async def purchase(self, i: discord.Interaction, button: ui.Button):
        await i.response.send_modal(BuyForm(self.items))
