import typing as t

import discord
import discord.ui as ui

from helpers import db_manager as dm
import util as u
from .adventure_template import AdventureTemplate


class DecisionSelect(ui.Select["Decision"]):
    def __init__(self, choices: t.Iterable[str]):
        choices = [
            discord.SelectOption(label=c, value=c)
            for c in choices
        ]
        super().__init__(options=choices, placeholder="What do you want to do?")

    async def callback(self, i: discord.Interaction):
        assert self.view is not None
        self.view.decision = self.values[0]
        await i.response.defer()
        self.view.stop()


class Decision(AdventureTemplate):
    def __init__(
            self,
            user: discord.Member,
            choices: t.Iterable[str],
            loc_file: discord.File | None = None
    ):
        super().__init__(user)

        self.decision = None
        self.add_item(DecisionSelect(choices))

        self.show_map = None
        self.loc_img = loc_file
        if loc_file is None:
            self.remove_item(self.children[1])

    @ui.button(label="Backpack", row=1, style=discord.ButtonStyle.blurple)
    async def backpack(self, i: discord.Interaction, button: ui.Button):
        inv = dm.get_user_inventory(self.user.id)
        await i.response.send_message(
            embed=u.container_embed(inv, "Backpack"),
            ephemeral=True
        )

    @ui.button(label="Toggle Map", row=1, style=discord.ButtonStyle.blurple)
    async def toggle_map(self, i: discord.Interaction, button: ui.Button):
        msg = i.message
        await i.response.defer()
        if msg.attachments:
            msg = await msg.remove_attachments(*msg.attachments)
        else:
            self.loc_img.fp.seek(0)
            msg = await msg.edit(attachments=[self.loc_img])
        self.show_map = bool(msg.attachments)

    @ui.button(label="Exit", row=1, style=discord.ButtonStyle.red)
    async def exit(self, i: discord.Interaction, button: ui.Button):
        self.decision = "exit"
        await super().exit(i, button)