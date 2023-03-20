import discord
import discord.ui as ui

from views.adventure.template import AdventureTemplate


class Adventure(AdventureTemplate):
    def __init__(self, user: discord.Member, adv: dict, start: tuple[str, str, int]):
        super().__init__(user)
        self.adv = adv
        self.at = start
