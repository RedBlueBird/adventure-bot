import typing as t

import discord
from discord.ext import commands
from discord.ext.commands import Context

import db
from helpers import checks, resources as r
from views import CardPages


class CardSearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["cs", "search"], description="View your cards.")
    @checks.is_registered()
    async def card_search(
        self,
        ctx: Context,
        name: str | None = None,
        level: int | None = None,
        energy: int | None = None,
        rarity: (
            t.Literal["legendary", "exclusive", "epic", "rare", "common", "monster"] | None
        ) = None,
    ):
        player = db.Player.get_by_id(ctx.author.id)
        cards = db.Card.select().where(db.Card.owner == player)
        if name is not None:
            cards = cards.where(db.Card.name.contains(name))
        if level is not None:
            cards = cards.where(db.Card.level == level)
        cards = list(cards)

        if energy is not None:
            cards = filter(lambda c: r.card(c.name).cost == energy, cards)
        if rarity is not None:
            rarity = {
                "legendary": "L",
                "exclusive": "EX",
                "epic": "E",
                "rare": "R",
                "common": "C",
                "monster": "M",
            }[rarity]
            cards = filter(lambda c: r.card(c.name).rarity == rarity, cards)

        if cards:
            view = CardPages(ctx.author, ctx.author, cards=cards)
            await ctx.send(embed=view.page_embed(), view=view)
        else:
            embed = discord.Embed(title="Nothing came up! :(", color=discord.Color.red())
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(CardSearch(bot))
