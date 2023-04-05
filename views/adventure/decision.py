import typing as t

import discord
import discord.ui as ui

from views.adventure.template import InteractionCheckMixin, Backpack


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


class Decision(ui.View, InteractionCheckMixin):
    def __init__(
            self,
            user: discord.Member,
            choices: t.Iterable[str],
            loc_file: discord.File | None = None
    ):
        super().__init__()

        self.user = user
        
        self.decision = None
        self.show_map = None
        self.loc_img = loc_file

        toggle, exit_button = self.children
        self.remove_item(toggle)
        self.remove_item(exit_button)

        order = [Backpack(row=1), exit_button, DecisionSelect(choices)]
        if loc_file is not None:
            order.insert(1, toggle)
        for i in order:
            self.add_item(i)

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
        await i.response.defer()
        self.stop()
