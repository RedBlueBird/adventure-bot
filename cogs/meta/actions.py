import random
import math
import datetime as dt
import asyncio

import discord
from discord.ext import commands

from helpers import db_manager as dm, util as u, resources as r, checks


class Actions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["d"], description="Get your daily rewards!")
    @checks.is_registered()
    async def daily(self, ctx: commands.Context):
        """Get your daily rewards!"""
        a = ctx.author
        last_d = dm.get_user_daily(a.id)
        if last_d.date() == dt.date.today():
            dts = u.time_til_midnight()
            await ctx.reply(f"Your next daily is in {dts}!")
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
            tick_msg = f"+{ticket_reward} {r.ICONS['ticket']}"

        coins = dm.get_user_coin(a.id)
        # Give the user a card or 250 coins, depending on how many they already have
        if dm.get_user_cards_count(a.id) < r.MAX_CARDS:
            card_level = u.log_level_gen(
                random.randint(
                    2 ** (max(0, 5 - (lvl // 4))), 2 ** (10 - math.floor(lvl / 10))
                )
            )
            card = u.random_card(card_level, "normal")
            dm.add_user_cards([(a.id, card, card_level)])
            card_msg = f"Obtained **[{u.rarity_cost(card)}] {card} lv: {card_level}**!"
        else:
            card_val = 250
            coins += card_val
            card_msg = f"Obtained {card_val} {r.ICONS['coin']}!"

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
            ("***JACKPOT!!!***\n" if jackpot else "") +
            f"**+{coin_amt} {r.ICONS['coin'].emoji()} +{xp_amt} {r.ICONS['exp'].emoji()}"
            f" +{medal_amt}{r.ICONS['medal'].emoji()} {tick_msg}\n"
            f"Daily streak {streak}/{max_streak} {r.ICONS['streak']}**\n{card_msg}"
        )

        dm.set_user_coin(a.id, coins)
        dm.set_user_exp(a.id, xp)
        dm.set_user_medal(a.id, medals)
        dm.set_user_ticket(a.id, tickets + ticket_reward)
        dm.set_user_daily(a.id, dt.date.today())
        dm.set_user_streak(a.id, streak)

    @commands.hybrid_command(description="Trade with other players!")
    @checks.not_preoccupied("trading")
    @checks.level_check(7)
    @checks.is_registered()
    async def trade(self, ctx: commands.Context, target: discord.Member):
        """Trade with other players!"""

        if not dm.is_registered(target.id):
            await ctx.reply("That user isn't registered in the bot yet!")
            return
        target_level = dm.get_user_level(target.id)
        if target_level < 7:
            await ctx.reply("The target user needs to be at least level 7 to trade!")
            return
        if target.id == ctx.author.id:
            await ctx.reply("Are you *really* trying to trade with yourself?")
            return
        if target.id in dm.queues:
            await ctx.reply(f"{target.mention} is currently {dm.queues[target.id]}!")
            return

        deal_msg = await ctx.send(
            f"Hey {target.mention}! Wanna do a trade with {ctx.author.mention}?"
        )
        await deal_msg.add_reaction("✅")
        await deal_msg.add_reaction("❌")
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add",
                timeout=60.0,
                check=checks.valid_reaction(
                    ["✅", "❌"], [target, ctx.author], deal_msg
                ),
            )
        except asyncio.TimeoutError:
            await deal_msg.edit(
                content=f"{ctx.author.mention}, your trade partner didn't respond in time..."
            )
            await deal_msg.clear_reactions()
            return
    
        if reaction.emoji == "❌":
            await deal_msg.edit(
                content=f"{ctx.author.mention}, your trade partner declined the trade! :weary:"
            )
            await deal_msg.clear_reactions()
            return
        
        trade_end = False
        confirmed = [False, False]
        author_deck_ids = dm.get_user_deck_ids(ctx.author.id)
        target_deck_ids = dm.get_user_deck_ids(target.id)
        author_coin = dm.get_user_coin(ctx.author.id)
        target_coin = dm.get_user_coin(target.id)
        author_coins_put = 0
        target_coins_put = 0
        author_cards = {}
        target_cards = {}

        def tax():
            return max(
                round(author_coins_put * 0.1) + 150 * len(author_cards),
                round(target_coins_put * 0.1) + 150 * len(target_cards),
            )

        def offer():
            embed = discord.Embed(
                title=f"Trade ongoing!",
                description=f"`{r.PREF}(put/drop) (coin/card) (amount/card_id)`\n"
                            f"`{r.PREF}(confirm/exit/refresh)`\n"
                            f"16 cards at max per side per trade",
                color=discord.Color.gold(),
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
                    name=f"{ctx.author}: :white_check_mark:",
                    value=f"```Golden Coins: {author_coins_put}\n"
                          + "\n".join(author_offer)
                          + "```",
                    inline=False,
                )
            else:
                embed.add_field(
                    name=f"{ctx.author}:",
                    value=f"```Golden Coins: {author_coins_put}\n"
                          + "\n".join(author_offer)
                          + "```",
                    inline=False,
                )
            if confirmed[1]:
                embed.add_field(
                    name=f"{target}: :white_check_mark:",
                    value=f"```Golden Coins: {target_coins_put}\n"
                          + "\n".join(target_offer)
                          + "```",
                    inline=False,
                )
            else:
                embed.add_field(
                    name=f"{target}:",
                    value=f"```Golden Coins: {target_coins_put}\n"
                          + "\n".join(target_offer)
                          + "```",
                    inline=False,
                )

            embed.set_footer(text=f"Transaction fee: {tax()}")
            return embed

        trade_msg = await ctx.send(embed=offer())

        dm.queues[target.id] = "trading"
        while not trade_end:
            try:
                reply_msg = await self.bot.wait_for(
                    "message",
                    timeout=120.0,
                    check=checks.valid_reply(
                        "", [target, ctx.author], ctx.message.channel
                    ),
                )
            except asyncio.TimeoutError:
                del dm.queues[target.id]
                await ctx.send(
                    f"Darn, no one showed up to the trade, so it was called off."
                )
                return

            reply_author = reply_msg.author
            reply_msg = [s.lower() for s in reply_msg.content[len(r.PREF):].split(" ")]
            if len(reply_msg) < 1:
                continue
            if "refresh".startswith(reply_msg[0]):
                trade_msg = await ctx.send(embed=offer())
                continue
            elif reply_msg[0] == "exit":
                confirmed = [False, False]
                await ctx.send(f"Trade is canceled by {reply_author.mention}!")
                trade_end = True
                break
            elif reply_msg[0] == "confirm":
                if reply_author.id == ctx.author.id:
                    if author_coins_put + tax() <= author_coin:
                        confirmed[0] = True
                    else:
                        await ctx.send(
                            f"{ctx.author.mention}, you can't afford the transaction fee!"
                        )
                        continue
                else:
                    if target_coins_put + tax() <= target_coin:
                        confirmed[1] = True
                    else:
                        await ctx.send(
                            f"{target.mention}, you can't afford the transaction fee!"
                        )
                        continue

            if len(reply_msg) < 3 and reply_msg[0] != "confirm":
                continue
            if reply_msg[0] in ["put", "pu"]:
                confirmed = [False, False]
                if reply_msg[1] in ["coin", "co", "coins"]:
                    try:
                        amount = max(int(reply_msg[2]), 0)
                        if reply_author.id == ctx.author.id:
                            if amount <= author_coin:
                                author_coins_put += amount
                            else:
                                await ctx.send(
                                    f"{ctx.author.mention}, you don't have enough coins for this!"
                                )
                                continue
                        else:
                            if amount <= target_coin:
                                target_coins_put += amount
                            else:
                                await ctx.send(
                                    f"{target.mention}, you don't have enough coins for this!"
                                )
                                continue
                    except:
                        continue

                elif reply_msg[1].lower() in ["card", "ca", "cards"]:
                    try:
                        card_id = int(reply_msg[2])
                        card_name = dm.get_card_name(reply_author.id, card_id)
                        card_level = dm.get_card_level(reply_author.id, card_id)
                        if not card_name:
                            await ctx.send(
                                f"{reply_author.mention}, you don't have this card id in your inventory!"
                            )
                            continue
                        else:
                            if reply_author.id == ctx.author.id:
                                if len(author_cards) == 16:
                                    await ctx.send(
                                        f"{ctx.author.mention}, you can only put 16 cards at max per trade!"
                                    )
                                elif card_id in author_cards:
                                    await ctx.send(
                                        f"{ctx.author.mention}, you already put this card id in the offer!"
                                    )
                                    continue
                                elif card_id in author_deck_ids:
                                    await ctx.send(
                                        f"{ctx.author.mention}, you can't put a card from your decks into this offer!"
                                    )
                                else:
                                    author_cards[card_id] = [card_name, card_level]
                            else:
                                if len(target_cards) == 16:
                                    await ctx.send(
                                        f"{target.mention}, you can only put 16 cards at max per trade!"
                                    )
                                elif card_id in target_cards:
                                    await ctx.send(
                                        f"{target.mention}, you already put this card id in the offer!"
                                    )
                                    continue
                                elif card_id in target_deck_ids:
                                    await ctx.send(
                                        f"{target.mention}, you can't put a card from your decks into this offer!"
                                    )
                                else:
                                    target_cards[card_id] = [card_name, card_level]
                    except:
                        continue

            elif "drop".startswith(reply_msg[0].lower()):
                confirmed = [False, False]
                if reply_msg[1].lower() in ["coin", "co", "coins"]:
                    try:
                        amount = max(int(reply_msg[2]), 0)
                        if reply_author.id == ctx.author.id:
                            if amount <= author_coins_put:
                                author_coins_put -= amount
                            else:
                                await ctx.send(
                                    f"{ctx.author.mention}, you can't drop more coins than what you have in your offer!"
                                )
                                continue
                        else:
                            if amount <= target_coins_put:
                                target_coins_put -= amount
                            else:
                                await ctx.send(
                                    f"{target.mention}, you can't drop more coins than what you have in your offer!"
                                )
                                continue
                    except:
                        continue

                elif reply_msg[1].lower() in ["card", "ca", "cards"]:
                    try:
                        card_id = int(reply_msg[2])
                        if reply_author.id == ctx.author.id:
                            if card_id in author_cards:
                                del author_cards[card_id]
                            else:
                                await ctx.send(
                                    f"{ctx.author.mention}, the card id you want to drop doesn't exist!"
                                )
                                continue
                        else:
                            if card_id in target_cards:
                                del target_cards[card_id]
                            else:
                                await ctx.send(
                                    f"{target.mention}, the card if you want to drop doesn't exist!"
                                )
                                continue
                    except:
                        continue

            try:
                await trade_msg.edit(embed=offer())
            except:
                trade_msg = await ctx.send(embed=offer())

            if confirmed[0] and confirmed[1]:
                dm.set_user_coin(
                    ctx.author.id,
                    author_coin + target_coins_put - author_coins_put - tax(),
                )
                dm.set_user_coin(
                    target.id, target_coin + author_coins_put - target_coins_put - tax()
                )
                for card in author_cards:
                    dm.set_card_owner(target.id, card)
                for card in target_cards:
                    dm.set_card_owner(ctx.author.id, card)
                trade_end = True
                del dm.queues[target.id]
                await ctx.send(
                    f"The trade between {ctx.author.mention} and {target.mention} is now finished!"
                )


async def setup(bot):
    await bot.add_cog(Actions(bot))
