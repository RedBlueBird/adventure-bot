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
        select: discord.ui.Select = self.children[0]
        for index, option in enumerate(select.options):
            if option.value.lower() == self.name:
                select.options[index].default = True
            else:
                select.options[index].default = False

    async def lb_embed(self):
        limit = 10
        order_by = None
        desc_fmt = None
        match self.name:
            case "level":
                order_by = "XP"
                desc_fmt = "• Level: {}, Exp: {}"
            case "coins":
                order_by = "Golden Coins"
                desc_fmt = "• Golden Coins: {}, Shiny Gems: {}"
            case "gems":
                order_by = "Shiny Gems"
                desc_fmt = "• Shiny Gems: {}, Golden Coins: {}"
            case "medals":
                order_by = "Medals"
                desc_fmt = "• Medals: {}"
            case "tokens":
                order_by = "Tokens"
                desc_fmt = "• Tokens: {}"
        assert order_by is not None and desc_fmt is not None

        top_players = []
        all_players = dm.get_leaderboard(order_by, limit)
        for index, (_, user_id, *data) in enumerate(all_players):
            user = await self.bot.fetch_user(user_id)
            username = f"**[{index + 1}] {user}**"
            description = desc_fmt.format(*data)
            if user_id == self.user_id:
                description = f"__{description}__"
            top_players.append(username + "\n" + description + "\n")

        embed = discord.Embed(
            title=f"Leaderboard - most {order_by}",
            description="".join(top_players),
            color=discord.Color.gold()
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
    async def select_leaderboard(self, i: discord.Interaction, select: discord.ui.Select):
        self.name = select.values[0].lower()
        self.change_select_default()
        await i.response.edit_message(embed=await self.lb_embed(), view=self)
