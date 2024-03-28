import discord
import discord.ui as ui

import db
from helpers import util as u


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
        player = db.Player.get_by_id(i.user.id)
        await i.response.send_message(
            embed=u.container_embed(player.inventory, "Backpack"), ephemeral=True
        )


class InteractionCheckMixin:
    def __init__(self, user: discord.Member, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user != self.user:
            await i.response.send_message("You aren't the explorer here!", ephemeral=True)
            return False
        return True
