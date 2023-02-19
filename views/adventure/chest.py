import discord
import discord.ui as ui

from helpers import db_manager as dm
import util as u


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
    print(from_)
    print(to)
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


class TakeForm(ui.Modal, title="Take something!"):
    item = ui.TextInput(label="Item", placeholder="What do you want to take?")
    amt = ui.TextInput(label="Amount", placeholder="How much do you want to take?")

    def __init__(self, user: discord.Member, chest_msg: discord.Message):
        super().__init__()
        self.user = user
        self.chest_msg = chest_msg

    async def on_submit(self, i: discord.Interaction):
        amt = self.amt.value
        if not amt.isdigit():
            await i.response.send_message(
                "That's an invalid amount to take!",
                ephemeral=True
            )
            return
        amt = int(amt)

        inv = dm.get_user_inventory(self.user.id)
        chest = dm.get_user_storage(self.user.id)
        try:
            transfer(
                self.item.value, amt,
                chest, "chest",
                inv, "backpack", 100
            )
        except ValueError as e:
            await i.response.send_message(e, ephemeral=True)

        lvl = dm.get_user_level(self.user.id)
        embed = u.container_embed(chest, "Chest", lvl) \
            .add_field(name="Your Backpack", value=f"```{u.container_str(inv)}```")
        await i.response.edit_message(embed=embed)

        dm.set_user_inventory(self.user.id, inv)
        dm.set_user_storage(self.user.id, chest)


class DepositForm(ui.Modal, title="Deposit something!"):
    item = ui.TextInput(label="Item", placeholder="What do you want to deposit?")
    amt = ui.TextInput(label="Amount", placeholder="How much do you want to deposit?")

    def __init__(self, user: discord.Member, chest_msg: discord.Message):
        super().__init__()
        self.user = user
        self.chest_msg = chest_msg

    async def on_submit(self, i: discord.Interaction):
        amt = self.amt.value
        if not amt.isdigit():
            await i.response.send_message(
                "That's an invalid amount to take!",
                ephemeral=True
            )
            return
        amt = int(amt)

        inv = dm.get_user_inventory(self.user.id)
        chest = dm.get_user_storage(self.user.id)
        lvl = dm.get_user_level(self.user.id)
        storage = u.chest_storage(lvl)
        try:
            transfer(
                self.item.value, amt,
                inv, "backpack",
                chest, "chest", storage
            )
        except ValueError as e:
            await i.response.send_message(e, ephemeral=True)

        embed = u.container_embed(chest, "Chest", lvl) \
            .add_field(name="Your Backpack", value=f"```{u.container_str(inv)}```")
        await i.response.edit_message(embed=embed)

        dm.set_user_inventory(self.user.id, inv)
        dm.set_user_storage(self.user.id, chest)


class Chest(ui.View):
    def __init__(self, user: discord.Member):
        super().__init__()
        self.user = user

    @ui.button(label="Take", style=discord.ButtonStyle.blurple)
    async def take(self, i: discord.Interaction, button: ui.Button):
        await i.response.send_modal(TakeForm(i.user, i.message))

    @ui.button(label="Deposit", style=discord.ButtonStyle.blurple)
    async def deposit(self, i: discord.Interaction, button: ui.Button):
        await i.response.send_modal(DepositForm(i.user, i.message))

    @ui.button(label="Close Chest", style=discord.ButtonStyle.red)
    async def close(self, i: discord.Interaction, button: ui.Button):
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
