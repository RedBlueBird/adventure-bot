import typing as t

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db_manager as dm
import util as u
from views import CardPages


def res_display(
        user: discord.Member, res: list
) -> tuple[discord.Embed, discord.ui.View | None]:
    if not res:
        embed = discord.Embed(
            title="Nothing came up! :(",
            color=discord.Color.red()
        )
        return embed, None

    view = CardPages(user, override=res)
    return view.page_embed(), view


class CardSearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(aliases=["cs", "search"], description="Search your cards.")
    async def card_search(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="Here's the things you can search by:") \
                .add_field(name="Level", value=f"`{u.PREF}card_search (level)`") \
                .add_field(name="Name", value=f"`{u.PREF}card_search (name)`") \
                .add_field(name="Rarity", value=f"`{u.PREF}card_search (rarity)`") \
                .add_field(name="Energy cost", value=f"`{u.PREF}card_search (energy)`")
            await ctx.reply(embed=embed)

    @card_search.command()
    async def level(self, ctx: Context, level: int):
        res = dm.get_user_cards(
            ctx.author.id, add_rules=f"AND card_level = {level}"
        )
        embed, view = res_display(ctx.author, res)
        await ctx.send(embed=embed, view=view)

    @card_search.command()
    async def name(self, ctx: Context, name: str):
        res = dm.get_user_cards(
            ctx.author.id, add_rules=f"AND card_name LIKE '%{name}%'"
        )
        embed, view = res_display(ctx.author, res)
        await ctx.send(embed=embed, view=view)

    @card_search.command()
    async def rarity(
            self, ctx: Context,
            rarity: t.Literal["legendary", "exclusive", "epic", "rare", "common", "monster"]
    ):
        cards = dm.get_user_cards(ctx.author.id)
        rarity_terms = {
            "L": "legendary",
            "EX": "exclusive",
            "E": "epic",
            "R": "rare",
            "C": "common",
            "M": "monster"
        }

        res = [
            c for c in cards
            if rarity == rarity_terms.get(u.cards_dict(c[2], c[1])["rarity"], None)
        ]
        embed, view = res_display(ctx.author, res)
        await ctx.send(embed=embed, view=view)

    @card_search.command()
    async def energy(self, ctx: Context, energy: int):
        user_cards = dm.get_user_cards(ctx.author.id)

        res = [c for c in user_cards if energy == u.cards_dict(c[2], c[1])["cost"]]
        embed, view = res_display(ctx.author, res)
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(CardSearch(bot))
