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


class Search(commands.Cog, name="search"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(name="info", description="Looks up info on entities.")
    async def info(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="Here's the things you can search up:") \
                .add_field(name="Cards", value="`a.info card`") \
                .add_field(name="Monsters", value="`a.info monster`") \
                .add_field(name="Items", value="`a.info item`") \
                .add_field(name="Effects", value="`a.info effect`")
            await ctx.reply(embed=embed)

    @info.command()
    async def card(self, ctx: Context, name: str, level: int = 1):
        card_info = u.cards_dict(level, " ".join(name.lower().split("_")))
        info_str = [
            f"**Name:** {card_info['name']}",
            f"**Level:** {level}",
            f"**Rarity:** {RARITIES[card_info['rarity']]}",
            f"**Energy Cost:** {card_info['cost']}",
            f"**Accuracy:** {card_info['acc']}%",
            f"**Critical Chance:** {card_info['crit']}%"
        ]

        if card_info["rarity"] == "M":
            info_str.insert(len(info_str), "**[Monster Card]** - Unobtainable")
        if card_info["rarity"] == "EX":
            info_str.insert(len(info_str), "**[Exclusive Card]** - Obtainable in events")

        embed = discord.Embed(title="Card's info:", description=None, color=discord.Color.green())
        embed.add_field(name="Description: ", value="\n".join(info_str), inline=False)
        embed.add_field(name="Uses: ", value=u.fill_args(card_info, level), inline=False)
        embed.add_field(name="Brief: ", value=card_info["brief"], inline=False)
        """
        if "journal" in card_info:
            embed.add_field(name="Scout's Journal: ", value="*" + card_info["journal"] + "*", inline=False)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        """
        await ctx.send(embed=embed)

    @info.command()
    async def monster(self, ctx: Context, name: str, level: int = 1):
        mob_info = u.mobs_dict(level, " ".join(name.lower().split("_")))
        info_str = [
            f"**Name:** {mob_info['name']}",
            f"**Level:** " + str(level),
            f"**Rarity:** {RARITIES[mob_info['rarity']]}",
            f"**Energy Lag:** {mob_info['energy_lag']} turns",
            f"**Health:** {mob_info['health']}",
            f"**Stamina:** {mob_info['stamina']}"
        ]

        embed = discord.Embed(title="Mob's info:", description=None, color=discord.Color.green())
        embed.add_field(name="Description: ", value="\n".join(info_str), inline=False)
        embed.add_field(name="Brief: ", value=f"*{mob_info['brief']}*", inline=False)
        """
        if "tip" in mob_info:
            embed.add_field(name="Fighting Tips: ", value="*" + mob_info["tip"] + "*", inline=False)
        if "journal" in mob_info:
            embed.add_field(name="Scout's Journal: ", value="*" + mob_info["journal"] + "*", inline=False)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        """
        await ctx.send(embed=embed)

    @info.command()
    async def item(self, ctx: Context, name: str):
        item_info = u.items_dict(" ".join(name.lower().split("_")))
        name = item_info["name"]
        info_str = [
            f"**Name:** {name}",
            f"**Weight:** {item_info['weight']}",
            f"**Rarity:** {RARITIES[item_info['rarity']]}",
            f"**Accuracy:** {item_info['acc']}%",
            f"**Critical Chance:** {item_info['crit']}%",
            f"**One Use:** {item_info['one_use']}",
            f"**Use In Battle:** {item_info['in_battle']}",
            f"**Sell Price:** {item_info['sell']}gc",
            f"**Abbreviation:** {item_info['abb']}"
        ]

        embed = discord.Embed(title="Item's info:", description=None, color=discord.Color.green())
        embed.add_field(name="Description: ", value="\n".join(info_str), inline=False)
        embed.add_field(name="Uses: ", value=item_info["description"], inline=False)
        embed.add_field(name="Brief: ", value=f"*{item_info['brief']}*", inline=False)

        """
        if "journal" in item_info:  
            embed.add_field(name="Scout's Journal: ", value="*" + item_info["journal"] + "*", inline=False)
        embed.set_thumbnail(url=ctx.author.avatar.url)a.
        """
        # print(u.ICON[item_info['name'].lower()])
        if name.lower() in u.ICON:
            icon = u.ICON[name.lower()]
            icon_id = icon[icon.rfind(":") + 1:-1]
            embed.set_image(url=f"https://cdn.discordapp.com/emojis/{icon_id}.png")
        await ctx.send(embed=embed)

    @info.command()
    async def effect(self, ctx: Context, name: str):
        fx_info = u.fx_dict(" ".join(name.lower().split("_")))
        embed = discord.Embed(title="Effect's info:", description=None, color=discord.Color.green())
        embed.add_field(name="Description: ", value=f"**Name:** {fx_info['name']}", inline=False)
        embed.add_field(name="Uses: ", value=fx_info["description"], inline=False)
        embed.set_image(
            url=f"https://cdn.discordapp.com/emojis/"
                f"{u.CONVERT[fx_info['name'].lower()][4:-1]}.png"
        )
        await ctx.send(embed=embed)

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
    await bot.add_cog(Search(bot))
