import typing as t

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db_manager as dm
from views import CardPages


class CardSearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["cs", "search"], description="Search your cards.")
    async def card_search(
        self,
        ctx: Context,
        name: str | None = None,
        level: int | None = None,
        energy: int | None = None,
        rarity: (
            t.Literal["legendary", "exclusive", "epic", "rare", "common", "monster"]
            | None
        ) = None,
    ):
        cards = dm.get_user_cards(
            ctx.author.id, name=name, level=level, energy=energy, rarity=rarity
        )
        if cards:
            view = CardPages(ctx.author, ctx.author, cards=cards)
            await ctx.send(embed=view.page_embed(), view=view)
        else:
            embed = discord.Embed(
                title="Nothing came up! :(", color=discord.Color.red()
            )
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(CardSearch(bot))
