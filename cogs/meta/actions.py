import random
import math
import datetime as dt
import asyncio

import discord
from discord.ext import commands

from helpers import db_manager as dm
from helpers import checks
import util as u


class Actions(commands.cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["d"], brief="Get your daily rewards!")
    @checks.is_registered()
    async def daily(self, ctx: commands.Context):
        """Get your daily rewards!"""
        a = ctx.author
        last_d = dm.get_user_daily(a.id)
        if last_d.date() == dt.date.today():
            dts = u.time_til_midnight()
            await ctx.send(f"{a.mention}, your next daily is in {dts}!")
            return

        streak = dm.get_user_streak(a.id) + 1
        max_streak = 7
        max_tickets = 5
        if dm.has_premium(a.id):
            max_streak = 14
            max_tickets = 10

        if last_d.date() < dt.date.today() - dt.timedelta(days=1):
            streak = 1
        elif streak >= max_streak:
            streak = max_streak

        tickets = dm.get_user_ticket(a.id)
        lvl = dm.get_user_level(a.id)
        if tickets >= max_tickets or lvl < 4:
            ticket_reward = 0
            tick_msg = ""
        else:
            ticket_reward = 1
            tick_msg = f"+{ticket_reward} {u.ICON['tick']}"

        coins = dm.get_user_coin(a.id)
        # Give the user a card or 250 coins, depending on how many they already have
        if dm.get_user_cards_count(a.id) < 500:
            card_level = u.log_level_gen(random.randint(
                2 ** (max(0, 5 - (lvl // 4))),
                2 ** (10 - math.floor(lvl / 10))
            ))
            card = u.random_card(card_level, "normal")
            dm.add_user_cards([(a.id, card, card_level)])
            card_msg = f"Obtained **[{u.rarity_cost(card)}] {card} lv: {card_level}**!"
        else:
            card_val = 250
            coins += card_val
            card_msg = f"Obtained {card_val} {u.ICON['coin']}!"

        xp = dm.get_user_exp(a.id)
        medals = dm.get_user_medal(a.id)
        medal_base = 1 if streak < 7 else 2
        # 1/7 change to get a jackpot daily, with greatly increased rewards
        if jackpot := random.randint(1, 7) == 1:
            coins += (coin_amt := 400 + math.floor(lvl / 5) * 20 + streak * 80)
            xp += (xp_amt := 200)
            medals += (medal_amt := medal_base * 4)
        else:
            coins += (coin_amt := 100 + math.floor(lvl / 5) * 5 + streak * 20)
            xp += (xp_amt := 50)
            medals += (medal_amt := medal_base)

        await ctx.reply(
            f"{'***JACKPOT!!!***' if jackpot else ''}\n"
            f"**+{coin_amt} {u.ICON['coin']} +{xp_amt} {u.ICON['exp']}"
            f" +{medal_amt}{u.ICON['medal']} {tick_msg}\n"
            f"Daily streak {streak}/{max_streak} {u.ICON['streak']}** \n{card_msg}"
        )

        dm.set_user_coin(a.id, coins)
        dm.set_user_exp(a.id, xp)
        dm.set_user_medal(a.id, medals)
        dm.set_user_ticket(a.id, tickets + ticket_reward)
        dm.set_user_daily(a.id, dt.date.today())
        dm.set_user_streak(a.id, streak)

    @commands.hybrid_command(brief="actions")
    @checks.is_registered()
    @checks.not_preoccupied("in the shop")
    @checks.level_check(3)
    async def buy(self, ctx: commands.Context, to_buy: str = None):
        """Command for buying items in the shop"""

        a = ctx.author
        deals = [i.split(".") for i in dm.get_user_deals(a.id).split(',')]
        card_count = dm.get_user_cards_count(a.id)
        coins = dm.get_user_coin(a.id)
        gems = dm.get_user_gem(a.id)
        tokens = dm.get_user_token(a.id)
        tickets = dm.get_user_ticket(a.id)
        user_level = dm.get_user_level(a.id)

        max_tickets = 5 if dm.has_premium(a.id) else 10
        deal_type = None
        deal_msg = None
        info = []  # Info relating to the purchase (depends on type of purchase)

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
        # gem, coin, ticket
        currency_deals = {
            "gc1": [3, 1000, 0],
            "gc2": [6, 2250, 0],
            "gc3": [24, 11000, 0],
            "rt1": [2, 0, 1],
            "rt2": [4, 0, 3],
            "rt3": [6, 0, 5]
        }

        to_buy = to_buy.lower()
        if to_buy in card_packs:
            gem_cost = card_packs[to_buy][0]
            token_cost = card_packs[to_buy][1]
            cards_count = card_packs[to_buy][2]
            cards_level = card_packs[to_buy][3]

            if gems >= gem_cost and tokens >= token_cost:
                if cards_count + card_count > 500:
                    deal_msg = "Purchasing this card pack will exceed the 500 cards capacity for your inventory!"
                else:
                    deal_msg = f"Are you sure you want to purchase a {to_buy.title()} Edition card pack?"
                    deal_type = "Card"
                    info = [gem_cost, token_cost, cards_count, cards_level]
            else:
                if token_cost == 0:
                    deal_msg = f"You need {gem_cost} {u.ICON['gem']} in order to buy a {to_buy.title()} Edition card pack!"
                else:
                    deal_msg = f"You need {token_cost} {u.ICON['token']} in order to buy a {to_buy.title()} Edition card pack!"
        
        elif to_buy in currency_deals:
            gem_cost = currency_deals[to_buy][0]
            coin_gain = currency_deals[to_buy][1]
            ticket_gain = currency_deals[to_buy][2]

            if ticket_gain != 0:
                if gems < gem_cost:
                    deal_msg = f"Not enough gems!"
                elif tickets + ticket_gain > max_tickets:
                    deal_msg = f"You can't buy {ticket_gain} {u.ICON['tick']}, it exceeds the maximum amount of {u.ICON['tick']} you can store!"
                else:
                    deal_type = "Currency"
                    deal_msg = f"Are you sure you want to buy {ticket_gain} {u.ICON['tick']} with {gem_cost} {u.ICON['gem']}?"
                    info = [gem_cost, coin_gain, ticket_gain]
            else:
                if gems < gem_cost:
                    deal_msg = f"Not enough gems!"
                else:
                    deal_type = "Currency"
                    deal_msg = f"Are you sure you want to buy {coin_gain} {u.ICON['coin']} with {gem_cost} {u.ICON['gem']}?"
                    info = [gem_cost, coin_gain, ticket_gain]
        
        elif to_buy in ["refresh", "ref", "re", "r"]:
            if coins < 200:
                deal_msg = f"You need least 200 {u.ICON['coin']} to refresh the shop!"
            else:
                deal_msg = f"Do you want to refresh the shop for 200 {u.ICON['coin']}?"
                deal_type = "Refresh"
        
        elif to_buy == "all":
            total_cost = sum([u.compute_card_cost(i[1], int(i[0])) if i != "-" else 0 for i in deals])
            total_count = sum([1 if i[0] != "-" else 0 for i in deals])

            if total_count + total_count > 500:
                deal_msg = f"Purchasing those cards will exceed the 500 cards capacity for your inventory!"
            elif total_count == 0:
                deal_msg = f"You have already bought every card!"
            elif total_cost > coins:
                deal_msg = f"You need {total_cost} {u.ICON['coin']} to buy all cards in the shop!"
            else:
                deal_msg = f"Do you want to buy all {total_count} card(s) in the shop for {total_cost} {u.ICON['coin']}?"
                deal_type = "All"
        
        elif to_buy.isdigit():
            selection = int(to_buy) - 1
            if not (0 < selection + 1 < len(deals)):
                deal_msg = f"Number must be between 1 and {len(deals)}!"
            elif deals[selection][0] == "-":
                deal_msg = f"You already bought this card!"
            elif card_count + 1 > 500:
                deal_msg = f"You are already at the maximum 500 cards capacity!"
            else:
                card_cost = u.compute_card_cost(deals[selection][1], int(deals[selection][0]))
                if card_cost > coins:
                    deal_msg = f"You don't have enough golden coins to buy that card!"
                else:
                    deal_msg = f"Are you sure you want to purchase **[{u.rarity_cost(deals[selection][1])}] {deals[selection][1]} lv: {deals[selection][0]}**?"
                    deal_type = "Single"

        if deal_type is None and deal_msg is None:
            await ctx.reply(
                "The correct format for this command is "
                f"`{u.PREF}buy (1-{len(deals)}/all/refresh)`!"
            )
            return
        
        deal_msg = await ctx.reply(deal_msg)
        await deal_msg.add_reaction("✅")
        await deal_msg.add_reaction("❎")
        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add", timeout=30.0,
                check=checks.valid_reaction(["❎", "✅"], a, deal_msg)
            )
        except asyncio.TimeoutError:
            await deal_msg.edit(content=f"The transaction timed out.")
            return
        finally:
            await deal_msg.clear_reactions()
        
        if reaction.emoji == "❎":
            await deal_msg.edit(content=f"You cancelled the purchase.")
            return
        
        await deal_msg.delete()

        if deal_type == "Currency":
            dm.set_user_gem(a.id, gems - info[0])
            dm.set_user_coin(a.id, coins + info[1])
            dm.set_user_ticket(a.id, tickets + info[2])
            if info[1] != 0:
                deal_msg = f"**{info[1]}** {u.ICON['coin']}!"
            else:
                deal_msg = f"**{info[2]}** {u.ICON['tick']}!"

            embed = discord.Embed(
                title="You got:",
                description=deal_msg,
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=ctx.author.avatar.url)
            embed.set_footer(text=f"Gems left: {gems - info[0]}")
            await ctx.reply(embed=embed)
        
        elif deal_type == "Card":
            dm.set_user_gem(a.id, gems - info[0])
            dm.set_user_token(a.id, tokens - info[1])
            if info[0] > 0:
                gained_cards = []
                cards_msg = []
                for x in range(info[2]):
                    card_level = u.log_level_gen(random.randint(1, info[3]))
                    card_name = u.random_card(card_level, to_buy)
                    gained_cards.append((a.id, card_name, card_level))
                    cards_msg.append(f"[{u.rarity_cost(card_name)}] **{card_name}** lv: **{card_level}** \n")

                dm.add_user_cards(gained_cards)

                cards_msg.append("=======================\n")
                cards_msg.append(f"**From {to_buy.title()} Edition card pack**")
                embed = discord.Embed(
                    title="You got:",
                    description=" ".join(cards_msg),
                    color=discord.Color.gold()
                )

            elif info[1] > 0:
                dm.add_user_cards([(a.id, "Confetti Cannon", 10)])
                embed = discord.Embed(
                    title=f"**From Anniversary card pack!!**",
                    description="You got\n [Ex/7] Confetti Cannon lv: 10",
                    color=discord.Color.green()
                )

            embed.set_thumbnail(url=ctx.author.avatar.url)
            embed.set_footer(text=f"Gems left: {gems - info[0]}")
            await ctx.send(embed=embed)
        
        elif deal_type == "Refresh":
            gained_cards = []
            for x in range(9 if dm.has_premium(a.id) else 6):
                gained_cards.append(u.add_a_card(user_level))
            dm.set_user_coin(a.id, coins - 200)
            dm.set_user_deals(a.id, ",".join(gained_cards))
            await ctx.reply(f"You refreshed your shop for 200 {u.ICON['coin']}!")
        
        elif deal_type == "All":
            gained_cards = []
            cards_msg = []
            total_cost = sum([u.compute_card_cost(i[1], int(i[0])) if i != "-" else 0 for i in deals])
            for x in deals:
                if x[0] == "-":
                    continue
                gained_cards.append((a.id, x[1], int(x[0])))
                cards_msg.append(
                    f"[{u.rarity_cost(x[1])}] **{x[1]}** lv: **{int(x[0])}** - "
                    f"**{dm.compute_card_cost(x[1], int(x[0]))}** {u.ICON['coin']} \n"
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
            embed.set_thumbnail(url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
        
        elif deal_type == "Single":
            selection = int(to_buy) - 1
            card_cost = u.compute_card_cost(deals[selection][1], int(deals[selection][0]))
            await ctx.reply(
                "You successfully bought a "
                f"**[{u.rarity_cost(deals[selection][1])}] {deals[selection][1]} "
                f"lv: {deals[selection][0]}** with "
                f"{card_cost} {u.ICON['coin']}!"
            )
            dm.add_user_cards([(a.id, deals[selection][1], deals[selection][0])])
            dm.set_user_coin(a.id, coins - card_cost)
            deals[selection][0] = "-"
            dm.set_user_deals(a.id, ",".join([".".join(i[:]) for i in deals]))

    @commands.hybrid_command(brief="Trade with other players!")
    @checks.is_registered()
    @checks.not_preoccupied("trading")
    @checks.level_check(7)
    async def trade(self, ctx: commands.Context, target: discord.Member):
        """Trade with other players!"""
        author = ctx.author
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
                    check=checks.valid_reaction(["❎", "✅"], [target, ctx.author], deal_msg)
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
                            f"{ctx.author}, you can't afford the transaction fee!")
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
                                await ctx.send(f"{ctx.author}, you don't have enough coins for this!")
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
                                    await ctx.send(f"{ctx.author}, you can only put 16 cards at max per trade!")
                                elif card_id in author_cards:
                                    await ctx.send(f"{ctx.author}, you already put this card id in the offer!")
                                    continue
                                elif card_id in decks1:
                                    await ctx.send(
                                        f"{ctx.author}, you can't put a card from your deck into this offer!")
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
                                    f"{ctx.author}, you can't drop more coins than what you have in your offer!")
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
                                await ctx.send(f"{ctx.author}, the card id you want to drop doesn't exist!")
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
                await ctx.send(f"Trade between {ctx.author} and {target} is now finished!")


async def setup(bot):
    await bot.add_cog(Actions(bot))
