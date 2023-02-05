import os
import random
import math
import datetime as dt
import asyncio
import io
from copy import deepcopy

from PIL import Image, ImageFont, ImageDraw
import discord
from discord.ext import commands

from helpers import db_manager as dm
import util as u
from helpers import checks


class Actions(commands.Cog, name="actions"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["d"], brief="Get your daily rewards!")
    @checks.is_registered()
    async def daily(self, ctx: commands.Context):
        """Get your daily rewards!"""
        member = ctx.message.author
        user_coin = dm.get_user_coin(member.id)
        user_exp = dm.get_user_exp(member.id)
        user_medal = dm.get_user_medal(member.id)
        user_level = dm.get_user_level(member.id)
        user_streak = dm.get_user_streak(member.id)
        user_ticket = dm.get_user_ticket(member.id)
        user_premium = dm.get_user_premium(member.id)
        user_daily = dm.get_user_daily(member.id)

        if user_daily.date() == dt.date.today():
            dts = u.time_til_midnight()
            await ctx.send(f"{member.mention}, your next daily is in {dts}!")
            return

        streak = int(user_streak) + 1
        medal_reward = 1
        ticket_reward = 1
        max_streak = 7
        max_tickets = 5
        tick_msg = ""

        if user_premium.date() > dt.date.today():
            max_streak = 14
            max_tickets = 10
        if user_daily.date() < dt.date.today() - dt.timedelta(days=1):
            streak = 1
        elif streak >= max_streak:
            streak = max_streak
        if streak >= 7:
            medal_reward = 2
        if user_ticket >= max_tickets or user_level < 4:
            ticket_reward = 0
        else:
            tick_msg = f"+{ticket_reward} {u.ICON['tick']}"

        user_cards_count = dm.get_user_cards_count(member.id)

        if user_cards_count < 500:
            card_level = u.log_level_gen(random.randint(2 ** (max(0, 5 - (user_level // 4))),
                                                         2 ** (10 - math.floor(user_level / 10))))
            card = u.random_card(card_level, "normal")
            dm.add_user_cards([(member.id, card, card_level)])
            card_msg = f"Obtained **[{u.rarity_cost(card)}] {card} lv: {card_level}**!"
        else:
            dm.set_user_coin(member.id, user_coin + 250)
            card_msg = f"Received extra 250 {u.ICON['coin']}!"

        if random.randint(1, 7) == 1:  # one in 7 chance ig

            new_coins = user_coin + 400 + math.floor(user_level / 5) * 20 + streak * 80
            new_exps = user_exp + 200
            new_medals = user_medal + medal_reward * 4
            await ctx.send(
                f"{member.mention} JACKPOT!!! \n"
                f"**+{math.floor(user_level / 5) * 20 + 400 + streak * 80} "
                f"{u.ICON['coin']} +200 {u.ICON['exp']}"
                f" +{medal_reward * 4} {u.ICON['medal']} {tick_msg}! \n"
                f"Daily streak {streak}/{max_streak} {u.ICON['streak']}** \n{card_msg}"
            )
        else:
            new_coins = user_coin + 100 + math.floor(user_level / 5) * 5 + streak * 20
            new_exps = user_exp + 50
            new_medals = user_medal + medal_reward
            await ctx.send(
                f"{member.mention} \n"
                f"**+{math.floor(user_level / 5) * 5 + 100 + streak * 20} {u.ICON['coin']} +50 {u.ICON['exp']}"
                f" +{medal_reward}{u.ICON['medal']} {tick_msg}\n"
                f"Daily streak {streak}/{max_streak} {u.ICON['streak']}** \n{card_msg}"
            )

        dm.set_user_coin(member.id, new_coins)
        dm.set_user_exp(member.id, new_exps)
        dm.set_user_medal(member.id, new_medals)
        dm.set_user_ticket(member.id, user_ticket + ticket_reward)
        dm.set_user_daily(member.id, dt.date.today())
        dm.set_user_streak(member.id, streak)


    @commands.hybrid_command(aliases=["orders"], brief="cards")
    @checks.is_registered()
    async def order(self, ctx: commands.Context, card_property: str, order_by: str):
        """Command formatting for the card display order"""

        level_aliases = ["level", "levels", "card_level", "card_levels", "l"]
        id_aliases = ["id", "ids", "i"]
        name_aliases = ["name", "names", "card_name", "card_names", "n", "nam"]
        cost_aliases = ["energy_cost", "energycost", "energy", "cost", "ec", "en", "co", "e", "c"]
        rarity_aliases = ["rarity", "rare", "ra", "r"]
        ascending_aliases = ["ascending", "ascend", "a", "asc"]
        descending_aliases = ["descending", "descend", "d", "desc", "des"]

        member = ctx.message.author

        if card_property is None or order_by is None:
            await ctx.send(f"{member.mention}, the correct format for this command is "
                           f"`{u.PREF}order (level/name/id/cost/rarity) (ascending/descending)`!")
        else:
            order = [0, None, None]
            if order_by in ascending_aliases + descending_aliases:
                card_property = card_property.lower()
                if card_property in level_aliases:
                    order = [1, "level", " ascending"]
                elif card_property in name_aliases:
                    order = [3, "name", " ascending"]
                elif card_property in id_aliases:
                    order = [5, "id", " ascending"]
                elif card_property in cost_aliases:
                    order = [7, "cost", " ascending"]
                elif card_property in rarity_aliases:
                    order = [9, "rarity", " ascending"]
            if order_by in descending_aliases:
                order[0] += 1
                order[2] = " descending"
            if order == [0, None, None]:
                await ctx.send(f"{member.mention}, the correct format for this command is "
                               f"`{u.PREF}order (level/name/id/cost/rarity) (ascending/descending)`!")
            else:
                dm.set_user_order(member.id, order[0])
                await ctx.send(f"{member.mention}, the order had been set to {order[1]}{order[2]}.")

    @commands.hybrid_command(aliases=["buying"], brief="actions")
    @checks.is_registered()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    async def buy(self, ctx: commands.Context, to_buy="None"):
        """Command for buying items in the shop"""

        member = ctx.message.author
        deals = [i.split(".") for i in dm.get_user_deals(member.id).split(',')]
        user_cards_count = dm.get_user_cards_count(member.id)
        user_coin = dm.get_user_coin(member.id)
        user_gem = dm.get_user_gem(member.id)
        user_token = dm.get_user_token(member.id)
        user_ticket = dm.get_user_ticket(member.id)
        user_premium = dm.get_user_premium(member.id)
        user_level = dm.get_user_level(member.id)

        max_tickets = 5 if user_premium.date() < dt.date.today() else 10
        deal_type = "None"
        deal_msg = "None"
        deal_transaction = []

        #gem, token, cards, levels
        card_packs = {
            "basic": [3,0,3,128],
            "fire": [5,0,4,128],
            "evil": [5,0,4,128],
            "electric": [5,0,4,128],
            "defensive": [5,0,4,128],
            "pro": [24,0,6,16],
            #"confetti": [0,40,6,16]
        }
        #gem, coin, ticket
        currency_deals = {
            "gc1": [3,1000,0],
            "gc2": [6,2250,0],
            "gc3": [24,11000,0],
            "rt1": [2,0,1],
            "rt2": [4,0,3],
            "rt3": [6,0,5]
        }

        if to_buy.lower() in card_packs:
            gem_cost = card_packs[to_buy.lower()][0]
            token_cost = card_packs[to_buy.lower()][1]
            cards_count = card_packs[to_buy.lower()][2]
            cards_level = card_packs[to_buy.lower()][3]

            if user_gem >= gem_cost and user_token >= token_cost:
                if cards_count + user_cards_count > 500:
                    deal_msg = "Purchasing this card pack will exceed the 500 cards capacity for your inventory!"
                else:
                    deal_msg = f"Are you sure you want to purchase a {to_buy.lower().title()} Edition card pack?"
                    deal_type = "Card"
                    deal_transaction = [gem_cost, token_cost, cards_count, cards_level]
            else:
                if token_cost == 0:
                    deal_msg = f"You need {gem_cost} {u.ICON['gem']} in order to buy a {to_buy.lower().title()} Edition card pack!"
                else:
                    deal_msg = f"You need {token_cost} {u.ICON['token']} in order to buy a {to_buy.lower().title()} Edition card pack!"
        elif to_buy.lower() in currency_deals:
            gem_cost = currency_deals[to_buy.lower()][0]
            coin_gain = currency_deals[to_buy.lower()][1]
            ticket_gain = currency_deals[to_buy.lower()][2]

            if ticket_gain != 0:
                if user_gem < gem_cost:
                    deal_msg = f"You need least {gem_cost} {u.ICON['gem']} to buy {ticket_gain} {u.ICON['tick']}!"
                elif user_ticket + ticket_gain > max_tickets:
                    deal_msg = f"You can't buy {ticket_gain} {u.ICON['tick']}, it exceeds the maximum amount of {u.ICON['tick']} you can store!"
                else:
                    deal_type = "Currency"
                    deal_msg = f"Are you sure you want to buy {ticket_gain} {u.ICON['tick']} with {gem_cost} {u.ICON['gem']}?"
                    deal_transaction = [gem_cost, coin_gain, ticket_gain]
            else:
                if user_gem < gem_cost:
                    deal_msg = f"You need least {gem_cost} {u.ICON['gem']} to buy {coin_gain} {u.ICON['coin']}!"
                else:
                    deal_type = "Currency"
                    deal_msg = f"Are you sure you want to buy {coin_gain} {u.ICON['coin']} with {gem_cost} {u.ICON['gem']}?"
                    deal_transaction = [gem_cost, coin_gain, ticket_gain]
        elif to_buy.lower() in ["refresh", "ref", "re", "r"]:
            if user_coin < 200:
                deal_msg = f"You need least 200 {u.ICON['coin']} to refresh the shop!"
            else:
                deal_msg = f"Do you want to refresh the shop for 200 {u.ICON['coin']}?"
                deal_type = "Refresh"
        elif to_buy.lower() == "all":
            total_cost = sum([u.compute_card_cost(i[1],int(i[0])) if i != "-" else 0 for i in deals])
            total_count = sum([1 if i[0] != "-" else 0 for i in deals])

            if total_count + cards_count > 500:
                deal_msg = f"Purchasing those cards will exceed the 500 cards capacity for your inventory!"
            elif total_count == 0:
                deal_msg = f"You have already bought every card!"
            elif total_cost > user_coin:
                deal_msg = f"You need {total_cost} {u.ICON['coin']} to buy all cards in the shop!"
            else:
                deal_msg = f"Do you want to buy all {total_count} card(s) in the shop for {total_cost} {u.ICON['coin']}?"
                deal_type = "All"
        elif to_buy.isdigit():
            selection = int(to_buy)-1
            if not (0 < selection+1 < len(deals)):
                deal_msg = f"Number must be between 1 and {len(deals)}!"
            elif deals[selection][0] == "-":
                deal_msg = f"You already bought this card!"
            elif user_cards_count + 1 > 500:
                deal_msg = f"You are already at the maximum 500 cards capacity!"
            else:
                card_cost = u.compute_card_cost(deals[selection][1],int(deals[selection][0]))
                if card_cost > user_coin:
                    deal_msg = f"You don't have enough golden coins to buy that card!"
                else:
                    deal_msg = f"Are you sure you want to purchase **[{u.rarity_cost(deals[selection][1])}] {deals[selection][1]} lv: {deals[selection][0]}**?"
                    deal_type = "Single"

        if deal_type == "None":
            if deal_msg == "None":
                deal_msg = f"The correct format for this command is `{u.PREF}buy (1-{len(deals)}/all/refresh)`!"
            deal_msg = f"{member.mention} {deal_msg}"
            await ctx.send(deal_msg)
            return
        deal_msg = f"{member.mention} {deal_msg}"
        deal_msg = await ctx.send(deal_msg)
        await deal_msg.add_reaction("✅")
        await deal_msg.add_reaction("❎")
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0,
                                                        check=checks.valid_reaction(["❎", "✅"],
                                                                                    [member],
                                                                                    [deal_msg]))
        except asyncio.TimeoutError:
            await deal_msg.edit(content=f"{member.mention}, the transaction timed out.")
            await deal_msg.clear_reactions()
            return
        if reaction.emoji == "❎":
            await deal_msg.edit(content=f"{member.mention}, you cancelled the purchase.")
            await deal_msg.clear_reactions()
            return
        await deal_msg.delete()

        if deal_type == "Currency":
            dm.set_user_gem(member.id, user_gem - deal_transaction[0])
            dm.set_user_coin(member.id, user_coin + deal_transaction[1])
            dm.set_user_ticket(member.id, user_ticket + deal_transaction[2])
            if deal_transaction[1] != 0:
                deal_msg = f"**{deal_transaction[1]}** {u.ICON['coin']}!"
            else:
                deal_msg = f"**{deal_transaction[2]}** {u.ICON['tick']}!"

            embed = discord.Embed(title="You got:",
                                    description=deal_msg,
                                    color=discord.Color.gold())
            embed.set_thumbnail(url=ctx.message.author.avatar.url)
            embed.set_footer(text="Gems left: " + str(user_gem - deal_transaction[0]))
            await ctx.send(embed=embed)
        elif deal_type == "Card":
            dm.set_user_gem(member.id, user_gem - deal_transaction[0])
            dm.set_user_token(member.id, user_token - deal_transaction[1])
            if deal_transaction[0] > 0:
                gained_cards = []
                cards_msg = []
                for x in range(deal_transaction[2]):
                    card_level = u.log_level_gen(random.randint(1, deal_transaction[3]))
                    card_name = u.random_card(card_level, to_buy.lower())
                    gained_cards.append((member.id, card_name, card_level))
                    cards_msg.append(f"[{u.rarity_cost(card_name)}] **{card_name}** lv: **{card_level}** \n")

                dm.add_user_cards(gained_cards)

                cards_msg.append("=======================\n")
                cards_msg.append(f"**From {to_buy.lower().title()} Edition card pack**")
                embed = discord.Embed(title="You got:", description=" ".join(cards_msg),
                                        color=discord.Color.gold())

            elif deal_transaction[1] > 0:
                dm.add_user_cards([(member.id, "Confetti Cannon", 10)])
                embed = discord.Embed(
                    title=f"**From Anniversary card pack!!**",
                    description="You got\n [Ex/7] Confetti Cannon lv: 10",
                    color=discord.Color.green())

            embed.set_thumbnail(url=ctx.message.author.avatar.url)
            embed.set_footer(text="Gems left: " + str(user_gem - deal_transaction[0]))
            await ctx.send(embed=embed)
        elif deal_type == "Refresh":
            gained_cards = []
            if user_premium.date() < dt.date.today():
                for x in range(6):
                    deals_cards.append(u.add_a_card(player_lvl))
            else:
                for x in range(9):
                    deals_cards.append(u.add_a_card(player_lvl))
            dm.set_user_coin(member.id, user_coin - 200)
            dm.set_user_deals(member.id, ",".join(deals_cards))
            await ctx.send(f"{member.mention}, you refreshed your shop for 200 {u.ICON['coin']}!")
        elif deal_type == "All":
            gained_cards = []
            cards_msg = []
            total_cost = sum([u.compute_card_cost(i[1],int(i[0])) if i != "-" else 0 for i in deals])
            for x in deals:
                if x[0] == "-":
                    continue
                gained_cards.append((member.id, x[1], int(x[0])))
                cards_msg.append(
                        f"[{u.rarity_cost(x[1])}] **{x[1]}** lv: **{int(x[0])}** - "
                        f"**{dm.compute_card_cost(x[1], int(x[0]))}** {u.ICON['coin']} \n")

            dm.add_user_cards(gained_cards)
            dm.set_user_coin(member.id, user_coin - total_cost)
            cards_msg.append("=======================\n")
            cards_msg.append(f"**Total Cost - {total_cost} {u.ICON['coin']}**")
            dm.set_user_deals(member.id, ",".join(["-." + i[1] for i in deals]))
            embed = discord.Embed(title="You Bought:",
                                    description=" ".join(cards_msg),
                                    color=discord.Color.gold())
            embed.set_footer(text=f"You currently have {user_coin - total_cost} golden coins left")
            embed.set_thumbnail(url=ctx.message.author.avatar.url)
            await ctx.send(embed=embed)
        elif deal_type == "Single":
            selection = int(to_buy)-1
            card_cost = u.compute_card_cost(deals[selection][1],int(deals[selection][0]))
            await ctx.send(content=f"{member.mention}, you successfully bought a **[{u.rarity_cost(deals[selection][1])}] {deals[selection][1]} " + 
                                        f"lv: {deals[selection][0]}** with " + 
                                        f"{card_cost} {u.ICON['coin']}!")
            dm.add_user_cards([(member.id, deals[selection][1], deals[selection][0])])
            dm.set_user_coin(member.id, user_coin - card_cost)
            deals[selection][0] = "-"
            dm.set_user_deals(member.id, ",".join([".".join(i[:]) for i in deals]))

    @commands.command(aliases=["dis"], brief="cards")
    @checks.is_registered()
    @checks.not_preoccupied("discarding cards")
    async def discard(self, ctx: commands.Context, *card_id):
        """Remove the existences of the unwanted cards"""

        member = ctx.message.author

        if not card_id:
            await ctx.send(f"{member.mention}, the correct format is `{u.PREF}discard (* card_ids)`!")
            return

        card_ids = list(card_id)
        discard_ids = []
        discard_msg = []
        error_msg = []

        for x in card_ids:
            if not x.isdigit():
                error_msg.append(f"`{x}` is not a number!")
            card_name = dm.get_card_name(member.id, x)
            card_level = dm.get_card_level(member.id, x)
            card_decks = dm.get_card_decks(x)

            if not card_name:
                error_msg.append(f"You don't have a card with id `{x}`!")
            elif sum(card_decks):
                error_msg.append(f"Id `{x}` is equipped in at least one of your decks!")
            else:
                discard_ids.append((x, member.id))
                discard_msg.append(f"**[{u.rarity_cost(card_name)}] {card_name} lv: {card_level}** Id `{x}`")

        if len(error_msg) != 0:
            await ctx.send(f"{member.mention} " + " \n".join(error_msg))
            return

        msg = await ctx.send(
            f"{member.mention} \nAre you sure you want to discard: \n" + 
            f" \n".join(discard_msg) + 
            f"\n{u.ICON['bers']} *(Discarded cards can't be retrieved!)*"
        )

        await msg.add_reaction("✅")
        await msg.add_reaction("❎")
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=30.0,
                check=checks.valid_reaction(["❎", "✅"], ctx.message.author, msg)
            )
        except asyncio.TimeoutError:
            await msg.edit(content=f"{member.mention}, discarding cancelled")
            await msg.clear_reactions()
            return
        await msg.clear_reactions()
        if reaction.emoji == "❎":
            await msg.edit(content=f"{member.mention}, discarding cancelled")
            return

        dm.delete_user_cards(discard_ids)
        await msg.edit(content=f"{member.mention}, {len(discard_ids)} card(s) discarded successfully!")

    @commands.hybrid_command(aliases=["mer"], brief="cards")
    @checks.is_registered()
    @checks.not_preoccupied("trying to merge cards")
    async def merge(self, ctx: commands.Context, card1_id: int, card2_id: int):
        """Upgrade a card to next level with two cards"""

        a_id = ctx.message.author.id
        mention = ctx.message.author.mention

        dm.cur.execute(
            f"SELECT deck1,deck2,deck3,deck4,deck5,deck6 FROM playersachivements WHERE userid = '{a_id}'")
        decks = [int(k) for i in dm.cur.fetchall()[0] for k in i.split(",")]

        dm.cur.execute(f"SELECT card_name, card_level, owned_user FROM cardsinfo WHERE id = {card1_id}")
        card1 = dm.cur.fetchall()[0]
        if not card1:
            await ctx.send(f"{mention}, you don't have the first card!")
            return

        dm.cur.execute(f"SELECT card_name, card_level, owned_user FROM cardsinfo WHERE id = {card2_id}")
        card2 = dm.cur.fetchall()[0]
        if not card2:
            await ctx.send(f"{mention}, you don't have the second card!")
            return

        if card1[2] != str(a_id) or card2[2] != str(a_id):
            await ctx.send(f"{mention}, you have to own both cards!")
            return

        if card1[1] != card2[1] or \
                u.cards_dict(1, card1[0])["rarity"] != u.cards_dict(1, card2[0])["rarity"]:
            await ctx.send(f"{mention}, both cards need to be the same level and rarity!")
            return

        if card1[1] >= 15:
            await ctx.send(f"{mention}, the card to merge is maxed out!")
            return

        if card2 in decks:
            await ctx.send(
                f"{mention}, the sacrificial card you chose "
                "is currently in one of your deck slots- \n"
                f"`{u.PREF}remove (* card_ids)` first before you merge it away!"
            )
            return

        dm.cur.execute("SELECT * FROM playersinfo WHERE userid = " + str(a_id))
        player_info = dm.cur.fetchall()

        merge_cost = math.floor(((card1[1] + 1) ** 2) * 10)
        if player_info[0][5] < merge_cost:
            await ctx.send(f"{mention} You don't have enough coins ({merge_cost} coins) to complete this merge!")
            return

        msg = await ctx.send(
            f"{mention}, \n"
            f"**[{u.rarity_cost(card1[0])}] {card1[0]} lv: {card1[1]}**\n"
            f"**[{u.rarity_cost(card2[0])}] {card2[0]} lv: {card2[1]}**\n"
            f"merging cost {merge_cost} {u.ICON['coin']}."
        )
        await msg.add_reaction("✅")
        await msg.add_reaction("❎")
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=30.0,
                check=checks.valid_reaction(["❎", "✅"], ctx.message.author, msg)
            )
        except asyncio.TimeoutError:
            await msg.edit(content=f"{mention}, merging timed out")
            await msg.clear_reactions()
        else:
            if reaction.emoji == "❎":
                await msg.edit(content=f"{mention}, merging timed out")
                await msg.clear_reactions()
            else:
                await msg.delete()
                dm.log_quest(7, 1, a_id)
                sql = "UPDATE playersinfo SET coins = coins - %s, exps = exps + %s WHERE userid = %s"
                value = (math.floor(((card1[1] + 1) ** 2) * 10), (card1[1] + 1) * 10, a_id)
                dm.cur.execute(sql, value)
                dm.cur.execute(f"DELETE FROM cardsinfo WHERE id = {card2_id}")
                dm.cur.execute(f"UPDATE cardsinfo SET card_level = card_level + 1 WHERE id = {card1_id}")
                dm.db.commit()

                embed = discord.Embed(
                    title="Cards merged successfully!",
                    description=f"-{math.floor(((card1[1] + 1) ** 2) * 10)} {u.ICON['coin']} "
                                f"+{(card1[1] + 1) * 10} {u.ICON['exp']}",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name=f"You got a [{u.rarity_cost(card1[0])}] {card1[0]} lv: {card1[1] + 1} from:",
                    value=f"[{u.rarity_cost(card1[0])}] {card1[0]} lv: {card1[1]} \n"
                          f"[{u.rarity_cost(card2[0])}] {card2[0]} lv: {card2[1]}"
                )
                embed.set_thumbnail(url=ctx.message.author.avatar.url)
                await ctx.send(embed=embed)

    @commands.hybrid_command(brief="Trade with other players!")
    @checks.is_registered()
    @checks.not_preoccupied("trading")
    @checks.level_check(7)
    async def trade(self, ctx: commands.Context, target: discord.Member):
        """Trade with other players!"""
        author = ctx.message.author
        mention = author.mention
        dm.cur.execute(f"SELECT level, coins FROM playersinfo WHERE userid = '{target.id}'")
        target_info = dm.cur.fetchall()

        # do some check to see if the people are all valid
        if len(target_info) == 0:
            await ctx.send("User is not registered in the bot!")
            return

        target_info = target_info[0]
        if target_info[0] < 7:
            await ctx.send("User needs to be at least level 7 to trade!")
            return

        if target.id == author.id:
            await ctx.send("Tag a valid user other than yourself!")
            return

        trade_end = False
        confirmed = [False, False]

        deal_msg = await ctx.send(f"{target.mention}. Accept a trade with {mention}?")
        await deal_msg.add_reaction("✅")
        await deal_msg.add_reaction("❎")

        while not trade_end:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=60.0,
                    check=checks.valid_reaction(["❎", "✅"], [target, ctx.message.author], deal_msg)
                )
            except asyncio.TimeoutError:
                await deal_msg.edit(content=f"{mention}, trade cancelled due to afk {u.ICON['dead']}")
                await deal_msg.clear_reactions()
                return

            if reaction.emoji == "❎":
                await deal_msg.edit(content=f"{mention}, trade cancelled! :weary:")
                await deal_msg.clear_reactions()
                return

            if reaction.emoji == "✅" and user == target:
                break

        if str(target.id) in dm.queues:
            await deal_msg.edit(
                content=f"{mention}, trade cancelled! The target user is currently {dm.queues[str(target.id)]}!")
            await deal_msg.clear_reactions()
            return

        dm.cur.execute(
            f"SELECT deck1,deck2,deck3,deck4,deck5,deck6 FROM playersachivements WHERE userid = '{target.id}'")
        decks1 = [int(k) for i in dm.cur.fetchall()[0] for k in i.split(",")]
        dm.cur.execute(
            f"SELECT deck1,deck2,deck3,deck4,deck5,deck6 FROM playersachivements WHERE userid = '{author.id}'")
        decks2 = [int(k) for i in dm.cur.fetchall()[0] for k in i.split(",")]
        dm.cur.execute(f"SELECT level, coins FROM playersinfo WHERE userid = '{author.id}'")
        author_info = dm.cur.fetchall()[0]
        dm.queues[str(target.id)] = "trading"
        author_coins = 0
        target_coins = 0
        author_cards = {}
        target_cards = {}

        def tax():
            return max(
                round(author_coins * 0.1) + 150 * len(author_cards),
                round(target_coins * 0.1) + 150 * len(target_cards)
            )

        def offer():
            embed = discord.Embed(
                title=f"Trade ongoing!",
                description=f"`{u.PREF}(put/drop) (coin/card) (amount/card_id)` \n"
                            f"`{u.PREF}(confirm/exit/refresh)` \n"
                            f"16 cards at max per side per trade",
                color=discord.Color.gold()
            )
            author_offer = []
            target_offer = []
            for c in author_cards:
                author_offer.append(
                    f"[{u.rarity_cost(author_cards[c][0])}] {author_cards[c][0]}, "
                    f"lv: {author_cards[c][1]}, id: {c} "
                )
            for c in target_cards:
                target_offer.append(
                    f"[{u.rarity_cost(target_cards[c][0])}] {target_cards[c][0]}, "
                    f"lv: {target_cards[c][1]}, id: {c} "
                )

            if confirmed[0]:
                embed.add_field(
                    name=f"{author}: :white_check_mark:",
                    value=f"```Golden Coins: {author_coins} \n" + "\n".join(author_offer) + "```",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"{author}:",
                    value=f"```Golden Coins: {author_coins} \n" + "\n".join(author_offer) + "```",
                    inline=False
                )
            if confirmed[1]:
                embed.add_field(
                    name=f"{target}: :white_check_mark:",
                    value=f"```Golden Coins: {target_coins} \n" + "\n".join(target_offer) + "```",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"{target}:",
                    value=f"```Golden Coins: {target_coins} \n" + "\n".join(target_offer) + "```",
                    inline=False
                )

            embed.set_footer(text=f"Transaction fee: {tax()}")
            return embed

        trade_msg = await ctx.send(embed=offer())

        while not trade_end:
            try:
                reply_msg = await self.bot.wait_for(
                    "message", timeout=120.0,
                    check=checks.valid_reply('', [target, author], ctx.message.channel)
                )
            except asyncio.TimeoutError:
                await ctx.send(f"Well, no one showed up to the trade, so it was called off.")
                return

            reply_author = reply_msg.author
            reply_msg = [s.lower() for s in reply_msg.content[len(u.PREF):].split(" ")]
            if len(reply_msg) < 1:
                continue
            if reply_msg[0] in ["refresh", "re", "ref", "r"]:
                trade_msg = await ctx.send(embed=offer())
                continue
            elif reply_msg[0] == "exit":
                confirmed = [False, False]
                await ctx.send(f"Trade is cancelled by {reply_author}!")
                trade_end = True
                break
            elif reply_msg[0] == "confirm":
                if reply_author.id == author.id:
                    if author_coins + tax() <= author_info[1]:
                        confirmed[0] = True
                    else:
                        await ctx.send(
                            f"{ctx.message.author}, you can't afford the transaction fee!")
                        continue
                else:
                    if target_coins + tax() <= target_info[1]:
                        confirmed[1] = True
                    else:
                        await ctx.send(f"{target}, you can't afford the transaction fee!")
                        continue

            if len(reply_msg) < 3 and reply_msg[0] != "confirm":
                continue
            if reply_msg[0] in ["put", "pu"]:
                confirmed = [False, False]
                if reply_msg[1] in ["coin", "co", "coins"]:
                    try:
                        amount = max(int(reply_msg[2]), 0)
                        if reply_author.id == author.id:
                            if amount <= author_info[1]:
                                author_coins += amount
                            else:
                                await ctx.send(f"{ctx.message.author}, you don't have enough coins for this!")
                                continue
                        else:
                            if amount <= target_info[1]:
                                target_coins += amount
                            else:
                                await ctx.send(f"{target}, you don't have enough coins for this!")
                                continue
                    except:
                        continue

                elif reply_msg[1].lower() in ["card", "ca", "cards"]:
                    try:
                        card_id = int(reply_msg[2])
                        dm.cur.execute(
                            f"SELECT card_name, card_level FROM cardsinfo WHERE id = {card_id} AND owned_user = '{reply_author.id}'")
                        result = dm.cur.fetchall()[0]
                        if len(result) == 0:
                            await ctx.send(f"{reply_author}, you don't have this card id in your inventory!")
                            continue
                        else:
                            if reply_author.id == author.id:
                                if len(author_cards) == 16:
                                    await ctx.send(f"{ctx.message.author}, you can only put 16 cards at max per trade!")
                                elif card_id in author_cards:
                                    await ctx.send(f"{ctx.message.author}, you already put this card id in the offer!")
                                    continue
                                elif card_id in decks1:
                                    await ctx.send(
                                        f"{ctx.message.author}, you can't put a card from your deck into this offer!")
                                else:
                                    author_cards[card_id] = result
                            else:
                                if len(target_cards) == 16:
                                    await ctx.send(f"{target}, you can only put 16 cards at max per trade!")
                                elif card_id in target_cards:
                                    await ctx.send(f"{target}, you already put this card id in the offer!")
                                    continue
                                elif card_id in decks2:
                                    await ctx.send(f"{target}, you can't put a card from your deck into this offer!")
                                else:
                                    target_cards[card_id] = result
                    except:
                        continue

            elif reply_msg[0].lower() in ["drop", "dr", "dp"]:
                confirmed = [False, False]
                if reply_msg[1].lower() in ["coin", "co", "coins"]:
                    try:
                        amount = max(int(reply_msg[2]), 0)
                        if reply_author.id == author.id:
                            if amount <= author_coins:
                                author_coins -= amount
                            else:
                                await ctx.send(
                                    f"{ctx.message.author}, you can't drop more coins than what you have in your offer!")
                                continue
                        else:
                            if amount <= target_coins:
                                target_coins -= amount
                            else:
                                await ctx.send(f"{target}, you can't drop more coins than what you have in your offer!")
                                continue
                    except:
                        continue

                elif reply_msg[1].lower() in ["card", "ca", "cards"]:
                    try:
                        card_id = int(reply_msg[2])
                        if reply_author.id == author.id:
                            if card_id in author_cards:
                                del author_cards[card_id]
                            else:
                                await ctx.send(f"{ctx.message.author}, the card id you want to drop doesn't exist!")
                                continue
                        else:
                            if card_id in target_cards:
                                del target_cards[card_id]
                            else:
                                await ctx.send(f"{target}, the card if you want to drop doesn't exist!")
                                continue
                    except:
                        continue

            try:
                await trade_msg.edit(embed=offer())
            except:
                trade_msg = await ctx.send(embed=offer())

            if confirmed[0] and confirmed[1]:
                dm.cur.execute(
                    f"UPDATE playersinfo SET coins = coins + {target_coins} - {author_coins} - {tax()} WHERE userid = '{author.id}'")
                dm.cur.execute(
                    f"UPDATE playersinfo SET coins = coins + {author_coins} - {target_coins} - {tax()} WHERE userid = '{target.id}'")
                for card in author_cards:
                    dm.cur.execute(f"UPDATE cardsinfo SET owned_user = '{target.id}' WHERE id = {card}")
                for card in target_cards:
                    dm.cur.execute(f"UPDATE cardsinfo SET owned_user = '{author.id}' WHERE id = {card}")
                dm.db.commit()
                trade_end = True
                await ctx.send(f"Trade between {ctx.message.author} and {target} is now finished!")

    @commands.hybrid_command(aliases=["selectdeck", "sel", "se"], brief="Get a deck from your deck slots.")
    @checks.is_registered()
    async def select(self, ctx: commands.Context, deck_slot: int):
        """Get a deck from your deck slots."""

        a_id = ctx.message.author.id
        if not 1 <= deck_slot <= 6:
            await ctx.send("The deck slot number must between 1-6!")
            return

        dm.cur.execute(f"SELECT level FROM playersinfo WHERE userid = {a_id}")
        level = dm.cur.fetchall()[0][0]

        if level < u.DECK_LVL_REQ[deck_slot]:
            await ctx.send(f"Deck #{deck_slot} is unlocked at {u.DECK_LVL_REQ[deck_slot]}!")
            return

        dm.cur.execute(f"UPDATE playersinfo SET deck_slot = {deck_slot} WHERE userid = {a_id}")
        dm.db.commit()
        await ctx.send(f"Deck #{deck_slot} is now selected!")

    @commands.hybrid_command(brief="Returns the card IDs of your current deck.")
    @checks.is_registered()
    async def paste(self, ctx: commands.Context, deck_slot: int = None):
        """Returns the card IDs of your current deck."""

        a_id = ctx.message.author.id
        if deck_slot is None:
            dm.cur.execute(f"SELECT deck_slot FROM playersinfo WHERE userid = {a_id}")
            deck_slot = dm.cur.fetchall()[0][0]

        if not 1 <= deck_slot <= 6:
            await ctx.send("The deck slot number must between 1-6!")
            return

        db_deck = f"deck{deck_slot}"
        dm.cur.execute(f"SELECT {db_deck} FROM playersachivements WHERE userid = {a_id}")
        deck = dm.cur.fetchall()[0][0].split(",")
        deck = [" "] if deck == ['0'] else deck

        await ctx.send(f"All the card IDs in Deck #{deck_slot}: \n`{' '.join(deck)}`")

    @commands.hybrid_command(
        aliases=["replace", "switch", "change", "alter"],
        brief="Swap a card from your deck with another."
    )
    @checks.is_registered()
    @checks.not_preoccupied()
    async def swap(self, ctx: commands.Context, new_id: int, old_id: int):
        """Swap a card from your deck with another."""

        a_id = ctx.message.author.id
        mention = ctx.message.author.mention

        dm.cur.execute(f"SELECT deck_slot FROM playersinfo WHERE userid = {a_id}")
        deck_slot = dm.cur.fetchall()[0][0]

        db_deck = f"deck{deck_slot}"
        dm.cur.execute(f"SELECT {db_deck} FROM playersachivements WHERE userid = {a_id}")
        deck = dm.cur.fetchall()[0][0].split(",")

        old_id, new_id = str(old_id), str(new_id)
        if old_id not in deck or new_id in deck:
            await ctx.send(
                f"{mention}, the first card shouldn't exist in your deck #{deck_slot} "
                f"and the second card needs to exist in your deck #{deck_slot}!"
            )
            return

        dm.cur.execute(f"SELECT card_name, card_level FROM cardsinfo WHERE id = {new_id} AND owned_user = '{a_id}'")
        new = dm.cur.fetchall()[0]
        if not new:
            await ctx.send(f"{mention}, the first id doesn't exist in your card inventory.")
            return

        deck.remove(old_id)
        deck.append(new_id)
        dm.cur.execute(f"SELECT card_name, card_level FROM cardsinfo WHERE id = {old_id} AND owned_user = '{a_id}'")
        old = dm.cur.fetchall()[0]
        dm.cur.execute(f"UPDATE playersachivements SET {db_deck} = '{','.join(deck)}' WHERE userid = '{a_id}'")
        dm.db.commit()
        await ctx.send(
            f"You swapped the card **[{u.rarity_cost(old[0])}] {old[0]} lv: {old[1]}** "
            f"with the card **[{u.rarity_cost(new[0])}] {new[0]} lv: {new[1]}** in your deck #{deck_slot}!"
        )

    @commands.hybrid_command(aliases=["adds", "use", "uses"], brief="Add a card to your deck.")
    @checks.is_registered()
    @checks.not_preoccupied()
    async def add(self, ctx: commands.Context, card_id: int):
        """Add a card to your deck."""

        mention = ctx.message.author.mention
        a_id = ctx.message.author.id
        if not card_id:
            await ctx.send(f"{mention}, the correct format is `{u.PREF}add (* card_ids)`!")
            return

        dm.cur.execute(f"SELECT deck_slot FROM playersinfo WHERE userid = '{a_id}'")
        deck_slot = dm.cur.fetchall()[0][0]

        db_deck = f"deck{deck_slot}"
        dm.cur.execute(f"SELECT {db_deck} FROM playersachivements WHERE userid = '{a_id}'")
        deck = dm.cur.fetchall()[0][0].split(",")

        deck = [] if deck == ['0'] else deck
        if str(card_id) in deck:
            await ctx.send(f"{mention}, Card #`{card_id}` is already in your deck.")
            return
        if len(deck) == 12:
            await ctx.send(f"{mention}, your deck's full - do `{u.PREF}swap` instead!")
            return

        dm.cur.execute(
            f"SELECT card_name, card_level FROM cardsinfo WHERE id = {card_id} AND owned_user = '{a_id}'"
        )
        y = dm.cur.fetchall()[0]
        if y:
            res_msg = f"**[{u.rarity_cost(y[0])}] {y[0]} lv: {y[1]}** » Deck #{deck_slot}"
            deck.append(str(card_id))
        else:
            res_msg = f"Card #`{card_id}` doesn't exist in your inventory"

        dm.cur.execute(f"UPDATE playersachivements SET {db_deck} = '{','.join(deck)}' WHERE userid = '{a_id}'")
        dm.db.commit()
        await ctx.send(f"{mention}\n {res_msg}")

    @commands.hybrid_command(aliases=["rem"], brief="Remove a card from your deck.")
    @checks.is_registered()
    @checks.not_preoccupied()
    async def remove(self, ctx: commands.Context, card_id: int):
        """Remove a card from your deck."""

        mention = ctx.message.author.mention
        a_id = ctx.message.author.id
        if not card_id:
            await ctx.send(f"{mention}, the correct format is `{u.PREF}remove (* card_ids)`!")
            return

        dm.cur.execute(f"SELECT deck_slot FROM playersinfo WHERE userid = '{a_id}'")
        deck_slot = dm.cur.fetchall()[0][0]

        db_deck = f"deck{deck_slot}"
        dm.cur.execute(f"SELECT {db_deck} FROM playersachivements WHERE userid = '{a_id}'")
        deck = dm.cur.fetchall()[0][0].split(",")
        deck_length = 0 if deck == ['0'] else len(deck)

        if deck_length == 0:
            await ctx.send(f"{mention}, your deck's empty!")
            return

        if str(card_id) in deck:
            dm.cur.execute(
                f"SELECT card_name, card_level FROM cardsinfo WHERE id = {card_id} AND owned_user = '{a_id}'"
            )
            y = dm.cur.fetchall()[0]
            res_msg = f"**[{u.rarity_cost(y[0])}] {y[0]} lv: {y[1]}** « Deck #{deck_slot}"
            deck.remove(str(card_id))
        else:
            res_msg = f"Card #`{card_id}` isn't in your deck."

        dm.cur.execute(f"UPDATE playersachivements SET {db_deck} = '{','.join(deck)}' WHERE userid = '{a_id}'")
        dm.db.commit()
        await ctx.send(f"{mention}\n {res_msg}")

    @commands.hybrid_command(aliases=["clear_deck", "cleardeck"], brief="Clear your current deck.")
    @checks.is_registered()
    @checks.not_preoccupied("clearing a deck slot")
    async def clear(self, ctx: commands.Context):
        """Clear your current deck."""

        a_id = ctx.message.author.id
        mention = ctx.message.author.mention

        dm.cur.execute(f"SELECT deck_slot FROM playersinfo WHERE userid = {a_id}")
        deck_slot = dm.cur.fetchall()[0][0]

        db_deck = f"deck{deck_slot}"
        dm.cur.execute(f"SELECT {db_deck} FROM playersachivements WHERE userid = {a_id}")
        deck = dm.cur.fetchall()[0][0].split(",")

        if deck == ["0"]:
            await ctx.send(f"{mention}, your deck's already empty!")
            return

        msg = await ctx.send(f"{mention}, do you really want to clear Deck #{deck_slot}?")
        await msg.add_reaction("✅")
        await msg.add_reaction("❎")
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=30.0,
                check=checks.valid_reaction(["❎", "✅"], ctx.message.author, msg)
            )
        except asyncio.TimeoutError:
            await msg.edit(content=f"{mention}, clearing deck cancelled")
            return

        if reaction.emoji == "❎":
            await msg.edit(content=f"{mention}, clearing deck cancelled")
            return

        dm.cur.execute(f"UPDATE playersachivements SET {db_deck} = '0' WHERE userid = {a_id}")
        dm.db.commit()
        await msg.edit(
            content=f"{mention}, your Deck #{deck_slot} has been cleared! \n"
                    f"Do `{u.PREF}add (card_id)` command to add new cards into your deck!"
        )
        await msg.clear_reactions()

    @commands.hybrid_command(aliases=["black", "bj"], brief="Practice your blackjack skills!")
    @checks.not_preoccupied("practicing blackjack")
    async def blackjack(self, ctx):
        """Practice your blackjack skills!"""

        a_id = ctx.message.author.id
        mention = ctx.message.author.mention

        deck = deepcopy(u.DECK)
        aces = deepcopy(u.ACES)
        values = [0, 0]
        cards = [[], []]
        included_aces = [[], []]
        end = False

        def add_card(card, target):
            if target == "self":
                values[0] += deck[card]
                cards[0].append(card)
            else:
                values[1] += deck[card]
                cards[1].append(card)
            del deck[card]

        add_card(random.choice(list(deck)), "self")
        add_card(random.choice(list(deck)), "self")
        add_card(random.choice(list(deck)), "opponent")

        hit = ["hit", "h"]
        stand = ["stand", "s"]
        while not end and values[0] < 21:
            await ctx.send(
                f"{mention} \nYour total: {values[0]} \n{' '.join(cards[0])}"
                f" \n------------------------------ \nDealer's total: {values[1]} + ? \n"
                f"{' '.join(cards[1])} [? ? ?] ```\n{u.PREF}hit -draw a card \n"
                f"{u.PREF}stand -end your turn```"
            )
            try:
                msg_reply = await self.bot.wait_for(
                    "message", timeout=30.0,
                    check=checks.valid_reply(hit + stand, ctx.message.author, ctx.message.channel)
                )
            except asyncio.TimeoutError:
                values = [1000, 1000]
                await ctx.send(f"{mention}, you blanked out and lost the game!")
                return
            else:
                action = msg_reply.content[len(u.PREF):].lower()
                if action in stand:
                    end = True
                    add_card(random.choice(list(deck)), "opponent")
                    while values[1] < 17:
                        add_card(random.choice(list(deck)), "opponent")
                        while values[1] > 21 and any(a in cards[1] and a not in included_aces[1] for a in aces):
                            for x in cards[1]:
                                if x in aces and x not in included_aces[1]:
                                    values[1] -= 10
                                    included_aces[1].append(x)
                                    break

                elif action in hit:
                    add_card(random.choice(list(deck)), "self")
                    while values[0] > 21 and any(a in cards[0] and a not in included_aces[0] for a in aces):
                        for x in cards[0]:
                            if x in aces and x not in included_aces[0]:
                                values[0] -= 10
                                included_aces[0].append(x)
                                break

        if len(cards[1]) == 1 and not values == [1000, 1000]:
            add_card(random.choice(list(deck)), "opponent")

        if values[0] == values[1] and values != [1000, 1000]:
            game_state = "tied"
        elif (values[0] > 21 and values[0] > values[1]) or (values[0] < values[1] < 22):
            game_state = "lost"
        elif (22 > values[0] > values[1]) or (values[1] > 21 and values[0] < values[1]):
            game_state = "won"

        await ctx.send(
            f"{mention}, **You {game_state}!** \nYour total: {values[0]} \n{''.join(cards[0])}"
            f" \n------------------------------ \nDealer's total: {values[1]} \n{''.join(cards[1])}"
        )

    @commands.hybrid_command(brief="Test your reflexes and counting ability!")
    @checks.not_preoccupied("testing timing accuracy")
    async def reaction(self, ctx: commands.Context, wait_time: float = -1.0):
        """Test your reflexes AND counting ability!"""
        mention = ctx.message.author.mention

        if wait_time <= 0:
            wait_time = random.randint(6, 30)

        t = await ctx.send(f"{mention}, reply `{u.PREF}` as close as you can to {wait_time} seconds!")
        try:
            message = await self.bot.wait_for(
                "message", timeout=70,
                check=checks.valid_reply("", ctx.message.author, ctx.message.channel)
            )
        except asyncio.TimeoutError:
            await ctx.send(f"{mention}, time's up!")
        else:
            recorded = (message.created_at - t.created_at).total_seconds()
            off = round(abs(wait_time - recorded) * 1000) / 1000
            await ctx.send(
                f"{mention}, you replied in {recorded} seconds, which "
                f"is {off} seconds off from {wait_time} seconds"
            )

    @commands.hybrid_command(brief="Have Crispy agree with anything!")
    async def agree(self, ctx: commands.Context, statement: str = "but u said u are stupid"):
        """Have Crispy agree with anything!"""
        img = Image.open("resources/img/crispy_reply.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("resources/fonts/whitneysemibold.ttf", 24)
        draw.text((323, 82), statement, (170, 172, 171), font=font)
        with io.BytesIO() as out:
            img.save(out, format="png")
            out.seek(0)
            await ctx.send(file=discord.File(fp=out, filename="crispy_reply.png"))

    @commands.hybrid_command(brief="Mock the bot's creator.")
    async def birb(self, ctx: commands.Context, stuff: str = "1 + 1 = 3"):
        """Mock the bot's creator."""
        img = Image.open("resources/img/birb_logic.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("resources/fonts/whitneysemibold.ttf", 12)
        draw.text((64, 28), stuff, (200, 200, 200), font=font)
        with io.BytesIO() as out:
            img.save(out, format="png")
            out.seek(0)
            await ctx.send(file=discord.File(fp=out, filename="birb_logic.png"))

    @commands.hybrid_command(brief="This is fine.")
    async def dead(self, ctx: commands.Context, msg: str = "Should I be scared?"):
        """Kind of like the 'this is fine' meme, except you can make the dog say whatever you want."""
        img = Image.open("resources/img/pandemic.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("resources/fonts/whitneysemibold.ttf", 14)
        draw.text((62, 290), msg, (200, 200, 200), font=font)
        with io.BytesIO() as out:
            img.save(out, format="png")
            out.seek(0)
            await ctx.send(file=discord.File(fp=out, filename="pandemic.png"))

    @commands.hybrid_command(brief="A adventure themed meme template.")
    async def kick_meme(
            self, ctx: commands.Context,
            kickee: str = "Me duelling someone", kicker: str = "RNG"
    ):
        """A adventurers themed meme generator."""
        img = Image.open("resources/img/meme_template.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("resources/fonts/whitneysemibold.ttf", 17)
        draw.text((80, 25), kickee, (256, 256, 256), font=font)
        draw.text((330, 25), kicker, (256, 256, 256), font=font)
        with io.BytesIO() as out:
            img.save(out, format="png")
            out.seek(0)
            await ctx.send(file=discord.File(fp=out, filename="kick.png"))

    @commands.hybrid_command(aliases=["find_words", "findwords", "fw"], brief="Finds words with given letters.")
    async def find_word(self, ctx: commands.Context, letters: str, limit: int = 5):
        """Finds words with given letters."""
        with open("resources/text/search.txt") as file:
            valid_words = []
            for line in file:
                if limit == 0:
                    break
                if letters in line:
                    valid_words.append(line)
                    limit -= 1

        if valid_words:
            await ctx.send(f"Words found: \n{''.join(valid_words)}")
        else:
            await ctx.send("No words found! :frown:")


async def setup(bot):
    await bot.add_cog(Actions(bot))
