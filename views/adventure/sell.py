import discord
import discord.ui as ui

from helpers import db_manager as dm
import util as u


class SellForm(ui.Modal, title="Sell something!"):
    item = ui.TextInput(label="Item", placeholder="What do you want to sell?")
    amt = ui.TextInput(label="Amount", placeholder="How much do you want to sell?")

    def __init__(self, user: discord.Member, sell_msg: discord.Message):
        super().__init__()
        self.user = user
        self.sell_msg = sell_msg

    async def on_submit(self, i: discord.Interaction):
        amt = self.amt.value
        if not amt.isdigit() or int(amt) <= 0:
            await i.response.send_message(
                "That's an invalid amount to sell!",
                ephemeral=True
            )
            return
        amt = int(amt)

        item = u.items_dict(self.item.value.lower())
        name = item['name'].lower()

        inv = dm.get_user_inventory(self.user.id)

        if inv.get(name, {}).get("items", 0) < amt:
            await i.response.send_message(
                "You don't have enough of those items in your backpack!",
                ephemeral=True
            )
            return

        dm.set_user_coin(
            self.user.id,
            dm.get_user_coin(self.user.id) + item["sell"] * amt
        )
        inv[name]["items"] -= amt
        if inv[name]["items"] == 0:
            del inv[name]

        descr = f"[{item['rarity']}/{item['weight']}]"
        await i.response.send_message(
            f"You just sold **{descr} {name.title()} x{amt}** "
            f"for {item['sell'] * amt} {u.ICON['coin']}!",
            ephemeral=True
        )
        dm.set_user_inventory(self.user.id, inv)
        await self.sell_msg.edit(embed=u.display_backpack(inv, self.user))


class Sell(ui.View):
    def __init__(self, user: discord.Member):
        super().__init__()
        self.user = user

    @ui.button(label="Sell", style=discord.ButtonStyle.blurple)
    async def sell(self, i: discord.Interaction, button: ui.Button):
        await i.response.send_modal(SellForm(self.user, i.message))

    @ui.button(label="Exit", style=discord.ButtonStyle.red)
    async def exit(self, i: discord.Interaction, button: ui.Button):
        await i.response.defer()
        self.stop()

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user != self.user:
            await i.response.send_message(
                "You aren't the explorer here!",
                ephemeral=True
            )
            return False
        return True
