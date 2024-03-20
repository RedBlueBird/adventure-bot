import discord
import discord.ui as ui

from helpers import util as u, db_manager as dm


class Exit(ui.Button):
    def __init__(self, label: str = "Exit", row: int | None = None):
        super().__init__(label=label, row=row, style=discord.ButtonStyle.danger)

    async def callback(self, i: discord.Interaction):
        assert self.view is not None
        await i.response.defer()
        self.view.stop()


class Backpack(ui.Button):
    def __init__(self, label: str = "Backpack", row: int | None = None):
        super().__init__(label=label, row=row, style=discord.ButtonStyle.blurple)

    async def callback(self, i: discord.Interaction):
        inv = dm.get_user_inventory(self.view.user.id)
        await i.response.send_message(embed=u.container_embed(inv, "Backpack"), ephemeral=True)


class InteractionCheckMixin:
    user: discord.Member

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user != self.user:
            await i.response.send_message("You aren't the explorer here!", ephemeral=True)
            return False
        return True
