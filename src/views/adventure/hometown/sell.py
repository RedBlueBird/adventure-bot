import discord
import discord.ui as ui

import db
from helpers import util as u, resources as r
from views.adventure.template import Exit, InteractionCheckMixin


class SellForm(ui.Modal, title="Sell something!"):
    item = ui.TextInput(label="Item", placeholder="What do you want to sell?")
    amt = ui.TextInput(label="Amount", placeholder="How much do you want to sell?")

    async def on_submit(self, i: discord.Interaction):
        amt = self.amt.value
        if not amt.isdigit() or int(amt) <= 0:
            await i.response.send_message("That's an invalid amount to sell!", ephemeral=True)
            return
        amt = int(amt)

        item = r.item(self.item.value.lower())
        name = item.id
        player = db.Player.get_by_id(i.user.id)
        inv = player.inventory
        if inv.get(name, 0) < amt:
            await i.response.send_message(
                "You don't have enough of those items in your backpack!", ephemeral=True
            )
            return

        player.coins += item.sell * amt
        inv[name] -= amt
        if inv[name] == 0:
            del inv[name]
        player.save()

        descr = f"[{item.rarity}/{item.weight}]"
        await i.response.send_message(
            f"You just sold **{descr} {name.title()} x{amt}** "
            f"for {item.sell * amt} {r.ICONS['coin']}!",
            ephemeral=True,
        )


class Sell(ui.View, InteractionCheckMixin):
    def __init__(self, user: discord.Member):
        super().__init__()
        self.user = user
        self.add_item(Exit())

    @ui.button(label="Sell", style=discord.ButtonStyle.blurple)
    async def sell(self, i: discord.Interaction, button: ui.Button):
        modal = SellForm()
        await i.response.send_modal(modal)
        await modal.wait()

        inv = db.Player.get_by_id(i.user.id).inventory
        await i.message.edit(embed=u.container_embed(inv))
