import typing as t
import random

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db_manager as dm
from helpers import checks
import util as u
from views import Confirm


async def confirm_purchase(ctx: commands.Context, msg: str) -> tuple[discord.Message, bool]:
    view = Confirm()
    msg = await ctx.reply(content=msg, view=view)
    await view.wait()

    if view.value is None:
        await msg.edit(content="Purchase timed out", view=None)
        return msg, False
    if not view.value:
        await msg.edit(content="Purchase cancelled", view=None)
        return msg, False
    return msg, True


class Purchase(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(aliases=["b"], description="Buy stuff!")
    async def buy(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="Here's the things you can buy:") \
                .add_field(name="Card Packs", value=f"`{u.PREF}buy (card pack name)`") \
                .add_field(name="Coins", value=f"`{u.PREF}buy coins (coin deal name)`") \
                .add_field(name="Tickets", value=f"`{u.PREF}buy tickets (ticket deal name)`") \
                .add_field(name="Shop Refresh", value=f"`{u.PREF}buy r`") \
                .add_field(name="Single Card", value=f"`{u.PREF}buy all`") \
                .add_field(name="All Cards", value=f"`{u.PREF}buy (card #)`")
            await ctx.reply(embed=embed)

    @buy.command()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def pack(
            self, ctx: Context,
            pack: t.Literal["basic", "fire", "evil", "electric", "defensive", "pro"]
    ):
        # gem, token, cards, levels
        card_packs = {
            "basic": [3, 0, 3, 128],
            "fire": [5, 0, 4, 128],
            "evil": [5, 0, 4, 128],
            "electric": [5, 0, 4, 128],
            "defensive": [5, 0, 4, 128],
            "pro": [24, 0, 6, 16],
            # "confetti": [0, 40, 6, 16]
        }

        a = ctx.author
        gems = dm.get_user_gem(a.id)
        tokens = dm.get_user_token(a.id)

        gem_cost = card_packs[pack][0]
        token_cost = card_packs[pack][1]
        cards_count = card_packs[pack][2]
        cards_level = card_packs[pack][3]

        if cards_count + dm.get_user_cards_count(a.id) > u.MAX_CARDS:
            await ctx.reply("You don't have enough space for this card pack!")
            return

        if gems < gem_cost or tokens < token_cost:
            cost = "Nothing"  # should never happen but oh well
            if gem_cost > 0 and token_cost > 0:
                cost = f"{gem_cost} {u.ICON['gem']} and {token_cost} {u.ICON['token']}"
            elif gem_cost > 0:
                cost = f"{gem_cost} {u.ICON['gem']}"
            elif token_cost > 0:
                cost = f"{token_cost} {u.ICON['token']}"
            await ctx.reply(f"You need {cost} to buy a {pack.title()} Edition card pack!")
            return

        msg, confirm = confirm_purchase(
            ctx,
            f"Are you sure you want to purchase a {pack.title()} Edition card pack?"
        )
        if not confirm:
            return

        dm.set_user_gem(a.id, gems - gem_cost)
        dm.set_user_token(a.id, tokens - token_cost)
        if pack != "confetti":
            gained_cards = []
            cards_msg = []
            for _ in range(cards_count):
                card_level = u.log_level_gen(random.randint(1, cards_level))
                card_name = u.random_card(card_level, pack)
                gained_cards.append((a.id, card_name, card_level))
                cards_msg.append(f"[{u.rarity_cost(card_name)}] **{card_name}** lv: **{card_level}** \n")

            dm.add_user_cards(gained_cards)

            cards_msg.append("=======================\n")
            cards_msg.append(f"**From {pack.title()} Edition card pack**")
            embed = discord.Embed(
                title="You got:",
                description=" ".join(cards_msg),
                color=discord.Color.gold()
            )
        else:
            dm.add_user_cards([(a.id, "Confetti Cannon", 10)])
            embed = discord.Embed(
                title=f"**From the Anniversary card pack!!**",
                description="You got\n[Ex/7] Confetti Cannon lv: 10",
                color=discord.Color.green()
            )

        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.set_footer(text=f"Gems left: {gems - gem_cost}")
        await msg.edit(content=None, embed=embed, view=None)

    @buy.command()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def coins(
            self, ctx: Context,
            deal: t.Literal["gc1", "gc2", "gc3"]
    ):
        # gem payment & coin gain
        deals = {
            "gc1": [3, 1000],
            "gc2": [6, 2250],
            "gc3": [24, 11000]
        }

        a = ctx.author
        gems = dm.get_user_gem(a.id)

        gem_cost = deals[deal][0]
        coin_gain = deals[deal][1]

        if gems < gem_cost:
            await ctx.reply("You don't have enough gems!")
            return

        view = Confirm()
        msg = await ctx.reply(
            f"Are you sure you want to buy {coin_gain} {u.ICON['coin']} "
            f"with {gem_cost} {u.ICON['gem']}?",
            view=view
        )
        await view.wait()

        if view.value is None:
            await msg.edit(content="Purchase timed out", view=None)
            return
        if not view.value:
            await msg.edit(content="Purchase cancelled", view=None)
            return

        dm.set_user_gem(a.id, gems - gem_cost)
        dm.set_user_coin(a.id, dm.get_user_coin(a.id) + coin_gain)

        embed = discord.Embed(
            title="You got:",
            description=f"**{coin_gain}** {u.ICON['coin']}!",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Gems left: {gems - gem_cost}")
        await msg.edit(content=None, embed=embed, view=None)

    @buy.command()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def tickets(
            self, ctx: Context,
            deal: t.Literal["rt1", "rt2", "rt3"]
    ):
        deals = {
            "rt1": [2, 1],
            "rt2": [4, 3],
            "rt3": [6, 5]
        }

        a = ctx.author
        gems = dm.get_user_gem(a.id)

        gem_cost = deals[deal][0]
        ticket_gain = deals[deal][1]
        tickets = dm.get_user_ticket(a.id)
        max_tickets = 10 if dm.has_premium(a.id) else 5

        if gems < gem_cost:
            await ctx.reply("You don't have enough gems!")
            return
        if tickets + ticket_gain > max_tickets:
            await ctx.reply("You can't store that many tickets!")
            return

        msg, confirm = confirm_purchase(
            ctx,
            f"Are you sure you want to buy {ticket_gain} {u.ICON['tick']} "
            f"with {gem_cost} {u.ICON['gem']}?"
        )
        if not confirm:
            return

        dm.set_user_gem(a.id, gems - gem_cost)
        dm.set_user_ticket(a.id, tickets + ticket_gain)

        embed = discord.Embed(
            title="You got:",
            description=f"**{ticket_gain}** {u.ICON['tick']}!",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Gems left: {gems - gem_cost}")
        await msg.edit(content=None, embed=embed, view=None)

    @buy.command(aliases=["r"])
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def refresh(self, ctx: Context):
        a = ctx.author
        coins = dm.get_user_coin(a.id)
        cost = 200
        if coins < cost:
            await ctx.reply("You don't have enough coins!")
            return

        # 200 coins isn't that big of a cost, idt we need a confirm view here ~ sans
        gained_cards = [
            u.add_a_card(dm.get_user_level(a.id))
            for _ in range(9 if dm.has_premium(a.id) else 6)
        ]
        dm.set_user_coin(a.id, coins - cost)
        dm.set_user_deals(a.id, ",".join(gained_cards))

        dm.set_user_coin(a.id, coins - cost)
        await ctx.reply(f"You refreshed your shop for {cost} {u.ICON['coin']}!")

    @buy.command()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def all(self, ctx: Context):
        a = ctx.author
        coins = dm.get_user_coin(a.id)
        deals = [i.split(".") for i in dm.get_user_deals(a.id).split(',')]

        cost = sum([u.compute_card_cost(i[1], int(i[0])) if i != "-" else 0 for i in deals])
        count = sum([1 if i[0] != "-" else 0 for i in deals])

        if count + dm.get_user_cards_count(a.id) > u.MAX_CARDS:
            await ctx.reply("You don't have enough space to buy everything!")
            return
        if count == 0:
            await ctx.reply("You've already bought everything!")
            return
        if coins < cost:
            await ctx.reply(f"You need {cost} {u.ICON['coin']} to buy everything!")
            return

        cards = f"all {count} cards" if count > 1 else "the one remaining card"
        msg, confirm = await confirm_purchase(
            ctx,
            f"Do you want to buy {cards} "
            f"in the shop for {cost} {u.ICON['coin']}?"
        )
        if not confirm:
            return

        gained_cards = []
        cards_msg = []
        total_cost = sum([u.compute_card_cost(i[1], int(i[0])) if i != "-" else 0 for i in deals])
        for d in deals:
            if d[0] == "-":
                continue
            gained_cards.append((a.id, d[1], int(d[0])))
            cards_msg.append(
                f"[{u.rarity_cost(d[1])}] **{d[1]}** lv: **{int(d[0])}** - "
                f"**{u.compute_card_cost(d[1], int(d[0]))}** {u.ICON['coin']} \n"
            )

        dm.add_user_cards(gained_cards)
        dm.set_user_coin(a.id, coins - total_cost)
        cards_msg.append("=======================\n")
        cards_msg.append(f"**Total Cost - {total_cost} {u.ICON['coin']}**")
        dm.set_user_deals(a.id, ",".join(["-." + i[1] for i in deals]))
        embed = discord.Embed(
            title="You Bought:",
            description=" ".join(cards_msg),
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"You have {coins - total_cost} golden coins left")
        await msg.edit(content=None, embed=embed, view=None)

    @buy.command()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def card(self, ctx: Context, card: int):
        a = ctx.author
        coins = dm.get_user_coin(a.id)
        deals = [i.split(".") for i in dm.get_user_deals(a.id).split(',')]

        card -= 1
        if not (0 < card + 1 < len(deals)):
            await ctx.reply(f"The deal number must be between 1 and {len(deals)}!")
            return
        if deals[card][0] == "-":
            await ctx.reply("You already bought this card!")
            return
        if dm.get_user_cards_count(a.id) == u.MAX_CARDS:
            await ctx.reply("You don't have space for this card!")
            return

        card_cost = u.compute_card_cost(deals[card][1], int(deals[card][0]))
        if coins < card_cost:
            await ctx.reply("You don't have enough golden coins to buy that card!")
            return

        msg, confirm = await confirm_purchase(
            ctx,
            f"Are you sure you want to purchase "
            f"**[{u.rarity_cost(deals[card][1])}] {deals[card][1]} lv: {deals[card][0]}**?"
        )
        if not confirm:
            return

        dm.add_user_cards([(a.id, deals[card][1], int(deals[card][0]))])
        dm.set_user_coin(a.id, coins - card_cost)
        dm.set_user_deals(a.id, ",".join([".".join(i) for i in deals]))
        await msg.edit(
            content="You successfully bought a "
                    f"**[{u.rarity_cost(deals[card][1])}] {deals[card][1]} "
                    f"lv: {deals[card][0]}** with "
                    f"{card_cost} {u.ICON['coin']}!",
            view=None
        )
        deals[card][0] = "-"


async def setup(bot):
    await bot.add_cog(Purchase(bot))
