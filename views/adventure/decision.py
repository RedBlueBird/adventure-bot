import typing as t

import discord
import discord.ui as ui

from helpers import db_manager as dm
import util as u


class DecisionSelect(ui.Select["Decision"]):
    def __init__(self, choices: t.Iterable[str]):
        choices = [
            discord.SelectOption(label=c, value=c)
            for c in choices
        ]
        super().__init__(options=choices, placeholder="Where do you want to go?")

    async def callback(self, i: discord.Interaction):
        assert self.view is not None
        self.view.decision = self.values[0]
        await i.response.defer()
        self.view.stop()


class Decision(ui.View):
    def __init__(
            self,
            user: discord.Member,
            loc_file: discord.File,
            choices: t.Iterable[str]
    ):
        super().__init__()
        self.user = user
        self.loc_img = loc_file
        self.decision = None
        self.add_item(DecisionSelect(choices))

    @ui.button(label="Backpack", row=1, style=discord.ButtonStyle.blurple)
    async def backpack(self, i: discord.Interaction, button: ui.Button):
        inv = dm.get_user_inventory(self.user.id)
        await i.response.send_message(
            embed=u.display_backpack(inv, self.user, "Backpack"),
            ephemeral=True
        )

    @ui.button(label="Toggle Map", row=1, style=discord.ButtonStyle.blurple)
    async def toggle_map(self, i: discord.Interaction, button: ui.Button):
        msg = i.message
        await i.response.defer()
        if i.message.attachments:
            await i.message.remove_attachments(*msg.attachments)
        else:
            self.loc_img.fp.seek(0)
            await i.message.edit(attachments=[self.loc_img])

    @ui.button(label="Exit", row=1, style=discord.ButtonStyle.red)
    async def exit(self, i: discord.Interaction, button: ui.Button):
        self.decision = "exit"
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
