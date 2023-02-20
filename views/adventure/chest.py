import typing as t

import discord
import discord.ui as ui

from helpers import db_manager as dm
import util as u
from .adventure_template import AdventureTemplate


def transfer(
        item: str, amt: int,
        from_: dict, from_name: str,
        to: dict, to_name: str, to_storage: int = float("inf")
):
    if amt <= 0:
        raise ValueError("That's an invalid amount to take!")

    item = u.items_dict(item.lower())
    name = item["name"].lower()
    descr = f"{amt} **[{item['rarity']}/{item['weight']}] {item['name']}**"
    if from_.get(name, {}).get("items", 0) < amt:
        raise ValueError(f"You don't have {descr} in your {from_name}!")

    weight = item["weight"] * amt
    if u.get_bp_weight(to) + weight > to_storage:
        raise ValueError(f"Your {to_name} doesn't have enough space for {descr}!")

    from_[name]["items"] -= amt
    if from_[name]["items"] == 0:
        del from_[name]

    if name in to:
        to[name]["items"] += amt
    else:
        to[name] = {"items": amt}


async def submit_chest_form(
        i: discord.Interaction,
        action:  t.Literal["take", "deposit"],
        item: str, amt: str
):
    if not amt.isdigit():
        await i.response.send_message(
            "That's an invalid amount to take!",
            ephemeral=True
        )
        return
    amt = int(amt)

    uid = i.user.id
    inv = dm.get_user_inventory(uid)
    chest = dm.get_user_storage(uid)
    lvl = dm.get_user_level(uid)
    try:
        if action == "take":
            transfer(
                item, amt,
                chest, "chest",
                inv, "backpack", 100
            )
        else:
            transfer(
                item, amt,
                inv, "backpack",
                chest, "chest", u.chest_storage(lvl)
            )
    except ValueError as e:
        await i.response.send_message(e, ephemeral=True)

    embed = u.container_embed(chest, "Chest", lvl) \
        .add_field(name="Your Backpack", value=f"```{u.container_str(inv)}```")
    await i.response.edit_message(embed=embed)

    dm.set_user_inventory(uid, inv)
    dm.set_user_storage(uid, chest)


class TakeForm(ui.Modal, title="Take something!"):
    item = ui.TextInput(label="Item", placeholder="What do you want to take?")
    amt = ui.TextInput(label="Amount", placeholder="How much do you want to take?")

    def __init__(self, user: discord.Member, chest_msg: discord.Message):
        super().__init__()
        self.user = user
        self.chest_msg = chest_msg

    async def on_submit(self, i: discord.Interaction):
        await submit_chest_form(i, "take", self.item.value, self.amt.value)


class DepositForm(ui.Modal, title="Deposit something!"):
    item = ui.TextInput(label="Item", placeholder="What do you want to deposit?")
    amt = ui.TextInput(label="Amount", placeholder="How much do you want to deposit?")

    def __init__(self, user: discord.Member, chest_msg: discord.Message):
        super().__init__()
        self.user = user
        self.chest_msg = chest_msg

    async def on_submit(self, i: discord.Interaction):
        await submit_chest_form(i, "deposit", self.item.value, self.amt.value)


class Chest(AdventureTemplate):
    @ui.button(label="Take", style=discord.ButtonStyle.blurple)
    async def take(self, i: discord.Interaction, button: ui.Button):
        await i.response.send_modal(TakeForm(i.user, i.message))

    @ui.button(label="Deposit", style=discord.ButtonStyle.blurple)
    async def deposit(self, i: discord.Interaction, button: ui.Button):
        await i.response.send_modal(DepositForm(i.user, i.message))

    @ui.button(label="Close Chest", style=discord.ButtonStyle.red)
    async def exit(self, i: discord.Interaction, button: ui.Button):
        await i.response.defer()
        self.stop()
