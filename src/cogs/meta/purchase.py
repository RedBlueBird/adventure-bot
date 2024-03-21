import typing as t
import random

import discord
from discord.ext import commands
from discord.ext.commands import Context

import db
from helpers import util as u, resources as r, checks, db_manager as dm
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
        player = db.Player.get_by_id(a.id)

        gem_cost = deals[deal][0]
        coin_gain = deals[deal][1]

        if player.gems < gem_cost:
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

        player.gems -= gem_cost
        player.coins += coin_gain
        player.save()

        embed = discord.Embed(
            title="You got:",
            description=f"**{coin_gain}** {r.ICONS['coin']}!",
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"Gems left: {player.gems}")
        await msg.edit(content=None, embed=embed, view=None)

    @buy.command()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def tickets(self, ctx: Context, deal: t.Literal["rt1", "rt2", "rt3"]):
        deals = {"rt1": [2, 1], "rt2": [4, 3], "rt3": [6, 5]}

        a = ctx.author
        player = db.Player.get_by_id(a.id)

        gem_cost = deals[deal][0]
        ticket_gain = deals[deal][1]
        max_tickets = 10 if player.has_premium() else 5

        if player.gems < gem_cost:
            await ctx.reply("You don't have enough gems!")
            return
        if player.raid_tickets + ticket_gain > max_tickets:
            await ctx.reply("You can't store that many tickets!")
            return

        msg, confirm = confirm_purchase(
            ctx,
            f"Are you sure you want to buy {ticket_gain} {r.ICONS['tick']} "
            f"with {gem_cost} {r.ICONS['gem']}?",
        )
        if not confirm:
            return

        player.gems -= gem_cost
        player.raid_tickets += ticket_gain
        player.save()

        embed = discord.Embed(
            title="You got:",
            description=f"**{ticket_gain}** {r.ICONS['tick']}!",
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"Gems left: {player.gems}")
        await msg.edit(content=None, embed=embed, view=None)

    @buy.command(aliases=["r"])
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def refresh(self, ctx: Context):
        a = ctx.author
        player = db.Player.get_by_id(a.id)
        cost = 200
        if player.coins < cost:
            await ctx.reply("You don't have enough coins!")
            return

        # 200 coins isn't that big of a cost, idt we need a confirm view here ~ sans
        card_amt = 9 if player.has_premium() else 6
        db.Deal.delete().where(db.Deal.player == player).execute()
        new_deals = [u.deal_card(player.level) for _ in range(card_amt)]
        db.Deal.insert_many(
            [{"player": player, "c_name": d["card"], "c_level": d["level"]} for d in new_deals]
        ).execute()

        player.coins -= cost
        player.save()

        await ctx.reply(f"You refreshed your shop for {cost} {r.ICONS['coin']}!")

    @buy.command()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def all(self, ctx: Context):
        a = ctx.author
        player = db.Player.get_by_id(a.id)

        cost = 0
        count = 0
        for d in player.deals:
            if not d.sold:
                cost += u.card_coin_cost(d.c_name, d.c_level)
                count += 1

        if count + len(player.cards) > r.MAX_CARDS:
            await ctx.reply("You don't have enough space to buy everything!")
            return
        if count == 0:
            await ctx.reply("You've already bought everything!")
            return
        if player.coins < cost:
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
        for d in player.deals:
            card = r.card(d.c_name)
            gained_cards.append({"owner": player, "name": card.id, "level": d.c_level})
            cards_msg.append(
                f"{card} lv: {d.c_level} - "
                f"**{u.card_coin_cost(d.c_name, d.c_level)}** {r.ICONS['coin']}"
            )
            d.sold = True
            d.save()  # not sure how bad this is?

        db.Card.insert_many(gained_cards).execute()
        player.coins -= cost
        player.save()

        embed = discord.Embed(
            title="You Bought:",
            description="\n".join(cards_msg),
            color=discord.Color.gold(),
        )
        embed.add_field(name="Total Cost", value=f"{cost} {r.ICONS['coin']}")
        embed.set_footer(text=f"You have {player.coins} golden coins left")
        await msg.edit(content=None, embed=embed, view=None)

    @buy.command()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    @checks.is_registered()
    async def card(self, ctx: Context, card: int):
        a = ctx.author
        player = db.Player.get_by_id(a.id)
        card -= 1  # 0-index it

        if not 0 <= card < len(player.deals):
            await ctx.reply(f"The card number must be between 1 and {len(player.deals)}!")
            return

        deal = player.deals[card]
        if deal.sold:
            await ctx.reply("You already bought this card!")
            return

        # please tell me this doesn't fetch all the cards (it probably does but :cope:)
        if len(player.cards) == r.MAX_CARDS:
            await ctx.reply("You don't have space for this card!")
            return

        card = r.card(deal.c_name)
        card_cost = u.card_coin_cost(deal.c_name, deal.c_level)
        if player.coins < card_cost:
            await ctx.reply("You don't have enough golden coins to buy that card!")
            return

        msg, confirm = await confirm_purchase(
            ctx,
            f"Are you sure you want to purchase a level {deal.c_level} {card}?",
        )
        if not confirm:
            return

        await msg.edit(
            content=(
                f"You successfully bought a level {deal.c_level} {card} with "
                f"{card_cost} {r.ICONS['coin']}!"
            ),
            view=None,
        )

        db.Card.create(owner=player, name=deal.c_name, level=deal.c_level)
        player.coins -= card_cost
        player.save()
        deal.sold = True
        deal.save()


async def setup(bot):
    await bot.add_cog(Purchase(bot))
