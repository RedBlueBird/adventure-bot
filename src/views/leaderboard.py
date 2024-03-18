import discord
from discord.ext import commands

from helpers import resources as r
from db import db_manager as dm


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
            select.options[index].default = option.value.lower() == self.name

    async def leaderboard_embed(self):
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
            color=discord.Color.gold(),
        )
        return embed

    @discord.ui.select(
        options=[
            discord.SelectOption(label="Level", emoji=r.ICONS["exp"].emoji()),
            discord.SelectOption(label="Coins", emoji=r.ICONS["coin"].emoji()),
            discord.SelectOption(label="Gems", emoji=r.ICONS["gem"].emoji()),
            discord.SelectOption(label="Medals", emoji=r.ICONS["medal"].emoji()),
            discord.SelectOption(label="Tokens", emoji=r.ICONS["token"].emoji()),
        ]
    )
    async def select_leaderboard(self, i: discord.Interaction, select: discord.ui.Select):
        self.name = select.values[0].lower()
        self.change_select_default()
        await i.response.edit_message(embed=await self.leaderboard_embed(), view=self)
