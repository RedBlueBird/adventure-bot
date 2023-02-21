import discord
from discord.ui import UserSelect

from helpers import db_manager as dm
import util as u
from helpers import Player

class BattleActions(discord.ui.View):
    def __init__(self, players: list[Player]):
        super().__init__()
        self.players = players

    @discord.ui.button(label="Deck", style=discord.ButtonStyle.blurple, row=1)
    async def deck_button(
        self, i: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="Test - Deck",
            color=discord.Color.gold()
        )
        await i.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Backpack", style=discord.ButtonStyle.blurple, row=1)
    async def backpack_button(
        self, i: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="Test - Backpack",
            color=discord.Color.gold()
        )
        await i.response.send_message(embed=embed, ephemeral=True)


    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, row=1)
    async def skip_button(self, i: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Test - Skip",
            color=discord.Color.gold()
        )
        await i.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Flee", style=discord.ButtonStyle.danger, row=1)
    async def flee_button(self, i: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Test - Flee",
            color=discord.Color.gold()
        )
        await i.response.send_message(embed=embed, ephemeral=True)