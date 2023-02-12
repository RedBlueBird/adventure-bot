import discord
from discord.ext import commands

from helpers import db_manager as dm
import util as u


class Leaderboard(discord.ui.View):
    def __init__(self, name: str, user_id: int, bot: commands.Bot):
        super().__init__()
        self.name = name
        self.user_id = user_id
        self.bot = bot
        self.change_select_default()

    def change_select_default(self):
        select = self.children[0]
        for index, option in enumerate(select.options):
            if option.value == self.name:
                select.options[index].default = True
            else:
                select.options[index].default = False

    async def generate_embed(self):
        limit = 10
        description_format = None
        match self.name:
            case "Level":
                order_by = "XP"
                description_format = "• Level: {}, Exp: {}"
            case "Coins":
                order_by = "Golden Coins"
                description_format = "• Golden Coins: {}, Shiny Gems: {}"
            case "Gems":
                order_by = "Shiny Gems"
                description_format = "• Shiny Gems: {}, Golden Coins: {}"
            case "Medals":
                order_by = "Medals"
                description_format = "• Medals: {}"
            case "Tokens":
                order_by = "Tokens"
                description_format = "• Tokens: {}"
        assert description_format is not None

        top_players = []
        all_players = dm.get_leaderboard(order_by, limit)
        for index, (_, user_id, *data) in enumerate(all_players):
            user = await self.bot.fetch_user(user_id)
            username = f"**[{index + 1}] {user}**"
            description = description_format.format(*data)
            if user_id == self.user_id:
                description = f"__{description}__"
            top_players.append(username + "\n" + description + "\n")

        embed = discord.Embed(
            title=f"Leaderboard - most {order_by}", description="".join(top_players), color=discord.Color.gold()
        )
        return embed

    @discord.ui.select(
        options=[
            discord.SelectOption(label="Level", emoji=u.ICON["exp"]),
            discord.SelectOption(label="Coins", emoji=u.ICON["coin"]),
            discord.SelectOption(label="Gems", emoji=u.ICON["gem"]),
            discord.SelectOption(label="Medals", emoji=u.ICON["medal"]),
            discord.SelectOption(label="Tokens", emoji=u.ICON["token"]),
        ]
    )
    async def select_leaderboard(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.name = select.values[0]
        self.change_select_default()
        await interaction.response.edit_message(embed=await self.generate_embed(), view=self)
