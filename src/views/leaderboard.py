import typing as t

import discord
from discord.ext import commands

import db
import resources as r


class Leaderboard(discord.ui.View):
    def __init__(
        self,
        name: t.Literal["level", "coins", "gems", "medals", "tokens"],
        user_id: int,
        bot: commands.Bot,
    ):
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
        order_by = None
        desc_fmt = None
        match self.name:
            case "level":
                order_by = db.Player.xp
                desc_fmt = lambda p: f"• Level: {p.level}, Exp: {p.xp}"
            case "coins":
                order_by = db.Player.coins
                desc_fmt = lambda p: f"• Golden Coins: {p.coins}, Shiny Gems: {p.gems}"
            case "gems":
                order_by = db.Player.gems
                desc_fmt = lambda p: f"• Shiny Gems: {p.gems}, Golden Coins: {p.coins}"
            case "medals":
                order_by = db.Player.medals
                desc_fmt = lambda p: f"• Medals: {p.medals}"
            case "tokens":
                order_by = db.Player.event_tokens
                desc_fmt = lambda p: f"• Tokens: {p.event_tokens}"

        top_players = []
        all_players = db.Player.select().order_by(order_by.desc()).limit(10)
        for index, p in enumerate(all_players):
            user = await self.bot.fetch_user(p.id)
            username = f"**[{index + 1}] {user}**"
            description = desc_fmt(p)
            if p.id == self.user_id:
                description = f"__{description}__"
            top_players.append(f"{username}\n{description}\n")

        embed = discord.Embed(
            title=f"Leaderboard - most {self.name}",
            description="".join(top_players),
            color=discord.Color.gold(),
        )
        return embed

    @discord.ui.select(
        options=[
            discord.SelectOption(label="Level", emoji=str(r.ICONS["exp"])),
            discord.SelectOption(label="Coins", emoji=str(r.ICONS["coin"])),
            discord.SelectOption(label="Gems", emoji=str(r.ICONS["gem"])),
            discord.SelectOption(label="Medals", emoji=str(r.ICONS["medal"])),
            discord.SelectOption(label="Tokens", emoji=str(r.ICONS["token"])),
        ]
    )
    async def select_leaderboard(self, i: discord.Interaction, select: discord.ui.Select):
        self.name = select.values[0].lower()
        self.change_select_default()
        await i.response.edit_message(embed=await self.leaderboard_embed(), view=self)
