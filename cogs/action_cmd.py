import os
import random
import math
import datetime as dt
import asyncio
from copy import deepcopy

from PIL import Image, ImageFont, ImageDraw
import discord
from discord.ext import commands

import tools.cmd_tools as cmd_tools
from tools.cmd_tools import reply_check, reaction_check
import tools.cmd_decorators as cmd_decos
import globals as gv


class ActionsCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, aliases=["d"], brief="actions")
    @commands.check(cmd_decos.is_registered)
    async def daily(self, ctx: commands.Context):
        """Give you your daily dose of rewards!"""
        a_id = ctx.message.author.id
        mention = ctx.message.author.mention
        gv.mycursor.execute(f"select coins, exps, medals, level, daily, streak, user_identity, tickets from playersinfo where userid = {a_id}")
        result = gv.mycursor.fetchall()[0]

        if result[4] == str(dt.date.today()):
            dts = dt.datetime.now()
            await ctx.send(f"{mention}, your next daily is in " +
                           str(cmd_tools.time_converter(((24 - dts.hour - 1) * 60 * 60) +
                                                        ((60 - dts.minute - 1) * 60) + (60 - dts.second))) + "!")
            return

        streak = int(result[5]) + 1
        medal_reward = 1
        ticket_reward = 1
        max_streak = 7
        max_tickets = 5
        card_msg = ""
        tick_msg = ""

        if int(result[6].split(",")[0]) == 1:
            max_streak = 14
            max_tickets = 10
        if result[4] != str(dt.date.today() - dt.timedelta(days=1)):
            streak = 1
        elif streak >= max_streak:
            streak = max_streak
        if streak >= 7:
            medal_reward = 2
        if result[7] >= max_tickets or result[3] < 4:
            ticket_reward = 0
        else:
            tick_msg = f"+{ticket_reward} {gv.icon['tick']}"

        gv.mycursor.execute(f"select id from cardsinfo where owned_user = {a_id}")
        cards_count = len(gv.mycursor.fetchall())

        if cards_count < 500:
            card_level = cmd_tools.log_level_gen(random.randint(2 ** (max(0, 5 - (result[3] // 4))),
                                                                2 ** (10 - math.floor(result[3] / 10))))
            card = cmd_tools.random_card(card_level, "normal")
            sql = "insert into cardsinfo (owned_user, card_name, card_level) values (%s, %s, %s)"
            val = (str(a_id), card, card_level)
            gv.mycursor.execute(sql, val)
            gv.mydb.commit()
            card_msg = f"Obtained **[{cmd_tools.rarity_cost(card)}] {card} lv: {card_level}**!"
        else:
            gv.mycursor.execute(
                f"update playersinfo set coins = coins + 250 where userid = '{a_id}'")
            gv.mydb.commit()
            card_msg = f"Received extra 250 {gv.icon['coin']}!"

        if random.randint(1, 7) == 1:  # one in 7 change ig
            new_coins = result[0] + 400 + math.floor(result[3] / 5) * 20 + streak * 80
            new_exps = result[1] + 200
            new_medals = result[2] + medal_reward * 4
            await ctx.send(f"{mention} JACKPOT!!! \n"
                           f"**+{math.floor(result[3] / 5) * 20 + 400 + streak * 80} "
                           f"{gv.icon['coin']} +200 {gv.icon['exp']}"
                           f" +{medal_reward * 4} {gv.icon['medal']} {tick_msg}! \n"
                           f"Daily streak {streak}/{max_streak} {gv.icon['streak']}** \n{card_msg}")
        else:
            new_coins = result[0] + 100 + math.floor(result[3] / 5) * 5 + streak * 20
            new_exps = result[1] + 50
            new_medals = result[2] + medal_reward
            await ctx.send(f"{mention} \n"
                           f"**+{math.floor(result[3] / 5) * 5 + 100 + streak * 20} {gv.icon['coin']} +50 {gv.icon['exp']}"
                           f" +{medal_reward}{gv.icon['medal']} {tick_msg}\n"
                           f"Daily streak {streak}/{max_streak} {gv.icon['streak']}** \n{card_msg}")
        sql = f"update playersinfo set coins = %s, exps = %s, medals = %s, tickets = tickets + %s, daily = %s, streak = %s where userid = %s"
        value = (new_coins, new_exps, new_medals, ticket_reward, str(dt.date.today()), streak, a_id)
        gv.mycursor.execute(sql, value)
        gv.mydb.commit()

    @commands.command(pass_context=True, aliases=["orders"], brief="cards")
    @commands.check(cmd_decos.is_registered)
    async def order(self, ctx: commands.Context, card_property=None, the_order=None):
        """Command formatting for the card display order"""

        a_id = ctx.message.author.id
        mention = ctx.message.author.mention
        level_aliases = ["level", "levels", "card_level", "card_levels", "l"]
        id_aliases = ["id", "ids", "i"]
        name_aliases = ["name", "names", "card_name", "card_names", "n", "nam"]
        cost_aliases = ["energy_cost", "energycost", "energy", "cost", "ec", "en", "co", "e", "c"]
        rarity_aliases = ["rarity", "rare", "ra", "r"]
        ascending_aliases = ["ascending", "ascend", "a", "asc"]
        descending_aliases = ["descending", "descend", "d", "desc", "des"]
        order = [0, None, None]
        if card_property is None or the_order is None:
            await ctx.send(f"{mention}, the correct format for this command is "
                           f"`{gv.prefix}order (level/name/id/cost/rarity) (ascending/descending)`!")
        else:
            if the_order in ascending_aliases + descending_aliases:
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
            if the_order in descending_aliases:
                order[0] += 1
                order[2] = " descending"
            if the_order == [0, None, None]:
                await ctx.send(f"{mention}, the correct format for this command is "
                               f"`{gv.prefix}order (level/name/id/cost/rarity) (ascending/descending)`!")
            else:
                gv.mycursor.execute(f"update playersinfo set inventory_order = {order[0]} where userid = {a_id}")
                gv.mydb.commit()
                await ctx.send(f"{mention}, the order had been set to {order[1]}/{order[2]}.")

    @commands.command(pass_context=True, aliases=["buying"], brief="actions")
    @commands.check(cmd_decos.is_registered)
    @commands.check(cmd_decos.not_preoccupied)
    @cmd_decos.check_level(3)
    async def buy(self, ctx: commands.Context, to_buy=None):
        """Command for buying items in the shop"""

        a_id = ctx.message.author.id
        mention = ctx.message.author.mention
        gv.mycursor.execute("select deals from playersinfo where userid = " + str(a_id))
        deals = gv.mycursor.fetchall()[0][0].split(',')

        if to_buy is None:
            await ctx.send(f"{mention}, the correct format for this command is "
                           f"`{gv.prefix}buy (1-{len(deals)}/all/refresh)`!")
            return

        gv.queues[str(a_id)] = "deciding to purchase something in the shop"

        gv.mycursor.execute(f"select count(*) from cardsinfo where owned_user = {a_id}")
        cards_count = gv.mycursor.fetchall()[0][0]

        gv.mycursor.execute(f"select coins, gems, event_token, tickets, user_identity, level from playersinfo where userid = '{a_id}'")
        coins, gems, tokens, tickets, user_identity, player_lvl = gv.mycursor.fetchall()[0]
        max_tickets = 5 if user_identity.split(",")[0] != "1" else 10

        if not to_buy.isdigit():
            # well, maybe the user wants to do some other action?
            other_action_taken = True
            deal_started = "None"
            deal_msg = "None"
            deal_transaction = [0, 'coins', 0, 'coin']
            deal_cards = [0, 0, 'basic', 0, 128]

            def currency_buy(command, gem_cost, reward_currency, reward_amount):
                if to_buy.lower() == command:
                    if gems >= gem_cost:
                        if reward_currency != "tick" or (reward_currency == "tick" and tickets + reward_amount <= max_tickets):
                            deal_started = "currency"
                            deal_transaction = [gem_cost, {'coin': 'coins', 'tick': 'tickets', 'token': 'event_token'}[reward_currency], reward_amount, reward_currency]
                            return f"Are you sure you want to buy {reward_amount} {gv.icon[reward_currency]} with {gem_cost} {gv.icon['gem']}?", deal_started, deal_transaction
                        else:
                            return f"You can't buy {reward_amount} {gv.icon[reward_currency]}, it exceeds the maximum amount of {gv.icon['tick']} you can store!", "None", [0, 'coins', 0, 'coin']
                    else:
                        return f"You need least {gem_cost} {gv.icon['gem']} to buy {reward_amount} {gv.icon[reward_currency]}!", "None", [0, 'coins', 0, 'coin']
                return "None", "None", [0, 'coins', 0, 'coin']

            def card_buy(command, gem_cost, token_cost, cards, levels):
                if to_buy.lower() == command:
                    if gems >= gem_cost and tokens >= token_cost:
                        if cards_count + cards > 500:
                            return "you can only have at most 500 cards!", "None", [0, 0, 'basic', 0, 128]
                        else:
                            return f"Are you sure you want to purchase a {command.title()} Edition card pack?", "card", [gem_cost, token_cost, command, cards, levels]
                    else:
                        if token_cost == 0:
                            return f"You need {gem_cost} {gv.icon['gem']} in order to buy a {command.title()} Edition card pack!", "None", [0, 0, 'basic', 0, 128]
                        else:
                            return f"You need {token_cost} {gv.icon['token']} in order to buy a {command.title()} Edition card pack!", "None", [0, 0, 'basic', 0, 128]
                return "None", "None", [0, 0, 'basic', 0, 128]

            if to_buy.lower() in ["refresh", "ref", "re", "r"]:
                if coins >= 200:
                    msg = await ctx.send(f"{mention}, do you want to refresh the shop for 200 {gv.icon['coin']}?")
                    await msg.add_reaction(emoji='✅')
                    await msg.add_reaction(emoji='❎')
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0,
                                                                 check=reaction_check(['❎', '✅'],
                                                                                      [ctx.message.author], [msg]))
                    except asyncio.TimeoutError:
                        await msg.edit(content=f"{mention}, purchase cancelled")
                        await msg.clear_reactions()
                    else:
                        if reaction.emoji == '❎':
                            await msg.edit(content=f"{mention}, purchase cancelled")
                            await msg.clear_reactions()
                        else:
                            await msg.delete()
                            deals_cards = []
                            if int(user_identity.split(",")[0]) == 0:
                                for x in range(6):
                                    deals_cards.append(
                                        cmd_tools.add_a_card(player_lvl, str(a_id)))
                            elif int(user_identity.split(",")[0]) == 1:
                                for x in range(9):
                                    deals_cards.append(cmd_tools.add_a_card(player_lvl, str(a_id)))
                            sql = "update playersinfo set deals = %s, coins = coins - 200 where userid = %s"
                            value = (",".join(deals_cards), str(a_id))
                            gv.mycursor.execute(sql, value)
                            gv.mydb.commit()
                            await ctx.send(f"{mention}, you refreshed your shop for 200 {gv.icon['coin']}!")
                else:
                    await ctx.send(f"{mention}, you need least 200 {gv.icon['coin']} to refresh the shop!")

            card_packs = [
                ['basic', 3, 0, 3, 128],
                ['fire', 5, 0, 4, 128],
                ['evil', 5, 0, 4, 128],
                ['electric', 5, 0, 4, 128],
                ['defensive', 5, 0, 4, 128],
                ['pro', 24, 0, 6, 16],
                ['pro', 24, 0, 6, 16],
                # ['confetti', 0, 40, 6, 16]
            ]

            for p in card_packs:
                if deal_msg == 'None':
                    deal_msg, deal_started, deal_cards = card_buy(*p)

            currency_deals = [
                ["gc1", 3, 'coin', 1000],
                ['gc2', 6, 'coin', 2250],
                ['gc3', 24, 'coin', 11000],
                ['rt1', 2, 'tick', 1],
                ['rt2', 4, 'tick', 3],
                ['rt3', 6, 'tick', 5]
            ]

            for c in currency_deals:
                if deal_msg == 'None':
                    deal_msg, deal_started, deal_transaction = currency_buy(*c)

            if deal_msg != "None":
                deal_msg = await ctx.send(deal_msg)

            if deal_started != "None":
                await deal_msg.add_reaction(emoji='✅')
                await deal_msg.add_reaction(emoji='❎')
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0,
                                                             check=reaction_check(['❎', '✅'],
                                                                                  [ctx.message.author], [deal_msg]))
                except asyncio.TimeoutError:
                    await deal_msg.edit(content=f"{mention}, the transaction timed out.")
                    await deal_msg.clear_reactions()
                else:
                    if reaction.emoji == '❎':
                        await deal_msg.edit(content=f"{mention}, you cancelled the purchase.")
                        await deal_msg.clear_reactions()
                    else:
                        await deal_msg.delete()
                        if deal_started == "currency":
                            gv.mycursor.execute(f"update playersinfo set gems = gems - {deal_transaction[0]}, "
                                                f"{deal_transaction[1]} = {deal_transaction[1]} + {deal_transaction[2]} "
                                                f"where userid = {a_id}")
                            gv.mydb.commit()
                            embed = discord.Embed(title="You got:",
                                                  description=f"**{deal_transaction[2]}** {gv.icon[deal_transaction[3]]}!",
                                                  color=discord.Color.gold())
                            embed.set_thumbnail(url=ctx.message.author.avatar_url)
                            embed.set_footer(text="Gems left: " + str(gems - deal_transaction[0]))
                            await ctx.send(embed=embed)

                        elif deal_started == "card":
                            gv.mycursor.execute(f"update playersinfo set gems = gems - {deal_cards[0]}, "
                                                f"event_token = event_token - {deal_cards[1]} where userid = {a_id}")
                            gv.mydb.commit()
                            if deal_cards[0] > 0:
                                deals_cards = []
                                for x in range(deal_cards[3]):
                                    energy_cost = cmd_tools.log_level_gen(random.randint(1, deal_cards[4]))
                                    deals_cards.append(energy_cost)
                                    deals_cards.append(cmd_tools.random_card(energy_cost, deal_cards[2]))

                                sql = "insert into cardsinfo (owned_user, card_name, card_level) values (%s, %s, %s)"
                                val = [(str(a_id), deals_cards[i * 2 + 1], deals_cards[i * 2]) for i in range(deal_cards[3])]

                                gv.mycursor.executemany(sql, val)
                                gv.mydb.commit()
                                all_cards = []
                                for x in range(deal_cards[3]):
                                    all_cards.append(f"[{cmd_tools.rarity_cost(deals_cards[x * 2 + 1])}] **{deals_cards[x * 2 + 1]}** lv: **{deals_cards[x * 2]}** \n")

                                all_cards.append("=======================\n")
                                all_cards.append(f"**From {deal_cards[2].title()} Edition card pack**")
                                embed = discord.Embed(title="You got:", description=" ".join(all_cards), color=discord.Color.gold())

                            elif deal_cards[1] > 0:
                                sql = "insert into cardsinfo (owned_user, card_name, card_level) values (%s, %s, %s)"
                                val = (str(a_id), "Confetti Cannon", 10)
                                gv.mycursor.execute(sql, val)
                                gv.mydb.commit()
                                embed = discord.Embed(
                                    title=f"**From {deal_cards[2].title()} Anniversary card pack!!**",
                                    description="You got\n [Ex/7] Confetti Cannon lv: 10",
                                    color=discord.Color.green())

                            embed.set_thumbnail(url=ctx.message.author.avatar_url)
                            embed.set_footer(text="Gems left: " + str(gems - deal_cards[0]))
                            await ctx.send(embed=embed)

            elif to_buy.lower() == "all":
                total_cost = 0
                total_energy = []
                for x in deals:
                    if x[0] != "-":
                        total_energy.insert(len(total_energy), int(x.split(".")[0]))
                    else:
                        total_energy.insert(len(total_energy), 0)
                for x in range(len(total_energy)):
                    if not total_energy[x] == 0:
                        total_cost += round(1.6 ** total_energy[x] * 50 *
                                            cmd_tools.price_factor(deals[x][len(str(total_energy[x])):]))

                if sum([1 if not i == 0 else 0 for i in total_energy]) + cards_count > 500:
                    await ctx.send(f"{mention}, you can't have more than 500 cards!")

                elif total_cost > 0:
                    if total_cost > coins:
                        await ctx.send(f"{mention}, you need {total_cost} {gv.icon['coin']} to buy all cards in the shop!")
                    else:
                        await ctx.send(f"{mention}, type `{gv.prefix}deals confirm` to buy all the cards for {total_cost} {gv.icon['coin']}.")

                        try:
                            message = await self.bot.wait_for("message", timeout=15.0,
                                                              check=reply_check(['deals confirm'],
                                                                                [ctx.message.author], [ctx.message.channel]))
                        except asyncio.TimeoutError:
                            await ctx.send(f"{mention}, deals cancelled")

                        else:
                            y = 0
                            cards_bought = []

                            for x in deals:
                                if total_energy[y] != 0:
                                    sql = "insert into cardsinfo (owned_user, card_name, card_level) values (%s, %s, %s)"
                                    val = (str(a_id), x.split(".")[1], total_energy[y])
                                    gv.mycursor.execute(sql, val)
                                    cards_bought.append(f"[{cmd_tools.rarity_cost(x.split('.')[1])}] **{x.split('.')[1]}** lv: **{total_energy[y]}** - "
                                                        f"**{round(1.6 ** total_energy[y] * 50 * cmd_tools.price_factor(x.split('.')[1]))}** {gv.icon['coin']} \n")
                                    gv.mydb.commit()
                                    deals[y] = "-" + x
                                y += 1

                            sql = "update playersinfo set coins = %s, deals = %s where userid = %s"
                            value = (coins - total_cost, ",".join(deals), str(a_id))
                            gv.mycursor.execute(sql, value)
                            gv.mydb.commit()

                            cards_bought.append("=======================\n")
                            cards_bought.append(f"**Total Cost - {total_cost} {gv.icon['coin']}**")
                            embed = discord.Embed(title="You Bought:",
                                                  description=" ".join(cards_bought),
                                                  color=discord.Color.gold())
                            embed.set_footer(text=f"You currently have {coins - total_cost} golden coins left")
                            embed.set_thumbnail(url=ctx.message.author.avatar_url)
                            await ctx.send(embed=embed)
                else:
                    await ctx.send(f"{mention}, you have already bought every card!")
        else:
            other_action_taken = False
            to_buy = int(to_buy)

        if not other_action_taken and 0 < to_buy <= len(deals):
            if deals[to_buy - 1][0] == "-":
                await ctx.send(f"{mention}, you already bought this card!")
            else:
                card_energy_cost = int(deals[to_buy - 1].split(".")[0])
                card = deals[to_buy - 1].split(".")[1]
                if round(1.6 ** card_energy_cost * 50 * cmd_tools.price_factor(card)) > coins:
                    await ctx.send(f"{mention}, you don't have enough golden coins to buy that card!")
                elif cards_count + 1 > 500:
                    await ctx.send(f"{mention}, you can't have more than 500 cards!")
                else:
                    msg = await ctx.send(
                        f"{mention}, are you sure you want to purchase **[{cmd_tools.rarity_cost(card)}] {card} lv: {card_energy_cost}**?")
                    await msg.add_reaction(emoji='✅')
                    await msg.add_reaction(emoji='❎')
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0,
                                                                 check=reaction_check(['❎', '✅'], [ctx.message.author], [msg]))
                    except asyncio.TimeoutError:
                        await msg.edit(content=f"{mention}, purchase cancelled")
                    else:
                        if reaction.emoji == '❎':
                            await msg.edit(content=f"{mention}, purchase cancelled")
                        else:
                            sql = "insert into cardsinfo (owned_user, card_name, card_level) values (%s, %s, %s)"
                            val = (str(a_id), card, card_energy_cost)
                            gv.mycursor.execute(sql, val)
                            gv.mydb.commit()
                            await msg.edit(
                                content=f"{mention}, you successfully bought a **[{cmd_tools.rarity_cost(card)}] {card} "
                                        f"lv: {card_energy_cost}** with "
                                        f"{round(1.6 ** card_energy_cost * 50 * cmd_tools.price_factor(card))} {gv.icon['coin']}!")
                            deals[to_buy - 1] = "-" + deals[to_buy - 1]
                            sql = "update playersinfo set coins = coins - %s, deals = %s where userid = %s"
                            value = (round(1.6 ** card_energy_cost * 50 * cmd_tools.price_factor(card)),
                                     ",".join(deals), str(a_id))
                            gv.mycursor.execute(sql, value)
                            gv.mydb.commit()
                    await msg.clear_reactions()
        else:
            try:
                if (to_buy.lower() not in ["all", "basic", "fire", "evil", "electric",
                                           "defensive", "pro", "gc1", "gc2", "gc3", "rt1",
                                           "rt2", "rt3", "refresh", "ref", "re", "r", "confetti"]):
                    await ctx.send(f"{mention}, the correct format for this command is `{gv.prefix}buy (1-{len(deals)}/all/refresh)`!")
            except:
                await ctx.send(f"{mention}, the correct format for this command is `{gv.prefix}buy (1-{len(deals)}/all/refresh)`!")
        del gv.queues[str(a_id)]

    # await ctx.send(f"{mention}, shop is currently temporarily disabled!")

    @commands.command(pass_context=True, aliases=["dis"], brief="cards")
    @commands.check(cmd_decos.is_registered)
    @commands.check(cmd_decos.not_preoccupied)
    async def discard(self, ctx: commands.Context, *card_id):
        """Remove the existences of the unwanted cards"""

        a_id = ctx.message.author.id
        mention = ctx.message.author.mention
        if not card_id:
            await ctx.send(f"{mention}, the correct format is `{gv.prefix}discard (* card_ids)`!")
            return

        gv.mycursor.execute(f"select deck1,deck2,deck3,deck4,deck5,deck6 from playersachivements where userid = '{a_id}'")
        decks = [int(k) for i in gv.mycursor.fetchall()[0] for k in i.split(",")]
        card_ids = list(card_id)
        final_msg = []

        for x in card_ids:
            try:
                gv.mycursor.execute(f"select card_name, card_level from cardsinfo where id = {x} and owned_user = '{a_id}'")
                y = gv.mycursor.fetchall()[0]
                if not y:
                    final_msg.append(f"You don't have a card with id `{x}`!")
                if str(x) in decks:
                    final_msg.append(f"Id `{x}` is equipped in your deck")
                else:
                    final_msg.append(f"**[{cmd_tools.rarity_cost(y[0])}] {y[0]} lv: {y[1]}** Id `{x}`")
            except:
                final_msg.append(f"`{x}` isn't a valid card id")

        gv.queues[str(a_id)] = "discarding cards"
        msg = await ctx.send(f"{mention}, are you sure you want to discard: \n"
                             " \n".join(final_msg) + "\n"
                                                     f"{gv.icon['bers']} *(Discarded cards can't be retrieved!)*")

        await msg.add_reaction(emoji='✅')
        await msg.add_reaction(emoji='❎')
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0,
                                                     check=reaction_check(['❎', '✅'], [ctx.message.author], [msg]))
        except asyncio.TimeoutError:
            await msg.edit(content=f"{mention}, discarding cancelled")
            await msg.clear_reactions()
            del gv.queues[str(a_id)]
            return

        if reaction.emoji == '❎':
            await msg.edit(content=f"{mention}, discarding cancelled")
            await msg.clear_reactions()
            del gv.queues[str(a_id)]
            return

        for x in card_ids:
            try:
                gv.mycursor.execute(
                    f"select card_name, card_level from cardsinfo where id = {x} and owned_user = '{a_id}'")
                y = gv.mycursor.fetchall()[0]
                if not y:
                    continue
                if str(x) in decks:
                    continue
                else:
                    gv.mycursor.execute(f"delete from cardsinfo where id = {x}")
            except:
                continue

        gv.mydb.commit()
        del gv.queues[str(a_id)]

        await msg.edit(content=f"{mention}, card(s) discarded successfully!")

    @commands.command(pass_context=True, aliases=["mer"], brief="cards")
    @commands.check(cmd_decos.is_registered)
    @commands.check(cmd_decos.not_preoccupied)
    async def merge(self, ctx: commands.Context, card1_id: str = "bruh moment", card2_id: str = "bruh moment"):
        """Upgrade a card to next level with two cards"""

        a_id = ctx.message.author.id
        mention = ctx.message.author.mention
        if card1_id is None or card2_id is None:
            await ctx.send(f"{mention}, the correct format for this command is `{gv.prefix}merge (primary_card_id) (supplementary_card_id)`!")
            return

        gv.mycursor.execute(
            f"select deck1,deck2,deck3,deck4,deck5,deck6 from playersachivements where userid = '{a_id}'")
        decks = [int(k) for i in gv.mycursor.fetchall()[0] for k in i.split(",")]

        if not card1_id.isnumeric() or not card2_id.isnumeric():
            await ctx.send(f"{mention}, you've given an invalid card id!")
            return

        card1_id, card2_id = int(card1_id), int(card2_id)
        gv.mycursor.execute(f"select card_name, card_level, owned_user from cardsinfo where id = {card1_id}")
        card1 = gv.mycursor.fetchall()[0]
        if not card1:
            await ctx.send(f"{mention}, you don't have the first card!")
            return

        gv.mycursor.execute(f"select card_name, card_level, owned_user from cardsinfo where id = {card2_id}")
        card2 = gv.mycursor.fetchall()[0]
        if not card2:
            await ctx.send(f"{mention}, you don't have the second card!")
            return

        if card1[2] != str(a_id) or card2[2] != str(a_id):
            await ctx.send(f"{mention}, you have to own both cards!")
            return

        if card1[1] != card2[1] or \
                cmd_tools.cards_dict(1, card1[0])["rarity"] != cmd_tools.cards_dict(1, card2[0])["rarity"]:
            await ctx.send(f"{mention}, both cards need to be the same level and rarity!")
            return

        if card1[1] >= 15:
            await ctx.send(f"{mention}, the card to merge is maxed out!")
            return

        if card2_id in decks:
            await ctx.send(f"{mention}, the sacrificial card you chose "
                           "is currently in one of your deck slots- \n"
                           f"`{gv.prefix}remove (* card_ids)` first before you merge it away!")
            return

        gv.mycursor.execute("select * from playersinfo where userid = " + str(a_id))
        player_info = gv.mycursor.fetchall()

        merge_cost = math.floor(((card1[1] + 1) ** 2) * 10)
        if player_info[0][5] < merge_cost:
            await ctx.send(f"{mention} You don't have enough coins ({merge_cost} coins) to complete this merge!")
            return

        gv.queues[str(a_id)] = "trying to merge cards"
        msg = await ctx.send(f"{mention}, \n"
                             f"**[{cmd_tools.rarity_cost(card1[0])}] {card1[0]} lv: {card1[1]}**\n"
                             f"**[{cmd_tools.rarity_cost(card2[0])}] {card2[0]} lv: {card2[1]}**\n"
                             f"merging cost {merge_cost} {gv.icon['coin']}.")
        await msg.add_reaction(emoji='✅')
        await msg.add_reaction(emoji='❎')
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0,
                                                     check=reaction_check(['❎', '✅'], [ctx.message.author], [msg]))
        except asyncio.TimeoutError:
            await msg.edit(content=f"{mention}, merging timed out")
            await msg.clear_reactions()
        else:
            if reaction.emoji == '❎':
                await msg.edit(content=f"{mention}, merging timed out")
                await msg.clear_reactions()
            else:
                await msg.delete()
                cmd_tools.log_quest(7, 1, a_id)
                sql = "update playersinfo set coins = coins - %s, exps = exps + %s where userid = %s"
                value = (math.floor(((card1[1] + 1) ** 2) * 10), (card1[1] + 1) * 10, a_id)
                gv.mycursor.execute(sql, value)
                gv.mycursor.execute("delete from cardsinfo where id = {}".format(card2_id))
                gv.mycursor.execute(
                    "update cardsinfo set card_level = card_level + 1 where id = {}".format(card1_id))
                gv.mydb.commit()
                embed = discord.Embed(title="Cards merged successfully!",
                                      description=f"-{math.floor(((card1[1] + 1) ** 2) * 10)} {gv.icon['coin']} +{(card1[1] + 1) * 10} {gv.icon['exp']}",
                                      color=discord.Color.green())
                embed.add_field(
                    name=f"You got a [{cmd_tools.rarity_cost(card1[0])}] {card1[0]} lv: {card1[1] + 1} from:",
                    value=f"[{cmd_tools.rarity_cost(card1[0])}] {card1[0]} lv: {card1[1]} \n" + \
                          f"[{cmd_tools.rarity_cost(card2[0])}] {card2[0]} lv: {card2[1]}")
                embed.set_thumbnail(url=ctx.message.author.avatar_url)
                await ctx.send(embed=embed)
        del gv.queues[str(a_id)]

    @commands.command(pass_context=True, aliases=["trades"], brief="actions")
    @commands.check(cmd_decos.is_registered)
    @commands.check(cmd_decos.not_preoccupied)
    @cmd_decos.check_level(7)
    async def trade(self, ctx: commands.Context, target=None):
        """Trade with other players for gold and cards"""
        target_info = []
        target = cmd_tools.get_user(target, ctx.message)
        author = ctx.message.author
        mention = author.mention
        a_id = author.id
        gv.mycursor.execute(f"select level, coins from playersinfo where userid = '{target.id}'")
        target_info = gv.mycursor.fetchall()

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

        gv.queues[str(author.id)] = "offering a trade"
        trade_end = False
        confirmed = [False, False]

        deal_msg = await ctx.send(f"{target.mention}. Accept a trade with {mention}?")
        await deal_msg.add_reaction(emoji='✅')
        await deal_msg.add_reaction(emoji='❎')

        while not trade_end:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=reaction_check(['❎', '✅'], [target, ctx.message.author], [deal_msg]))
            except asyncio.TimeoutError:
                await deal_msg.edit(content=f"{mention}, trade cancelled due to afk {gv.icon['dead']}")
                await deal_msg.clear_reactions()
                del gv.queues[str(author.id)]
                return

            if reaction.emoji == '❎':
                await deal_msg.edit(content=f"{mention}, trade cancelled! :weary:")
                await deal_msg.clear_reactions()
                del gv.queues[str(author.id)]
                return

            if reaction.emoji == '✅' and user == target:
                break

        if str(target.id) in gv.queues:
            await deal_msg.edit(content=f"{mention}, trade cancelled! The target user is currently {gv.queues[str(target.id)]}!")
            await deal_msg.clear_reactions()
            del gv.queues[str(author.id)]
            return

        gv.mycursor.execute(f"select deck1,deck2,deck3,deck4,deck5,deck6 from playersachivements where userid = '{target.id}'")
        decks1 = [int(k) for i in gv.mycursor.fetchall()[0] for k in i.split(",")]
        gv.mycursor.execute(f"select deck1,deck2,deck3,deck4,deck5,deck6 from playersachivements where userid = '{author.id}'")
        decks2 = [int(k) for i in gv.mycursor.fetchall()[0] for k in i.split(",")]
        gv.mycursor.execute(f"select level, coins from playersinfo where userid = '{author.id}'")
        author_info = gv.mycursor.fetchall()[0]
        gv.queues[str(author.id)] = "currently trading"
        gv.queues[str(target.id)] = "currently trading"
        author_coins = 0
        target_coins = 0
        author_cards = {}
        target_cards = {}

        def tax():
            return max(round(author_coins * 0.1) + 150 * len(author_cards),
                       round(target_coins * 0.1) + 150 * len(target_cards))

        def offer():
            embed = discord.Embed(title=f"Trade ongoing!",
                                  description=f"`{gv.prefix}(put/drop) (coin/card) (amount/card_id)` \n"
                                              f"`{gv.prefix}(confirm/exit/refresh)` \n"
                                              f"16 cards at max per side per trade",
                                  color=discord.Color.gold())
            author_offer = []
            target_offer = []
            for c in author_cards:
                author_offer.append(f"[{cmd_tools.rarity_cost(author_cards[c][0])}] {author_cards[c][0]}, "
                                    f"lv: {author_cards[c][1]}, id: {c} ")
            for c in target_cards:
                target_offer.append(f"[{cmd_tools.rarity_cost(target_cards[c][0])}] {target_cards[c][0]}, "
                                    f"lv: {target_cards[c][1]}, id: {c} ")

            if confirmed[0]:
                embed.add_field(name=f"{author}: :white_check_mark:",
                                value=f"```Golden Coins: {author_coins} \n" + "\n".join(author_offer) + "```",
                                inline=False)
            else:
                embed.add_field(name=f"{author}:",
                                value=f"```Golden Coins: {author_coins} \n" + "\n".join(author_offer) + "```",
                                inline=False)
            if confirmed[1]:
                embed.add_field(name=f"{target}: :white_check_mark:",
                                value=f"```Golden Coins: {target_coins} \n" + "\n".join(target_offer) + "```",
                                inline=False)
            else:
                embed.add_field(name=f"{target}:",
                                value=f"```Golden Coins: {target_coins} \n" + "\n".join(target_offer) + "```",
                                inline=False)

            embed.set_footer(text=f"Transaction fee: {tax()}")
            return embed

        trade_msg = await ctx.send(embed=offer())

        while not trade_end:
            try:
                reply_msg = await self.bot.wait_for("message", timeout=120.0,
                                                    check=reply_check([''], [target, author], [ctx.message.channel]))
            except asyncio.TimeoutError:
                await ctx.send(f"Well, no one showed up to the trade, so it was called off.")
                return

            reply_author = reply_msg.author
            reply_msg = [s.lower() for s in reply_msg.content[len(gv.prefix):].split(" ")]
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

            if len(reply_msg) < 3 and reply_msg[0] != 'confirm':
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
                        gv.mycursor.execute(f"select card_name, card_level from cardsinfo where id = {card_id} and owned_user = '{reply_author.id}'")
                        result = gv.mycursor.fetchall()[0]
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
                                    await ctx.send(f"{ctx.message.author}, you can't put a card from your deck into this offer!")
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
                                await ctx.send(f"{ctx.message.author}, you can't drop more coins than what you have in your offer!")
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
                gv.mycursor.execute(f"update playersinfo set coins = coins + {target_coins} - {author_coins} - {tax()} where userid = '{author.id}'")
                gv.mycursor.execute(f"update playersinfo set coins = coins + {author_coins} - {target_coins} - {tax()} where userid = '{target.id}'")
                for card in author_cards:
                    gv.mycursor.execute(f"update cardsinfo set owned_user = '{target.id}' where id = {card}")
                for card in target_cards:
                    gv.mycursor.execute(f"update cardsinfo set owned_user = '{author.id}' where id = {card}")
                gv.mydb.commit()
                trade_end = True
                await ctx.send(f"Trade between {ctx.message.author} and {target} is now finished!")

        del gv.queues[str(author.id)]
        del gv.queues[str(target.id)]

    @commands.command(pass_context=True, aliases=["selects", "select_deck", "selectdeck", "sel", "se"], brief="cards")
    @commands.check(cmd_decos.is_registered)
    async def select(self, ctx: commands.Context, deck_slot="bruh moment"):
        """Select a deck from your deck slots"""

        a_id = ctx.message.author.id
        if not deck_slot.isdecimal():
            await ctx.send(f"The correct format for this is `{gv.prefix}select (#deck_slot)`!")
            return
        else:
            deck_slot = int(deck_slot)
            if not 1 <= deck_slot <= 6:
                await ctx.send("The deck slot number must between 1-6!")
                return

        gv.mycursor.execute("select level from playersinfo where userid = " + str(a_id))
        level = gv.mycursor.fetchall()[0][0]
        deck_slots = {1: 0, 2: 0, 3: 6, 4: 15, 5: 21, 6: 29}

        if level < deck_slots[deck_slot]:
            await ctx.send(f"Deck #{deck_slot} is unlocked at {deck_slots[deck_slot]}!")
            return

        gv.mycursor.execute(f"update playersinfo set deck_slot = {deck_slot} where userid = {a_id}")
        gv.mydb.commit()
        await ctx.send(f"Deck #{deck_slot} is now selected!")

    @commands.command(pass_context=True, aliases=["paste", "past", "pas", "paste_deck"], brief="cards")
    @commands.check(cmd_decos.is_registered)
    async def pasta(self, ctx: commands.Context, deck_slot="bruh moment"):
        """Returns the card ids of your current selected deck"""

        a_id = ctx.message.author.id
        if deck_slot is None:
            gv.mycursor.execute(f"select deck_slot from playersinfo where userid = {a_id}")
            deck_slot = gv.mycursor.fetchall()[0][0]

        if not deck_slot.isnumeric():
            await ctx.send(f"The correct format for this is `{gv.prefix}pasta (#deck_slot)`!")
            return
        else:
            deck_slot = int(deck_slot)
            if not 1 <= deck_slot <= 6:
                await ctx.send("The deck slot number must between 1-6!")
                return

        gv.mycursor.execute(f"select deck{deck_slot} from playersachivements where userid = {a_id}")
        deck = gv.mycursor.fetchall()[0][0].split(",")
        deck = [" "] if deck == ['0'] else deck

        await ctx.send(f"All the ids in Deck #{deck_slot}: \n`" + " ".join(deck) + "`")

    @commands.command(pass_context=True, aliases=["swaps", "replace", "switch", "change", "alter"], brief="cards")
    @commands.check(cmd_decos.is_registered)
    async def swap(self, ctx: commands.Context, new_id=None, old_id=None):
        """Swap a card from your deck with another"""

        a_id = ctx.message.author.id
        mention = ctx.message.author.mention
        if new_id is None or old_id is None:
            await ctx.send(f"{mention}, the correct format for this command is `{gv.prefix}swap (new_card_id) (old_card_id)`.")
            return
        if not old_id.isnumeric() or not new_id.isnumeric():
            await ctx.send(f"{mention}, those are invalid card id(s)!")
            return

        gv.mycursor.execute(f"select deck_slot from playersinfo where userid = {a_id}")
        deck_slot = gv.mycursor.fetchall()[0][0]
        gv.mycursor.execute(f"select deck{deck_slot} from playersachivements where userid = {a_id}")
        deck = gv.mycursor.fetchall()[0][0].split(",")

        old_id, new_id = int(old_id), int(new_id)
        if (not str(old_id) in deck) or (str(new_id) in deck):
            await ctx.send(f"{mention}, the first id shouldn't exist in your deck #{deck_slot} "
                           f"but the second id need to exist in your deck #{deck_slot}!")
        else:
            gv.mycursor.execute(
                f"select card_name, card_level from cardsinfo where id = {new_id} and owned_user = '{a_id}'")
            new = gv.mycursor.fetchall()[0]
            if not new:
                await ctx.send(f"{mention}, the first id doesn't exist in your card inventory!")
            else:
                deck.remove(str(old_id))
                deck.append(str(new_id))
                gv.mycursor.execute(
                    f"select card_name, card_level from cardsinfo where id = {old_id} and owned_user = '{a_id}'")
                old = gv.mycursor.fetchall()[0]
                gv.mycursor.execute(
                    f"update playersachivements set deck{deck_slot} = '{','.join(deck)}' where userid = '{a_id}'")
                gv.mydb.commit()
                await ctx.send(
                    f"You swapped the card **[{cmd_tools.rarity_cost(old[0])}] {old[0]} lv: {old[1]}** "
                    f"with the card **[{cmd_tools.rarity_cost(new[0])}] {new[0]} lv: {new[1]}** in your deck #{deck_slot}!")

    @commands.command(pass_context=True, aliases=["adds", "use", "uses"], brief="cards")
    @commands.check(cmd_decos.is_registered)
    async def add(self, ctx: commands.Context, *card_id):
        """Add a card to your deck"""

        mention = ctx.message.author.mention
        a_id = ctx.message.author.id
        if not card_id:
            await ctx.send(f"{mention}, the correct format is `{gv.prefix}add (* card_ids)`!")
            return

        gv.mycursor.execute(f"select deck_slot from playersinfo where userid = '{a_id}'")
        deck_slot = gv.mycursor.fetchall()[0][0]
        gv.mycursor.execute(f"select deck{deck_slot} from playersachivements where userid = '{a_id}'")
        deck = gv.mycursor.fetchall()[0][0].split(",")

        deck = [] if deck == ['0'] else deck
        deck_length = 0 if deck else len(deck)

        if deck_length == 12:
            await ctx.send(f"{mention}, your deck's full - do `" + gv.prefix + "swap` instead!")
            return

        card_ids = list(card_id)
        if len(card_ids) > 12 - deck_length:
            await ctx.send(f"{mention}, you can only have at most 12 cards in your deck!")
            return

        final_msg = []
        for x in card_ids:
            try:
                x = math.floor(int(x) + 1 - 1)
                if str(x) in deck:
                    final_msg.append(f"Id `{x}` already in your deck")
                else:
                    gv.mycursor.execute(
                        f"select card_name, card_level from cardsinfo where id = {x} and owned_user = '{a_id}'")
                    y = gv.mycursor.fetchall()[0]
                    if y:
                        final_msg.append(f"**[{cmd_tools.rarity_cost(y[0])}] {y[0]} lv: {y[1]}** » Deck #{deck_slot}")
                        deck.append(str(x))
                    else:
                        final_msg.append(f"Id `{x}` doesn't exist in your inventory")
            except:
                final_msg.append(f"`{x}` isn't a valid card id")

        gv.mycursor.execute(
            f"update playersachivements set deck{deck_slot} = '{','.join(deck)}' where userid = '{a_id}'")
        gv.mydb.commit()
        await ctx.send(f"{mention}\n " + " \n".join(final_msg))

    @commands.command(pass_context=True, aliases=["rem"], brief="cards")
    @commands.check(cmd_decos.is_registered)
    async def remove(self, ctx: commands.Context, *card_id):
        """Remove a card from your deck"""

        mention = ctx.message.author.mention
        a_id = ctx.message.author.id
        if not card_id:
            await ctx.send(f"{mention}, the correct format is `{gv.prefix}remove (* card_ids)`!")
            return

        gv.mycursor.execute(f"select deck_slot from playersinfo where userid = '{a_id}'")
        deck_slot = gv.mycursor.fetchall()[0][0]
        gv.mycursor.execute(f"select deck{deck_slot} from playersachivements where userid = '{a_id}'")
        deck = gv.mycursor.fetchall()[0][0].split(",")
        deck_length = 0 if deck == ['0'] else len(deck)

        if deck_length == 0:
            await ctx.send(f"{mention}, your deck's empty!")
            return

        card_ids = list(card_id)
        final_msg = []
        for x in card_ids:
            try:
                x = math.floor(int(x) + 1 - 1)
                if str(x) in deck:
                    gv.mycursor.execute(
                        f"select card_name, card_level from cardsinfo where id = {x} and owned_user = '{a_id}'")
                    y = gv.mycursor.fetchall()[0]
                    final_msg.append(f"**[{cmd_tools.rarity_cost(y[0])}] {y[0]} lv: {y[1]}** « Deck #{deck_slot}")
                    deck.remove(str(x))
                else:
                    final_msg.append(f"Id `{x}` doesn't exist in your deck")
            except:
                final_msg.append(f"`{x}` isn't a valid card id")

        gv.mycursor.execute(f"update playersachivements set deck{deck_slot} = '{','.join(deck)}' where userid = '{a_id}'")
        gv.mydb.commit()
        await ctx.send(f"{mention}\n " + " \n".join(final_msg))

    @commands.command(pass_context=True, aliases=["clear_deck", "cleardeck"], brief="cards")
    @commands.check(cmd_decos.is_registered)
    @commands.check(cmd_decos.not_preoccupied)
    async def clear(self, ctx):
        """Clear your current deck"""

        a_id = ctx.message.author.id
        mention = ctx.message.author.mention

        gv.queues[str(a_id)] = "deciding to clear a deck slot"
        gv.mycursor.execute("select deck_slot from playersinfo where userid = " + str(a_id))
        deck_slot = gv.mycursor.fetchall()[0][0]
        gv.mycursor.execute(
            f"select deck{deck_slot} from playersachivements where userid = " + str(a_id))
        deck = gv.mycursor.fetchall()[0][0].split(",")

        if deck == ['0']:
            await ctx.send(f"{mention}, your deck's already empty!")
            del gv.queues[str(a_id)]
            return

        msg = await ctx.send(f"{mention}, do you really want to clear Deck #{deck_slot}?")
        await msg.add_reaction(emoji='✅')
        await msg.add_reaction(emoji='❎')
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0,
                                                     check=reaction_check(['❎', '✅'], [ctx.message.author], [msg]))
        except asyncio.TimeoutError:
            await msg.edit(content=f"{mention}, clearing deck cancelled")
            del gv.queues[str(a_id)]
            return

        if reaction.emoji == '❎':
            await msg.edit(content=f"{mention}, clearing deck cancelled")
            del gv.queues[str(a_id)]
            return

        gv.mycursor.execute(
            f"update playersachivements set deck{deck_slot} = '0' where userid = " + str(a_id))
        gv.mydb.commit()
        await msg.edit(content=f"{mention}, your Deck #{deck_slot} has been cleared! \n"
                               f"Do `{gv.prefix}add (card_id)` command to start add new cards into your deck!")
        await msg.clear_reactions()
        del gv.queues[str(a_id)]

    @commands.command(pass_context=True, aliases=["black", "bj"], brief="fun")
    @commands.check(cmd_decos.is_registered)
    @commands.check(cmd_decos.not_preoccupied)
    async def blackjack(self, ctx):
        """No risk no rewards practice command"""

        a_id = ctx.message.author.id
        mention = ctx.message.author.mention

        deck = deepcopy(gv.deck)
        aces = deepcopy(gv.aces)
        values = [0, 0]
        cards = [[], []]
        included_aces = [[], []]
        end = False
        gv.queues[str(a_id)] = "practicing in the blackjack game"

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
        while not end and values[0] < 21:
            await ctx.send(f"{mention} \nYour total: {values[0]} \n{' '.join(cards[0])}"
                           f" \n------------------------------ \nDealer's total: {values[1]} + ? \n"
                           f"{' '.join(cards[1])} [? ? ?] ```\n{gv.prefix}hit -draw a card \n"
                           f"{gv.prefix}stand -end your turn```")
            try:
                msg_reply = await self.bot.wait_for("message", timeout=30.0,
                                                    check=reply_check(['hit', 'stand', 'h', 's'], [ctx.message.author], [ctx.message.channel]))
            except asyncio.TimeoutError:
                values = [1000, 1000]
                await ctx.send(f"{mention}, you blanked out and lost the game!")
            else:
                action = msg_reply.content[len(gv.prefix):].lower()
                if action in ['s', 'stand']:
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

                elif action in ['h', 'hit']:
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

        await ctx.send(f"{mention}, **You {game_state}!** \nYour total: {values[0]} \n{''.join(cards[0])}"
                       f" \n------------------------------ \nDealer's total: {values[1]} \n{''.join(cards[1])}")
        del gv.queues[str(a_id)]

    @commands.command(pass_context=True, brief="fun")
    @commands.check(cmd_decos.is_registered)
    @commands.check(cmd_decos.not_preoccupied)
    async def reaction(self, ctx: commands.Context, wait_time=None):
        """Test your reflexes and counting ability"""

        mention = ctx.message.author.mention
        a_id = ctx.message.author.id
        gv.queues[str(a_id)] = "testing timing accuracy"
        try:
            sec = math.floor(abs(round(int(wait_time)))) + 1 - 1
        except (TypeError, ValueError):
            sec = random.randint(6, 30)
        if sec > 60 or sec < 1:
            sec = random.randint(6, 30)
        t = await ctx.send(f"{mention}, reply `{gv.prefix}` as close as you can to {sec} seconds!")
        try:
            message = await self.bot.wait_for("message", timeout=70.0,
                                              check=reply_check([''], [ctx.message.author], [ctx.message.channel]))
        except asyncio.TimeoutError:
            await ctx.send(f"{mention}, time's up!")
        else:
            recorded = (message.created_at - t.created_at).total_seconds()
            await ctx.send(f"{mention}, you replied in {recorded} seconds, which "
                           f"is {round(abs(sec - recorded) * 1000) / 1000} seconds off from {sec} seconds")
        del gv.queues[str(a_id)]

    @commands.command(pass_context=True, brief="fun")
    @commands.check(cmd_decos.is_registered)
    @commands.check(cmd_decos.not_preoccupied)
    async def say(self, ctx: commands.Context, *stuff):
        """I will agree with anything!"""
        a_id = ctx.message.author.id
        if not stuff:
            stuff = ["but u said u are stupid"]
        img = Image.open("img/crispy_reply.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("fonts/whitneysemibold.ttf", 24)
        draw.text((323, 82), " ".join(stuff), (170, 172, 171), font=font)
        img.save(f"img/{a_id}.png")
        await ctx.send(file=discord.File(f"img/{a_id}.png", filename=f"img/{a_id}.png"))
        os.remove(f"img/{a_id}.png")
        await ctx.message.delete()

    @commands.command(pass_context=True, brief="fun")
    @commands.check(cmd_decos.is_registered)
    @commands.check(cmd_decos.not_preoccupied)
    async def birb(self, ctx: commands.Context, *stuff):
        """Mock the bot's creator"""
        a_id = ctx.message.author.id
        if not stuff:
            stuff = ["1 + 1 = 3"]
        img = Image.open("img/birb_logic.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("fonts/whitneysemibold.ttf", 12)
        draw.text((64, 28), " ".join(stuff), (200, 200, 200), font=font)
        img.save(f"img/{a_id}.png")
        await ctx.send(file=discord.File(f"img/{a_id}.png", filename=f"img/{a_id}.png"))
        os.remove(f"img/{a_id}.png")
        await ctx.message.delete()

    @commands.command(pass_context=True, brief="fun")
    @commands.check(cmd_decos.is_registered)
    @commands.check(cmd_decos.not_preoccupied)
    async def dead(self, ctx: commands.Context, *stuff):
        """Kind of like the 'this is fine' meme, except you can make the dog say whatever you want."""
        a_id = ctx.message.author.id
        if not stuff:
            stuff = ["Should I be scared?"]
        img = Image.open("img/pandemic.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("fonts/whitneysemibold.ttf", 14)
        draw.text((62, 290), " ".join(stuff), (200, 200, 200), font=font)
        img.save(f"img/{a_id}.png")
        await ctx.send(file=discord.File(f"img/{a_id}.png", filename=f"img/{a_id}.png"))
        os.remove(f"img/{a_id}.png")
        await ctx.message.delete()

    @commands.command(pass_context=True, brief="fun")
    @commands.check(cmd_decos.is_registered)
    @commands.check(cmd_decos.not_preoccupied)
    async def kick(self, ctx: commands.Context, *stuffs):
        """A adventurers themed meme template"""

        a_id = ctx.message.author.id
        stuff = [[], []]
        if not stuffs:
            stuff = [["Me", "duelling", "someone"], ["RNG"]]
        else:
            i = 0
            while stuffs[i] != ",":
                stuff[0].append(stuffs[i])
                if i != len(stuffs) - 1:
                    i += 1
                else:
                    break
            if i == len(stuffs) - 1:
                stuff[1] = ["The", "Bot"]
            else:
                i += 1
                for x in range(len(stuffs) - i):
                    stuff[1].append(stuffs[i])
                    i += 1

        img = Image.open("img/meme_template.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("fonts/whitneysemibold.ttf", 17)
        draw.text((80, 25), " ".join(stuff[0]), (256, 256, 256), font=font)
        draw.text((330, 25), " ".join(stuff[1]), (256, 256, 256), font=font)
        img.save(f"img/{a_id}.png")
        await ctx.send(
            file=discord.File(f"img/{a_id}.png", filename=f"img/{a_id}.png"))
        os.remove(f"img/{a_id}.png")
        await ctx.message.delete()

    @commands.command(pass_context=True, aliases=['find_words', 'findwords', 'findword', 'word', 'fw'], brief="fun")
    @commands.check(cmd_decos.is_registered)
    async def find_word(self, ctx: commands.Context, input_: str, limit=5):
        """A tool for finding words with given letters"""
        with open('txts/search.txt') as file:
            try:
                valid_words = []
                for line in file:
                    if limit == 0:
                        break
                    if input_ in line:
                        valid_words.append(line)
                        limit -= 1
                await ctx.send("Words found: \n" + "".join(valid_words))
            except:
                await ctx.send("Something wrong happened with the command! :frowning2:")


def setup(bot):
    bot.add_cog(ActionsCmd(bot))
