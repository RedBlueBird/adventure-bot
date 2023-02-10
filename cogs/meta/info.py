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
from views import Shop, CardPages


class Info(commands.Cog, name="info"):
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
            description_msg = f"14\n{u.ICON['timer']}**ᴘʀᴇᴍɪᴜᴍ**: " \
                              f"{(user_premium - dt.datetime.today()).days} days remaining\n"
            tickets = 10
        else:
            description_msg = "7\n"
            tickets = 5

        tick_msg = ""
        lvl = dm.get_user_level(user.id)
        if lvl >= 4:
            tick_msg = f"{u.ICON['tick']}**Raid Tickets: **{dm.get_user_ticket(user.id)}/{tickets}"

        descr = f"```{dm.queues[str(user.id)]}```\n" if str(user.id) in dm.queues else None
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
        """
        Displays all the cards in a member's inventory in the form of an embed.
        :param page: The page of cards to display
        :param user: The user whose cards to display
        """

        user = ctx.author if user is None else user
        if not dm.is_registered(user.id):
            await ctx.reply("That user isn't registered yet!")
            return

        view = CardPages(user, page=page - 1)
        await ctx.send(embed=view.gen_embed(), view=view)

    @commands.hybrid_command(
        name="leaderboard",
        description="Displays the world's top players.",
        aliases=["lb", "lbs"]
    )
    async def leaderboard(
            self, ctx: Context,
            lb_type: t.Literal["level", "coins", "gems", "medals", "tokens"]
    ) -> None:
        """
        Displays the world's top players.
        :param lb_type: The type of leaderboard to display
        """

        lim = 10
        raw_descr = None
        if lb_type == "level":
            lb_type = "XP"
            raw_descr = "• Level: {}, Exp: {}"
        elif lb_type == "coins":
            lb_type = "Golden Coins"
            raw_descr = "• Golden Coins: {}, Shiny Gems: {}"
        elif lb_type == "gems":
            lb_type = "Shiny Gems"
            raw_descr = "• Shiny Gems: {}, Golden Coins: {}"
        elif lb_type == "medals":
            lb_type = "Medals"
            raw_descr = "• Medals: {}"
        elif lb_type == "tokens":
            lb_type = "Tokens"
            raw_descr = "• Tokens: {}"
        assert raw_descr is not None

        selected_players = []
        players = dm.get_leaderboard(lb_type, lim)
        for index, player in enumerate(players):
            username = await self.bot.fetch_user(str(player[1]))
            name = f"**[{index + 1}] {username}**\n"

            if len(player) == 3:
                descr = raw_descr.format(player[2])
            else:
                descr = raw_descr.format(player[2], player[3])

            if str(player[1]) == str(ctx.author.id):
                descr = f"__{descr}__"
            selected_players.append("".join([name, descr + "\n"]))

        embed = discord.Embed(
            title=f"Leaderboard - most {lb_type}",
            description="".join(selected_players),
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="deck",
        description="Displays the deck in the member's current deck slot"
    )
    async def deck(self, ctx: Context, slot: int = 0, user: discord.Member = None) -> None:
        """
        Displays the deck in the member's current deck slot
        :param slot: The deck slot to search.
        :param user: The user whose deck slots to search.
        """

        user = ctx.author if user is None else user
        if not dm.is_registered(user.id):
            await ctx.send(f"{ctx.author.mention}, that user isn't registered yet!")
            return

        if not 0 <= slot <= 6:
            await ctx.send("The deck slot number must between 1-6!")
            return

        u_slot = dm.get_user_deck_slot(user.id)
        slot = slot if slot != 0 else u_slot

        if dm.get_user_level(user.id) < u.DECK_LVL_REQ[slot]:
            await ctx.send("You don't have access to that deck slot yet!")
            return

        user_deck = dm.get_user_deck(user.id, slot)
        equipped_deck_ids = user_deck if slot == u_slot else dm.get_user_deck(user.id, u_slot)
        equipped_deck_ids = [i[0] for i in equipped_deck_ids]
        all_cards = []
        tot_energy = 0
        for x in user_deck:
            card = f"[{u.rarity_cost(x[1])}] **{x[1]}**, lv: **{x[2]}**, id: `{x[0]}` "
            if x[0] == equipped_deck_ids:
                card = f"**>**{card}"
            all_cards.append(card)
            tot_energy += u.cards_dict(x[2], x[1])["cost"]

        mod_msg = "" if slot == u_slot else f"\n`{u.PREF}select {slot}` to modify this deck"
        embed = discord.Embed(
            title=f"{user.display_name}'s Deck #{slot}:",
            description=f"`{u.PREF}decklist` to display all your decks{mod_msg}\n\n" +
                        "\n".join(all_cards),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=user.avatar.url)
        if not user_deck:
            embed.add_field(
                name="You don't have any cards in your deck!",
                value=f"`{u.PREF}add (card_id)` to start adding cards!"
            )

        len_req = 12
        if len(user_deck) != len_req:
            embed.set_footer(text=f"{len_req - len(user_deck)}/12 more card(s) to complete this deck.")
        else:
            embed.set_footer(text=f"Average energy cost: {round(tot_energy / len_req, 1)}")

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="decklist",
        description="Displays all decks of a user."
    )
    async def decklist(self, ctx: Context, user: discord.Member = None):
        user = ctx.author if user is None else user
        if not dm.is_registered(user.id):
            await ctx.send(f"{ctx.author.mention}, that user isn't registered yet!")
            return

        embed = discord.Embed(
            title=f"{user.display_name}'s decks",
            description=f"`{u.PREF}deck #` to view a specific deck",
            color=discord.Color.gold()
        )

        for i in range(6):
            name = f"**Deck {i + 1}**"
            if dm.get_user_deck_slot(user.id) == i + 1:
                name += " - selected"

            if dm.get_user_level(user.id) < u.DECK_LVL_REQ[i + 1]:
                card_info = f"Unlocked at level {u.DECK_LVL_REQ[i + 1]}"
            else:
                deck_lens = dm.get_user_deck_count(user.id, i + 1)
                card_info = f"{deck_lens}/12 cards"

            embed.add_field(name=name, value=card_info, inline=False)

        embed.set_thumbnail(url=user.avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="shop", description="Display the shop.")
    @checks.level_check(3)
    async def shop(self, ctx: Context) -> None:
        """The player can buy cards and other things here."""
        embed = discord.Embed(
            title="Welcome to the card shop!",
            description="Click a page to get started."
        )
        await ctx.send(embed=embed, view=Shop(ctx.author.id))


async def setup(bot):
    await bot.add_cog(Info(bot))
