import time

import discord
import discord.ui as ui

from views.adventure.template import InteractionCheckMixin


class Reaction(ui.View, InteractionCheckMixin):
    def __init__(self, user: discord.Member):
        super().__init__(timeout=5)
        self.user = user
        self.click_time = None

    @ui.button(label="Now!", style=discord.ButtonStyle.green)
    async def react(self, i: discord.Interaction, button: ui.Button):
        self.click_time = time.time()
        await i.response.defer()
        self.stop()
