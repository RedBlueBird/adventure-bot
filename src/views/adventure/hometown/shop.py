import typing as t

import discord
import discord.ui as ui

from helpers import util as u, resources as r
from db import db_manager as dm
from views.adventure.template import Exit, InteractionCheckMixin


class BuyForm(ui.Modal, title="Buy something!"):
    item = ui.TextInput(label="Item", placeholder="What do you want to buy?")
    amt = ui.TextInput(label="Amount", placeholder="How much do you want to buy?")

    def __init__(self, user: discord.Member, offers: t.Collection[str]):
        super().__init__()
        self.user = user
        self.offers = {o.lower() for o in offers}

    async def on_submit(self, i: discord.Interaction):
        amt = self.amt.value
        if not amt.isdigit() or int(amt) <= 0:
            await i.response.send_message("That's an invalid amount to buy!", ephemeral=True)
            return
        amt = int(amt)

        item = r.item(self.item.value.lower())
        name = item.name.lower()
        if name not in self.offers:
            await i.response.send_message("Sorry, I don't have that item!", ephemeral=True)
            return

        inv = dm.get_user_inventory(self.user.id)
        if item.weight * amt > r.BP_CAP - u.bp_weight(inv):
            await i.response.send_message(
                "You don't have enough space in your backpack for these items!",
                ephemeral=True,
            )
            return

        coins = dm.get_user_coin(self.user.id)
        if item.buy * amt > coins:
            await i.response.send_message("You can't afford that much stuff!", ephemeral=True)
            return

        coins -= item.buy * amt
        if name in inv:
            inv[name] += amt
        else:
            inv[name] = {"items": amt}

        dm.set_user_inventory(self.user.id, inv)
        dm.set_user_coin(self.user.id, coins)

        await i.response.send_message(
            "You just bought "
            f"**[{item.rarity}/{item.weight}] {name.title()} x{amt}** "
            f"for {item.buy * amt} {r.ICONS['coin']}!",
            ephemeral=True,
        )


class Shop(ui.View, InteractionCheckMixin):
    def __init__(self, user: discord.Member, offers: t.Collection[str]):
        super().__init__()
        self.user = user
        self.add_item(Exit())
        self.items = offers

    @ui.button(label="Purchase", style=discord.ButtonStyle.blurple)
    async def purchase(self, i: discord.Interaction, button: ui.Button):
        await i.response.send_modal(BuyForm(self.user, self.items))

    @ui.button(label="Backpack", style=discord.ButtonStyle.blurple)
    async def backpack(self, i: discord.Interaction, button: ui.Button):
        inv = dm.get_user_inventory(self.user.id)
        await i.response.send_message(embed=u.container_embed(inv, "Backpack"), ephemeral=True)
