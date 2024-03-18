import typing as t
import random

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db_manager as dm, util as u, resources as r, checks
from views import Confirm


async def confirm_purchase(ctx: commands.Context, msg: str) -> tuple[discord.Message, bool]:
    view = Confirm()
    msg = await ctx.reply(content=msg, view=view)
    await view.wait()

    if view.value is None:
        await msg.edit(content="Purchase timed out.", view=None)
        return msg, False
    if not view.value:
        await msg.edit(content="Purchase canceled.", view=None)
        return msg, False
    return msg, True


class Purchase(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(aliases=["b"], description="Buy stuff!")
    async def buy(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            embed = (
                discord.Embed(title="Here's the things you can buy:")
                .add_field(name="Card Packs", value=f"`{r.PREF}buy (card pack name)`")
                .add_field(name="Coins", value=f"`{r.PREF}buy coins (coin deal name)`")
                .add_field(name="Tickets", value=f"`{r.PREF}buy tickets (ticket deal name)`")
                .add_field(name="Shop Refresh", value=f"`{r.PREF}buy r`")
                .add_field(name="Single Card", value=f"`{r.PREF}buy (card #)`")
                .add_field(name="All Cards", value=f"`{r.PREF}buy all`")
            )
            await ctx.reply(embed=embed)

    @buy.command()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def pack(
        self,
        ctx: Context,
        pack: t.Literal["basic", "fire", "evil", "electric", "defensive", "pro"],
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
        amt = card_packs[pack][2]
        lvls = card_packs[pack][3]

        if amt + dm.get_user_cards_count(a.id) > r.MAX_CARDS:
            await ctx.reply("You don't have enough space for this card pack!")
            return

        if gems < gem_cost or tokens < token_cost:
            cost = "Nothing"  # should never happen
            if gem_cost > 0 and token_cost > 0:
                cost = f"{gem_cost} {r.ICONS['gem']} and {token_cost} {r.ICONS['token']}"
            elif gem_cost > 0:
                cost = f"{gem_cost} {r.ICONS['gem']}"
            elif token_cost > 0:
                cost = f"{token_cost} {r.ICONS['token']}"
            await ctx.reply(f"You need {cost} to buy a {pack.title()} card pack!")
            return

        msg, confirm = await confirm_purchase(
            ctx, f"Are you sure you want to buy a {pack.title()} card pack?"
        )
        if not confirm:
            return

        dm.set_user_gem(a.id, gems - gem_cost)
        dm.set_user_token(a.id, tokens - token_cost)
        if pack != "confetti":
            gained_cards = []
            cards_msg = []
            for _ in range(amt):
                lvl = u.log_level_gen(random.randint(1, lvls))
                name = u.random_card(lvl, pack)
                gained_cards.append((a.id, name, lvl))
                cards_msg.append(f"[{u.rarity_cost(name)}] **{name}** lv: **{lvl}** \n")

            dm.add_user_cards(gained_cards)

            cards_msg.append("=======================\n")
            cards_msg.append(f"**From the {pack.title()} Pack**")
            embed = discord.Embed(
                title="You got:",
                description=" ".join(cards_msg),
                color=discord.Color.gold(),
            )
        else:
            dm.add_user_cards([(a.id, "Confetti Cannon", 10)])
            embed = discord.Embed(
                title=f"**From the Anniversary Pack!!**",
                description="You got\n[Ex/7] Confetti Cannon lv: 10",
                color=discord.Color.green(),
            )

        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.set_footer(text=f"Gems left: {gems - gem_cost}")
        await msg.edit(content=None, embed=embed, view=None)

    @buy.command()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def coins(self, ctx: Context, deal: t.Literal["gc1", "gc2", "gc3"]):
        # gem payment & coin gain
        deals = {"gc1": [3, 1000], "gc2": [6, 2250], "gc3": [24, 11000]}

        a = ctx.author
        gems = dm.get_user_gem(a.id)

        gem_cost = deals[deal][0]
        coin_gain = deals[deal][1]

        if gems < gem_cost:
            await ctx.reply("You don't have enough gems!")
            return

        view = Confirm()
        msg = await ctx.reply(
            f"Are you sure you want to buy {coin_gain} {r.ICONS['coin']} "
            f"with {gem_cost} {r.ICONS['gem']}?",
            view=view,
        )
        await view.wait()

        if view.value is None:
            await msg.edit(content="Purchase timed out.", view=None)
            return
        if not view.value:
            await msg.edit(content="Purchase canceled.", view=None)
            return

        dm.set_user_gem(a.id, gems - gem_cost)
        dm.set_user_coin(a.id, dm.get_user_coin(a.id) + coin_gain)

        embed = discord.Embed(
            title="You got:",
            description=f"**{coin_gain}** {r.ICONS['coin']}!",
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"Gems left: {gems - gem_cost}")
        await msg.edit(content=None, embed=embed, view=None)

    @buy.command()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def tickets(self, ctx: Context, deal: t.Literal["rt1", "rt2", "rt3"]):
        deals = {"rt1": [2, 1], "rt2": [4, 3], "rt3": [6, 5]}

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
            f"Are you sure you want to buy {ticket_gain} {r.ICONS['tick']} "
            f"with {gem_cost} {r.ICONS['gem']}?",
        )
        if not confirm:
            return

        dm.set_user_gem(a.id, gems - gem_cost)
        dm.set_user_ticket(a.id, tickets + ticket_gain)

        embed = discord.Embed(
            title="You got:",
            description=f"**{ticket_gain}** {r.ICONS['tick']}!",
            color=discord.Color.gold(),
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
            u.deal_card(dm.get_user_level(a.id)) for _ in range(9 if dm.has_premium(a.id) else 6)
        ]
        dm.set_user_coin(a.id, coins - cost)
        dm.set_user_deals(a.id, ",".join(gained_cards))

        dm.set_user_coin(a.id, coins - cost)
        await ctx.reply(f"You refreshed your shop for {cost} {r.ICONS['coin']}!")

    @buy.command()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def all(self, ctx: Context):
        a = ctx.author
        coins = dm.get_user_coin(a.id)
        deals = [i.split(".") for i in dm.get_user_deals(a.id).split(",")]

        cost = sum(
            [u.card_coin_cost(card, int(lvl)) if lvl[0] != "-" else 0 for lvl, card in deals]
        )

        count = sum([lvl[0] != "-" for lvl, _ in deals])
        if count + dm.get_user_cards_count(a.id) > r.MAX_CARDS:
            await ctx.reply("You don't have enough space to buy everything!")
            return
        if count == 0:
            await ctx.reply("You've already bought everything!")
            return
        if coins < cost:
            await ctx.reply(f"You need {cost} {r.ICONS['coin']} to buy everything!")
            return

        cards = f"all {count} cards" if count > 1 else "the one remaining card"
        msg, confirm = await confirm_purchase(
            ctx,
            f"Do you want to buy {cards} in the shop for {cost} {r.ICONS['coin']}?",
        )
        if not confirm:
            return

        gained_cards = []
        cards_msg = []
        for lvl, name in deals:
            if lvl[0] == "-":
                continue

            lvl = int(lvl)
            gained_cards.append((a.id, name, lvl))
            cards_msg.append(
                f"[{u.rarity_cost(name)}] **{name}** lv: **{lvl}** - "
                f"**{u.card_coin_cost(name, lvl)}** {r.ICONS['coin']}"
            )

        dm.add_user_cards(gained_cards)
        dm.set_user_coin(a.id, coins - cost)
        dm.set_user_deals(a.id, ",".join(["-." + i[1] for i in deals]))

        embed = discord.Embed(
            title="You Bought:",
            description="\n".join(cards_msg),
            color=discord.Color.gold(),
        )
        embed.add_field(name="Total Cost", value=f"{cost} {r.ICONS['coin']}")
        embed.set_footer(text=f"You have {coins - cost} golden coins left")
        await msg.edit(content=None, embed=embed, view=None)

    @buy.command()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def card(self, ctx: Context, card: int):
        a = ctx.author
        coins = dm.get_user_coin(a.id)
        deals = [i.split(".") for i in dm.get_user_deals(a.id).split(",")]

        if not 1 <= card < len(deals):
            await ctx.reply(f"The card number must be between 1 and {len(deals)}!")
            return

        card -= 1
        lvl, name = deals[card]
        if lvl[0] == "-":
            await ctx.reply("You already bought this card!")
            return
        if dm.get_user_cards_count(a.id) == r.MAX_CARDS:
            await ctx.reply("You don't have space for this card!")
            return

        card_cost = u.card_coin_cost(name, int(lvl))
        if coins < card_cost:
            await ctx.reply("You don't have enough golden coins to buy that card!")
            return

        msg, confirm = await confirm_purchase(
            ctx,
            f"Are you sure you want to purchase **[{u.rarity_cost(name)}] {name} lv: {lvl}**?",
        )
        if not confirm:
            return

        await msg.edit(
            content=(
                "You successfully bought a "
                f"**[{u.rarity_cost(name)}] {name} "
                f"lv: {lvl}** with "
                f"{card_cost} {r.ICONS['coin']}!"
            ),
            view=None,
        )

        dm.add_user_cards([(a.id, deals[card][1], int(lvl))])
        dm.set_user_coin(a.id, coins - card_cost)
        deals[card][0] = f"-{lvl}"
        dm.set_user_deals(a.id, ",".join([".".join(i) for i in deals]))


async def setup(bot):
    await bot.add_cog(Purchase(bot))
