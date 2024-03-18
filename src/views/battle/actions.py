import discord

from helpers.battle import BattleData2
from helpers import db_manager as dm


class Actions(discord.ui.View):
    def __init__(self, battledata: BattleData2, stats_msg: discord.message):
        super().__init__()
        self.battledata = battledata
        self.stats_msg = stats_msg

    @discord.ui.button(label="Deck", style=discord.ButtonStyle.blurple, row=0)
    async def deck_button(self, i: discord.Interaction, button: discord.ui.Button):
        await i.response.send_message(embed=self.battledata.show_deck(i.user.id), ephemeral=True)

    @discord.ui.button(label="Backpack", style=discord.ButtonStyle.blurple, row=0)
    async def backpack_button(self, i: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Test - Backpack", color=discord.Color.gold())
        await i.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.secondary, row=1)
    async def finish_button(self, i: discord.Interaction, button: discord.ui.Button):
        result = self.battledata.show_finish(i.user.id)
        if result is not None:
            await i.response.send_message(content=result, ephemeral=True)
        elif self.battledata.game_end:
            team_colors = ["Red", "Purple", "White", "Blue", "Orange", "Green"]
            alive_teams = [0, 0, 0, 0, 0, 0]
            alive_names = ["Members:"]
            team_number = 0
            for player in self.battledata.players:
                if player.dead or player.flee:
                    continue
                alive_names.append(player.user.name)
                alive_teams[player.team - 1] = 1
                team_number = player.team

            embed = discord.Embed(title="Battle Ended!")
            if sum(alive_teams) == 1:
                embed.add_field(
                    name=f"Team {team_colors[self.battledata.team_orders.index(team_number)]} Won!",
                    value=" ".join(alive_names),
                )
            else:
                embed.add_field(name="Draw!", value="No one won the match")

            await self.stats_msg.edit(embed=self.battledata.show_stats(), view=None)
            await i.response.send_message(embed=embed)
        else:
            await i.response.edit_message(embed=self.battledata.show_stats())

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.success, row=1)
    async def refresh_button(self, i: discord.Interaction, button: discord.ui.Button):
        await self.stats_msg.edit(view=None)
        await i.response.send_message(embed=self.battledata.show_stats(), view=self)
        self.stats_msg = await i.original_response()

    @discord.ui.button(label="Flee", style=discord.ButtonStyle.danger, row=1)
    async def flee_button(self, i: discord.Interaction, button: discord.ui.Button):
        player = self.battledata.player_selector(i.user.id)
        if player.id != self.battledata.turn:
            name = self.battledata.players[self.battledata.turn - 1].user.name
            flee_message = f"{player.user.mention} It's {name}'s turn!"
        else:
            dm.set_user_battle_command(i.user.id, "flee")
            flee_message = f"{i.user.mention} Press `Finish` to confirm fleeing."
        await i.response.send_message(content=flee_message, ephemeral=True)
