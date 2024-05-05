import random
import math
import datetime as dt

import discord
from discord.ext import commands

import db
from helpers import util as u, checks
import resources as r
from views import Confirm, UserTrade

trading_level = 7


class Actions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["d"], description="Get your daily rewards!")
    @checks.is_registered()
    async def daily(self, ctx: commands.Context):
        player = db.Player.get_by_id(ctx.author.id)
        if player.daily_date == dt.date.today():
            dts = u.time_til_midnight()
            await ctx.reply(f"Your next daily is in {dts}!")
            return

        max_streak = 7
        max_tickets = 5
        if player.has_premium():
            max_streak = 14
            max_tickets = 10

        streak = player.streak + 1
        if player.daily_date < dt.date.today() - dt.timedelta(days=1):
            streak = 1
        elif streak >= max_streak:
            streak = max_streak
        player.daily_date = dt.date.today()

        if player.raid_tickets >= max_tickets or player.level < 4:
            ticket_reward = 0
            tick_msg = ""
        else:
            ticket_reward = 1
            tick_msg = f"+{ticket_reward} {r.ICONS['ticket']}"
        player.raid_tickets += ticket_reward

        # Give the user a card or 250 coins, depending on how many they already have
        if len(player.cards) < r.MAX_CARDS:
            card_level = u.log_level_gen(
                random.randint(
                    2 ** (max(0, 5 - (player.level // 4))),
                    2 ** (10 - math.floor(player.level / 10)),
                )
            )
            card = r.card(u.random_card(card_level, "normal"))
            db.Card.create(owner=player.id, name=card.id, level=card_level)
            card_msg = f"Obtained {card} lv: {card_level}!"
        else:
            card_val = 250
            player.coins += card_val
            card_msg = f"Obtained {card_val} {r.ICONS['coin']}!"

        # 1/7 change to get a jackpot daily
        if jackpot := random.randint(1, 7) == 1:
            player.coins += (coin_amt := 400 + math.floor(player.level / 5) * 20 + streak * 80)
            player.xp += (xp_amt := 200)
        else:
            player.coins += (coin_amt := 100 + math.floor(player.level / 5) * 5 + streak * 20)
            player.xp += (xp_amt := 50)

        player.save()
        await ctx.reply(
            ("***JACKPOT!!!***\n" if jackpot else "")
            + f"**+{coin_amt} {r.ICONS['coin']} +{xp_amt} {r.ICONS['exp']} {tick_msg}\n"
            f"Daily streak {streak}/{max_streak} {r.ICONS['streak']}**\n{card_msg}"
        )

    @commands.hybrid_command(description="Trade with other players!")
    @checks.not_preoccupied("trading")
    @checks.level_check(trading_level)
    @checks.is_registered()
    async def trade(self, ctx: commands.Context, target: discord.Member):
        """Trade with other players!"""

        a = ctx.author
        if target.id == a.id:
            await ctx.reply("Are you *really* trying to trade with yourself?")
            return

        db_target = db.Player.get_or_none(db.Player.id == target.id)
        if db_target is None:
            await ctx.reply("That user isn't registered in the bot yet!")
            return
        if db_target.level < trading_level:
            await ctx.reply(f"The target user needs to be at least level {trading_level} to trade!")
            return

        view = Confirm(target)
        deal_msg = await ctx.send(
            f"Hey {target.mention}! Wanna do a trade with {a.mention}?", view=view
        )
        await view.wait()
        if view.value is None:
            await deal_msg.edit(
                content=f"{a.mention}, your trade partner didn't respond in time...",
                view=None,
            )
            return
        elif not view.value:
            await deal_msg.edit(
                content=f"{a.mention}, your trade partner declined the offer...",
                view=None,
            )
            return

        action = db.get_user_action(target.id)
        if action is not None:
            await ctx.reply(f"{target.mention} is currently {action}!")
            return
        db.lock_user(target.id, "trade", "trading")

        view = UserTrade(a, target)
        deal_msg = await deal_msg.edit(content="", embed=view.trade_embed(), view=view)
        await view.wait()

        init_title = f"Trade between {a.display_name} and {target.display_name}"
        if view.went_through is None:
            embed = view.trade_embed()
            embed.title = f"{init_title} - timed out"
            await deal_msg.edit(embed=embed, view=None)
        elif not view.went_through:
            embed = view.trade_embed()
            embed.title = f"{init_title} - rejected"
            await deal_msg.edit(embed=embed, view=None)
        else:
            db_user1 = db.Player.get_by_id(a.id)
            db_user2 = db.Player.get_by_id(target.id)
            db_user1.coins += view.user2_coins - view.user1_coins
            db_user2.coins += view.user1_coins - view.user2_coins
            db_user1.save()
            db_user2.save()

            for c in view.user1_cards:
                c.owner = db_user2
                c.save()
            for c in view.user2_cards:
                c.owner = db_user1
                c.save()

            db.DeckCard.delete().where(
                db.DeckCard.card.in_(view.user1_cards + view.user2_cards)
            ).execute()

            embed = view.trade_embed()
            embed.title = f"{init_title} - **DONE!**"
            await deal_msg.edit(embed=embed, view=None)

        db.unlock_user(target.id, "trade")


async def setup(bot):
    await bot.add_cog(Actions(bot))
