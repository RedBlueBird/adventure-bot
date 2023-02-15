import typing as t
import random
import math
import time as times
import datetime as dt

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db_manager as dm
import util as u
from helpers import checks
from views import Shop, CardPages, Decks, Leaderboard


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="profile",
        description="Check a player's general information.",
        aliases=["p", "pro"]
    )
    async def profile(self, ctx: Context, user: discord.Member = None):
        """Check a player's general information."""

        user = ctx.author if user is None else user

        if not dm.is_registered(user.id):
            await ctx.send(f"{ctx.author.mention}, that user isn't registered!")
            return

        user_premium = dm.get_user_premium(user.id)
        if user_premium > dt.datetime.today():
            days_left = (user_premium - dt.datetime.today()).days
            description_msg = f"14\n{u.ICON['timer']}**ᴘʀᴇᴍɪᴜᴍ**: " \
                              f"{days_left} days remaining\n"
            tickets = 10
        else:
            description_msg = "7\n"
            tickets = 5

        tick_msg = ""
        lvl = dm.get_user_level(user.id)
        if lvl >= 4:
            tick_msg = f"{u.ICON['tick']}**Raid Tickets: **{dm.get_user_ticket(user.id)}/{tickets}"

        descr = f"```{dm.queues[user.id]}```\n" if user.id in dm.queues else None
        embed = discord.Embed(
            title=f"{user.display_name}'s profile:",
            description=descr,
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=user.avatar.url)

        hp = round((100 * u.SCALE[1] ** math.floor(lvl / 2)) * u.SCALE[0])
        xp = dm.get_user_exp(user.id)
        if lvl < 30:
            embed.add_field(
                name=f"Current Level: {lvl}",
                value=f"{u.ICON['exp']} {xp}/{u.level_xp(lvl)}\n"
                      f"{u.ICON['hp']} {hp}",
                inline=False
            )
        else:
            embed.add_field(
                name=f"Max Level: {lvl}",
                value=f"{u.ICON['exp']} {xp}\n"
                      f"{u.ICON['hp']} {hp}",
                inline=False
            )

        user_daily = dm.get_user_daily(user.id)
        dts = "Right now!" if user_daily.date() != dt.date.today() else u.time_til_midnight()
        embed.add_field(
            name="Currency",
            value=f"{u.ICON['coin']}**Golden Coins: **{dm.get_user_coin(user.id)}\n"
                  f"{u.ICON['gem']}**Shiny Gems: **{dm.get_user_gem(user.id)}\n"
                  f"{u.ICON['token']}**Confetti: **{dm.get_user_token(user.id)}\n"
                  f"{u.ICON['medal']}**Medals: **{dm.get_user_gem(user.id)}\n"
                  f"{tick_msg}",
            inline=False
        )

        quests = dm.get_user_quest(user.id)
        embed.add_field(
            name="Tasks",
            value=f"{u.ICON['streak']}**Daily streak: **{dm.get_user_streak(user.id)}/" +
                  description_msg +
                  f"{u.ICON['timer']}**Next daily: **{dts}\n"
                  f"{u.ICON['timer']}**Next quest: "
                  f"**{u.time_converter(int(quests.split(',')[-1]) - int(times.time()))}",
            inline=False
        )

        badges = dm.get_user_badge(user.id)
        if badges != 2 ** 30:
            badges = ["beta b", "pro b", "art b", "egg b", "fbi b", "for b"]
            owned_badges = []
            for i in range(29):
                if badges % 2 == 1:
                    owned_badges.append(u.ICON[badges[i]])
                badges = badges >> 1
            embed.add_field(name="Badges: ", value=" ".join(owned_badges))

        embed.set_footer(
            text=f"Player ID: {dm.get_id(user.id)}; "
                 f"Register Date: {dm.get_user_register_date(user.id)}"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="quests",
        description="Displays all current quests of a user.",
        aliases=["q", "quest", "qu"]
    )
    async def quests(self, ctx: Context, user: discord.Member = None):
        """Displays all current quests of a user."""

        user = ctx.author if user is None else user
        if not dm.is_registered(user.id):
            await ctx.send(f"{ctx.author.mention}, that user isn't registered yet!")
            return

        user_quest = dm.get_user_quest(user.id)
        user_premium = dm.get_user_premium(user.id)

        quests = user_quest.split(",")
        is_premium = user_premium > dt.datetime.today()

        if (len(quests) < 4 and not is_premium) or (len(quests) < 5 and is_premium):
            if int(quests[-1]) - int(times.time()) <= 1:
                # premium members have to wait less and get one more quest slot as well
                quests_count = abs(math.floor((int(times.time()) - int(quests[-1])) / (1800 - 900 * is_premium))) + 1
                extra_time = (int(times.time()) - int(quests[-1])) % (1800 - 900 * is_premium)
                if (4 + is_premium) - len(quests) < quests_count:
                    quests_count = (4 + is_premium) - len(quests)
                    extra_time = 0

                quests[-1] = str(int(times.time()) + (900 + 900 * is_premium) - extra_time)

                for _ in range(quests_count):
                    quest_id = math.ceil(u.log_level_gen(random.randint(1, 2 ** 8)) / 2) - 2
                    award_type = 1
                    if quest_id > 0 and random.randint(1, 100) >= 75:
                        award_type = 2
                    elif random.randint(1, 100) >= 101:
                        award_type = 3
                    received_quest_types = [int(quests[x].split(".")[1]) for x in range(len(quests) - 1)]
                    new_quest_type = random.randint(1, 8)
                    while new_quest_type in received_quest_types:
                        new_quest_type = random.randint(1, 8)
                    quests.insert(-1, f"{quest_id}{award_type}.{new_quest_type}.0")

                dm.set_user_quest(user.id, ','.join(quests))

        if len(quests) == 1:
            embed = discord.Embed(
                title=f"{user.display_name}'s Quests:",
                description="You don't have any quests.\nCome back later for more!",
                color=discord.Color.green()
            )
        else:
            bad = 4 + is_premium
            if len(quests) == bad:
                embed = discord.Embed(
                    title=f"{user.display_name}'s Quests:",
                    description=f"You can't have more than {bad - 1} quests active!",
                    color=discord.Color.gold()
                )
            else:
                embed = discord.Embed(
                    title=f"{user.display_name}'s Quests:",
                    color=discord.Color.gold()
                )

            for q in quests[:-1]:
                quest = u.quest_index(q)
                embed.add_field(
                    name=f"**{quest[2]} {u.quest_str_rep(q.split('.')[1], quest[0])}**",
                    value=f"Finished {math.floor(100 * int(q.split('.')[2]) / quest[0])}%\n"
                          f"Reward: **{''.join(quest[1::2])} {quest[4]} {u.ICON['exp']}**",
                    inline=False
                )

        embed.set_thumbnail(url=user.avatar.url)
        time_left = u.time_converter(int(quests[-1]) - int(times.time()))
        if time_left != "Right Now":
            embed.set_footer(text=f"There's {time_left} left till a new quest")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="inventory",
        description="Displays all the cards in a member's inventory.",
        aliases=["card", "cards", "i", "inv"]
    )
    async def inventory(self, ctx: Context, page: int = 1, user: discord.Member = None):
        user = ctx.author if user is None else user
        if not dm.is_registered(user.id):
            await ctx.reply("That user isn't registered yet!")
            return

        view = CardPages(user, page=page - 1)
        await ctx.send(embed=view.page_embed(), view=view)

    @commands.hybrid_command(
        name="leaderboard",
        description="Displays the world's top players.",
        aliases=["lb", "lbs"]
    )
    async def leaderboard(
            self, ctx: Context,
            name: t.Literal["level", "coins", "gems", "medals", "tokens"]
    ) -> None:
        view = Leaderboard(name, ctx.author.id, self.bot)
        await ctx.send(embed=await view.lb_embed(), view=view)

    @commands.hybrid_command(
        name="deck",
        description="Displays the user's currently equipped deck."
    )
    async def deck(self, ctx: Context, slot: int = 0, user: discord.Member = None) -> None:
        user = ctx.author if user is None else user
        if not dm.is_registered(user.id):
            await ctx.reply(f"That user isn't registered yet!")
            return

        if not 0 <= slot <= 6:
            await ctx.reply("The deck slot number must between 1-6!")
            return

        if slot != 0 and dm.get_user_level(user.id) < u.DECK_LVL_REQ[slot]:
            await ctx.reply(f"You need to reach {u.DECK_LVL_REQ[slot]} to get that deck slot!")
            return

        view = Decks(user, slot)
        await ctx.send(embed=view.deck_embed(), view=view)

    @commands.hybrid_command(
        name="decklist",
        description="Displays all decks of a user."
    )
    async def decklist(self, ctx: Context, user: discord.Member = None):
        user = ctx.author if user is None else user
        if not dm.is_registered(user.id):
            await ctx.reply(f"That user isn't registered!")
            return

        view = Decks(user)
        await ctx.send(embed=view.decklist_embed(), view=view)

    @commands.hybrid_command(name="shop", description="Display the shop.")
    @checks.level_check(3)
    async def shop(self, ctx: Context) -> None:
        embed = discord.Embed(
            title="Welcome to the card shop!",
            description="Click a page to get started."
        )
        await ctx.send(embed=embed, view=Shop(ctx.author.id))


async def setup(bot):
    await bot.add_cog(Info(bot))
