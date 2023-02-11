import typing as t

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db_manager as dm
import util as u


RARITIES = {
    "C": "Common", "R": "Rare", "E": "Epic", "EX": "Exclusive",
    "L": "Legendary", "M": "N/A", "NA": "N/A"
}


class CardSearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="card_search",
        description="Searches your cards according to a query.",
        aliases=["cardsearch", "cs", "search"]
    )
    async def card_search(
            self, ctx: Context,
            search_type: t.Literal["level", "name", "rarity", "energy cost"],
            query: str | None = None,
            page: int = 1
    ) -> None:
        """
        Searches your cards according to a query.
        :param search_type: What to search by
        :param query: The actual search query that the bot will search by
        :param page: The page of the card results to go to.
        """
        p_len = 15

        page = max(page, 1)

        a = ctx.author
        deck_ids = [card[0] for card in dm.get_user_deck(a.id, dm.get_user_deck_slot(a.id))]

        res = []
        search_type = search_type.lower()
        if search_type == "level":
            additional = "" if query is None else f"AND card_level = {query}"
            res = dm.get_user_cards(a.id, add_rules=additional)

        elif search_type == "name":
            res = dm.get_user_cards(
                a.id, add_rules="" if query is None else f"AND card_name LIKE '%{query}%'"
            )

        elif search_type == "rarity":
            user_cards = dm.get_user_cards(a.id)
            rarity_terms = {
                "L": ["legendary", "legend", "leg", "le", "l"],
                "EX": ["exclusive", "exclu", "exc", "ex"],
                "E": ["epic", "ep", "e"],
                "R": ["rare", "ra", "rr", "r"],
                "C": ["common", "com", "co", "c"],
                "M": ["monsters", "monster", "mon", "mons", "mo", "most", "mosts", "m", "ms"],
                "NA": ["not_available", "notavailable", "not_ava", "notava", "not", "no", "na", "n/a", "n"]
            }

            if query is None:
                res = user_cards
            else:
                for x in user_cards:
                    if query.lower() in rarity_terms[u.cards_dict(x[2], x[1])["rarity"]]:
                        res.append(x)

        elif search_type == "energy cost":
            user_cards = dm.get_user_cards(a.id)

            if query is None:
                res = user_cards
            else:
                for x in user_cards:
                    if query == str(u.cards_dict(x[2], x[1])["cost"]):
                        res.append(x)

        if not res:
            await ctx.send(f"{ctx.author.mention}, nothing matched your search!")
            return
        elif len(res) <= (page - 1) * p_len:
            await ctx.send(f"{ctx.author.mention}, you don't have any cards on page {page}!")
            return

        all_cards = []

        for x in res[(page - 1) * p_len:(page - 1) * p_len + p_len]:
            card = f"[{u.rarity_cost(x[1])}] **{x[1]}**, " \
                   f"lv: **{x[2]}**, id: `{x[0]}` "
            if x[0] in deck_ids:
                card = f"**>**{card}"
            all_cards.append(card)

        embed = discord.Embed(
            title="Results",
            description="\n".join(all_cards),
            color=discord.Color.gold()
        )

        show_start = (page - 1) * p_len + 1
        show_end = min(show_start + 14, len(res))
        embed.set_footer(
            text=f"{show_start}-{show_end}/{len(res)} cards displayed in page {page}"
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(CardSearch(bot))
