import discord
import discord.ui as ui

from .adventure_template import AdventureTemplate


class LevelSelect(AdventureTemplate):
    def __init__(self, user: discord.Member):
        super().__init__(user)
        self.level = None

    @discord.ui.select(
        options=[
            discord.SelectOption(label="Easy - Lvl 1", value="1"),
            discord.SelectOption(label="Normal - Lvl 5", value="2"),
            discord.SelectOption(label="Hard - Lvl 10", value="3"),
            discord.SelectOption(label="Insane - Lvl 15", value="4"),
        ]
    )
    async def select(self, i: discord.Interaction, select: ui.Select):
        self.level = int(select.values[0])
        await i.response.defer()
        self.stop()
