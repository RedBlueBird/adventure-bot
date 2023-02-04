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


class Stats(commands.Cog, name="informational"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="profile",
        description="Check a player's general information.",
        aliases=["p", "pro"]
    )
    async def profile(self, ctx: Context, user: discord.Member = None) -> None:
        """Check a player's general information."""

        user = ctx.author if user is None else user

        if not dm.is_registered(user.id):
            await ctx.send(f"{ctx.author.mention}, that user isn't registered!")
            return

        user_premium = dm.get_user_premium(user.id)
        if user_premium > dt.datetime.today():
            description_msg = f"14 \n{u.ICON['timer']}**ᴘʀᴇᴍɪᴜᴍ**: " \
                              f"{(user_premium - dt.datetime.today()).days} days remaining\n"
            tickets = 10
        else:
            description_msg = "7 \n"
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
            name="Currency: ",
            value=f"{u.ICON['coin']}**Golden Coins: **{dm.get_user_coin(user.id)}\n"
                  f"{u.ICON['gem']}**Shiny Gems: **{dm.get_user_gem(user.id)}\n"
                  f"{u.ICON['token']}**Confetti: **{dm.get_user_token(user.id)}\n"
                  f"{u.ICON['medal']}**Medals: **{dm.get_user_gem(user.id)}\n"
                  f"{tick_msg}",
            inline=False
        )

        quests = dm.get_user_quest(user.id)
        embed.add_field(
            name="Times: ",
            value=f"{u.ICON['streak']}**Daily streak: **{dm.get_user_streak(user.id)}/" +
                  description_msg +
                  f"{u.ICON['timer']}**Next daily: **{dts} \n"
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
        aliases=["q"]
    )
    async def quests(self, ctx: Context, user: discord.Member = None) -> None:
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

                for y in range(quests_count):
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

            for x in range(len(quests) - 1):
                quest = u.quest_index(quests[x])
                embed.add_field(
                    name=f"**{quest[2]} {u.quest_str_rep(quests[x].split('.')[1], quest[0])}**",
                    value=f"Finished {math.floor(100 * int(quests[x].split('.')[2]) / quest[0])}%\n"
                          f"Reward: **{''.join(quest[1::2])} {quest[4]} {u.ICON['exp']}**",
                    inline=False
                )  # **1 {u.icon['token']}**", inline=False)

        embed.set_thumbnail(url=user.avatar.url)
        time_left = u.time_converter(int(quests[-1]) - int(times.time()))
        if time_left != "Right Now":
            embed.set_footer(text=f"There's {time_left} left till a new quest")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="inventory",
        description="Displays all the cards in a member's inventory in the form of an embed.",
        aliases=["card", "i", "inv"]
    )
    async def inventory(self, ctx: Context, page: int = 1, user: discord.Member = None) -> None:
        """
        Displays all the cards in a member's inventory in the form of an embed.

        :param page: The page of cards to display
        :param user: The user whose cards to display
        """

        user = ctx.author if user is None else user
        if not dm.is_registered(user.id):
            await ctx.send(f"{ctx.author.mention}, that user isn't registered yet!")
            return

        user_deck = dm.get_user_deck(user.id)
        deck_ids = [card[0] for card in user_deck]
        user_cards = dm.get_user_cards(user.id, start=(page - 1) * 15, length=15)
        user_cards_count = dm.get_user_cards_count(user.id)

        if len(user_cards) == 0:
            await ctx.send(f"{ctx.author.mention}, you don't have any cards on page {page}!")
            return

        all_cards = []
        for card in user_cards:
            if card[0] in deck_ids:
                all_cards.append(
                    f"**>**[{u.rarity_cost(card[1])}] **{card[1]}**, "
                    f"lv: **{card[2]}**, id: `{card[0]}` "
                )
            else:
                all_cards.append(
                    f"[{u.rarity_cost(card[1])}] **{card[1]}**, "
                    f"lv: **{card[2]}**, id: `{card[0]}` "
                )

        embed = discord.Embed(
            title=f"{user.display_name}'s cards:",
            description="\n".join(all_cards),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=user.avatar.url)
        show_start = (page - 1) * 15 + 1
        show_end = show_start + len(user_cards) - 1
        embed.set_footer(text=f"{show_start}-{show_end}/{user_cards_count} cards displayed on page {page}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="leaderboard",
        description="Displays the world's top players.",
        aliases=["lb", "lbs"]
    )
    async def leaderboard(self, ctx: Context, lb_type: str = "") -> None:
        """
        Displays the world's top players.
        :param lb_type: The type of leaderboard to display
        """

        lim = 10
        lb_type = lb_type.lower()
        if lb_type.lower() in ["levels", "level", "exps", "exp", "l", "e"]:
            lb_type = "XP"
            raw_descr = "• Level: {}, Exp: {}"
        elif lb_type.lower() in ["coins", "golden_coins", "goldencoins", "goldencoins", "coin", "gc", "c"]:
            lb_type = "Golden Coins"
            raw_descr = "• Golden Coins: {}, Shiny Gems: {}"
        elif lb_type.lower() in ["shiny_gems", "shinygems", "shiny_gem", "shinygem", "gems", "gem", "g", "sg"]:
            lb_type = "Shiny Gems"
            raw_descr = "• Shiny Gems: {}, Golden Coins: {}"
        elif lb_type.lower() in ["medals", "medal", "m"]:
            lb_type = "Medals"
            raw_descr = "• Medals: {}"
        elif lb_type.lower() in ["tokens", "t", "event_tokens", "token"]:
            lb_type = "Tokens"
            raw_descr = "• Tokens: {}"
        else:
            embed = discord.Embed(
                title="Available leaderboards",
                description=f"`{u.PREF}leaderboard (leaderboard type)`",
                color=discord.Color.gold()
            )
            lb_types = ["XP", "Golden Coins", "Shiny Gems", "Medals", "Tokens"]
            lb_commands = ["levels", "coins", "gems", "medals", "tokens"]
            for i in range(len(lb_types)):
                embed.add_field(
                    name=f"Players with the most {lb_types[i]}",
                    value=f"`{u.PREF}leaderbord {lb_commands[i]}`",
                    inline=False
                )
            embed.set_footer(text=f"Shows the top {lim} players in the world.")
            await ctx.send(embed=embed)
            return

        selected_players = []
        players = dm.get_leaderboard(lb_type, lim)
        for index, player in enumerate(players):
            username = await self.bot.fetch_user(str(player[1]))
            name = f"**[{index + 1}] {username}** \n"

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
        description="Displays the deck in the member's current deck slot",
        aliases=["decks"]
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

        user_deck = dm.get_user_deck(user.id)
        all_cards = []
        tot_energy = 0
        for x in user_deck:
            card = f"[{u.rarity_cost(x[1])}] **{x[1]}**, lv: **{x[2]}**, id: `{x[0]}` "
            if slot == u_slot:
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
            embed.set_footer(text=f"You need {len_req - len(user_deck)} more cards needed to complete this deck.")
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

    @commands.hybrid_command(
        name="info",
        description="Looks up entities, from effects to mobs and displays an embed containing info about it.",
        aliases=["in", "information", "check"]
    )
    async def info(
            self, ctx: Context,
            type_: t.Literal["card", "monster", "item", "effect"],
            name: str, level: int = 1
    ) -> None:
        """
        Looks up entities, from effects to mobs and displays an embed containing info about it.
        :param type_: The type of the thing which to look up (can be a card, mob, item, or effect)
        :param name: The name of the thing to look up
        :param level: The level of the thing for number crunching
        """

        rarity_translator = {
            "C": "Common", "R": "Rare", "E": "Epic", "EX": "Exclusive",
            "L": "Legendary", "M": "N/A", "NA": "N/A"
        }

        embed = None
        if type_ == "card":
            card_info = u.cards_dict(level, " ".join(name.lower().split("_")))
            info_str = [
                f"**Name:** {card_info['name']}",
                f"**Level:** {level}",
                f"**Rarity:** {rarity_translator[card_info['rarity']]}",
                f"**Energy Cost:** {card_info['cost']}",
                f"**Accuracy:** {card_info['acc']}%",
                f"**Critical Chance:** {card_info['crit']}%"
            ]

            if card_info["rarity"] == "M":
                info_str.insert(len(info_str), "**[Monster Card]** - Unobtainable")
            if card_info["rarity"] == "EX":
                info_str.insert(len(info_str), "**[Exclusive Card]** - Obtainable in events")

            embed = discord.Embed(title="Card's info:", description=None, color=discord.Color.green())
            embed.add_field(name="Description: ", value="\n".join(info_str), inline=False)
            embed.add_field(name="Uses: ", value=u.fill_args(card_info, level), inline=False)
            embed.add_field(name="Brief: ", value=card_info["brief"], inline=False)
            """
            if "journal" in card_info:
                embed.add_field(name="Scout's Journal: ", value="*" + card_info["journal"] + "*", inline=False)
            embed.set_thumbnail(url=ctx.author.avatar.url)
            """

        elif type_ == "monster":
            mob_info = u.mobs_dict(level, " ".join(name.lower().split("_")))
            info_str = [
                f"**Name:** {mob_info['name']}",
                f"**Level:** " + str(level),
                f"**Rarity:** {rarity_translator[mob_info['rarity']]}",
                f"**Energy Lag:** {mob_info['energy_lag']} turns",
                f"**Health:** {mob_info['health']}",
                f"**Stamina:** {mob_info['stamina']}"
            ]

            embed = discord.Embed(title="Mob's info:", description=None, color=discord.Color.green())
            embed.add_field(name="Description: ", value="\n".join(info_str), inline=False)
            embed.add_field(name="Brief: ", value=f"*{mob_info['brief']}*", inline=False)
            """
            if "tip" in mob_info:
                embed.add_field(name="Fighting Tips: ", value="*" + mob_info["tip"] + "*", inline=False)
            if "journal" in mob_info:
                embed.add_field(name="Scout's Journal: ", value="*" + mob_info["journal"] + "*", inline=False)
            embed.set_thumbnail(url=ctx.author.avatar.url)
            """

        elif type_ == "item":
            item_info = u.items_dict(" ".join(name.lower().split("_")))
            name = item_info["name"]
            info_str = [
                f"**Name:** {name}",
                f"**Weight:** {item_info['weight']}",
                f"**Rarity:** {rarity_translator[item_info['rarity']]}",
                f"**Accuracy:** {item_info['acc']}%",
                f"**Critical Chance:** {item_info['crit']}%",
                f"**One Use:** {item_info['one_use']}",
                f"**Use In Battle:** {item_info['in_battle']}",
                f"**Sell Price:** {item_info['sell']}gc",
                f"**Abbreviation:** {item_info['abb']}"
            ]

            embed = discord.Embed(title="Item's info:", description=None, color=discord.Color.green())
            embed.add_field(name="Description: ", value="\n".join(info_str), inline=False)
            embed.add_field(name="Uses: ", value=item_info["description"], inline=False)
            embed.add_field(name="Brief: ", value=f"*{item_info['brief']}*", inline=False)

            """
            if "journal" in item_info:  
                embed.add_field(name="Scout's Journal: ", value="*" + item_info["journal"] + "*", inline=False)
            embed.set_thumbnail(url=ctx.author.avatar.url)a.
            """
            # print(u.ICON[item_info['name'].lower()])
            if name.lower() in u.ICON:
                icon = u.ICON[name.lower()]
                icon_id = icon[icon.rfind(":") + 1:-1]
                embed.set_image(url=f"https://cdn.discordapp.com/emojis/{icon_id}.png")

        elif type_ == "effect":
            fx_info = u.fx_dict(" ".join(name.lower().split("_")))
            embed = discord.Embed(title="Effect's info:", description=None, color=discord.Color.green())
            embed.add_field(name="Description: ", value=f"**Name:** {fx_info['name']}", inline=False)
            embed.add_field(name="Uses: ", value=fx_info["description"], inline=False)
            embed.set_image(
                url=f"https://cdn.discordapp.com/emojis/"
                    f"{u.CONVERT[fx_info['name'].lower()][4:-1]}.png"
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="shop", description="Display the shop.")
    @checks.level_check(3)
    async def shop(self, ctx: Context, page: int = -1) -> None:
        """
        The player can buy cards and other things here.
        :param page: The page of the stop to display.
        """
        a = ctx.author
        if not 1 <= page <= 3:
            embed = discord.Embed(title="Card Shop", description=None, color=discord.Color.gold())
            embed.add_field(name="Daily Deals", value="**»** page 1", inline=False)
            embed.add_field(name="Card Packs", value="**»** page 2", inline=False)
            embed.add_field(name="Currency", value="**»** page 3", inline=False)
            embed.set_footer(text=f"{u.PREF}shop (page_number)")
            await ctx.send(embed=embed)
            return

        coins = dm.get_user_coin(a.id)
        gems = dm.get_user_gem(a.id)
        tokens = dm.get_user_token(a.id)

        embed = None
        if page == 1:
            user_deals = dm.get_user_deals(a.id).split(",")
            embed = discord.Embed(
                title="Shop - Daily Deals:",
                description=f"{u.ICON['coin']} **{coins}** {u.ICON['gem']} **{gems}**",
                color=discord.Color.gold()
            )

            for x in range(len(user_deals)):
                card = user_deals[x].split('.')
                if user_deals[x][0] != "-":
                    cost = round(1.6 ** int(card[0]) * 50 * u.price_factor(card[1]))
                    embed.add_field(
                        name=f"**[{u.rarity_cost(card[1])}] {card[1]} lv: {card[0]}**",
                        value=f"Cost: **{cost}** {u.ICON['coin']} \n`{u.PREF}buy {x + 1}`"
                    )
                else:
                    embed.add_field(
                        name=f"**[{u.rarity_cost(card[1])}] {card[1]} lv: {card[0][1:]}**",
                        value="Purchased"
                    )
            embed.set_footer(text=f"Wait {u.time_til_midnight()} or {u.PREF}buy r to refresh shop")

        elif page == 2:
            embed = discord.Embed(
                title="Shop - Card Packs:",
                description=f"{u.ICON['coin']} **{coins}** {u.ICON['gem']} "
                            f"**{gems}** {u.ICON['token']} **{tokens}**",
                color=discord.Color.green()
            )

            packs = [
                {
                    "name": "**Basic Pack**",
                    "value": f"Cost: **3** {u.ICON['gem']} \n"
                             "• contains 3 (lv 4-10) cards \n"
                             f"`{u.PREF}buy basic`"
                },
                {
                    "name": "**Fire Pack**",
                    "value": f"Cost: **5** {u.ICON['gem']} \n"
                             "• contains 4 (lv 4-10) cards with a \nhigher chance of fire cards \n"
                             f"`{u.PREF}buy fire`"
                },
                {
                    "name": "**Evil Pack**",
                    "value": f"Cost: **5** {u.ICON['gem']} \n"
                             "• contains 4 (lv 4-10) cards with a \nhigher chance of curse cards \n"
                             f"`{u.PREF}buy evil`"
                },
                {
                    "name": "**Electric Pack**",
                    "value": f"Cost: **5** {u.ICON['gem']} \n"
                             "• contains 4 (lv 4-10) cards with a \nhigher chance of electric cards \n"
                             f"`{u.PREF}buy electric`"
                },
                {
                    "name": "**Defensive Pack**",
                    "value": f"Cost: **5** {u.ICON['gem']} \n"
                             "• contains 4 (lv 4-10) cards with a \nhigher chance of defense cards \n"
                             f"`{u.PREF}buy defensive`"
                },
                {
                    "name": "**Pro Pack**",
                    "value": f"Cost: **24** {u.ICON['gem']} \n"
                             "• contains 6 (lv 7-10) cards \n"
                             f"`{u.PREF}buy pro`"
                },
                # {"name": "**Anniversary Pack**",
                # "value": f"Cost: **40** {u.icon['token']} \n"
                #          "• contains **[EX/7] Confetti Cannon** \n"
                #          f"`{u.prefix}buy confetti`"}
            ]

            for p in packs:
                embed.add_field(**p)
            embed.set_footer(text="Let the buyer beware")

        elif page == 3:
            embed = discord.Embed(
                title="Shop - Currencies:",
                description=f"{u.ICON['coin']} **{coins}** {u.ICON['gem']} **{gems}**",
                color=discord.Color.green()
            )  # {u.icon['token']} **{user_token}**")

            currency_offers = [
                {"name": "**1000 Golden Coins**", "value": f"Cost: **3** {u.ICON['gem']} \n`{u.PREF}buy gc1`"},
                {"name": "**2250 Golden Coins**", "value": f"Cost: **6** {u.ICON['gem']} \n`{u.PREF}buy gc2`"},
                {"name": "**11000 Golden Coins**", "value": f"Cost: **24** {u.ICON['gem']} \n`{u.PREF}buy gc3`"},
                {"name": "**1 Raid Ticket**", "value": f"Cost: **2** {u.ICON['gem']} \n`{u.PREF}buy rt1`"},
                {"name": "**2 Raid Ticket**", "value": f"Cost: **4** {u.ICON['gem']} \n`{u.PREF}buy rt2`"},
                {"name": "**3 Raid Ticket**", "value": f"Cost: **6** {u.ICON['gem']} \n`{u.PREF}buy rt3`"}
            ]
            for field in currency_offers:
                embed.add_field(**field)

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="card_search",
        description="Searches your cards according to a query.",
        aliases=["cardsearch", "cs", "search"]
    )
    async def card_search(
            self, ctx: Context,
            search_type: t.Literal["level", "name", "rarity", "energy cost"],
            query: str | None = None,
            page: int = 1
    ) -> None:
        """
        Searches your cards according to a query.
        :param search_type: What to search by
        :param query: The actual search query that the bot will search by
        :param page: The page of the card results to go to.
        """
        p_len = 15

        page = max(page, 1)

        a = ctx.author
        deck_ids = [card[0] for card in dm.get_user_deck(a.id)]

        res = []
        search_type = search_type.lower()
        if search_type == "level":
            additional = "" if query is None else f"AND card_level = {query}"
            res = dm.get_user_cards(a.id, add_rules=additional)

        elif search_type == "name":
            res = dm.get_user_cards(
                a.id, add_rules="" if query is None else f"AND card_name LIKE '%{query}%'"
            )

        elif search_type == "rarity":
            user_cards = dm.get_user_cards(a.id)
            rarity_terms = {
                "L": ["legendary", "legend", "leg", "le", "l"],
                "EX": ["exclusive", "exclu", "exc", "ex"],
                "E": ["epic", "ep", "e"],
                "R": ["rare", "ra", "rr", "r"],
                "C": ["common", "com", "co", "c"],
                "M": ["monsters", "monster", "mon", "mons", "mo", "most", "mosts", "m", "ms"],
                "NA": ["not_available", "notavailable", "not_ava", "notava", "not", "no", "na", "n/a", "n"]
            }

            if query is None:
                res = user_cards
            else:
                for x in user_cards:
                    if query.lower() in rarity_terms[u.cards_dict(x[2], x[1])["rarity"]]:
                        res.append(x)

        elif search_type == "energy cost":
            user_cards = dm.get_user_cards(a.id)

            if query is None:
                res = user_cards
            else:
                for x in user_cards:
                    if query == str(u.cards_dict(x[2], x[1])["cost"]):
                        res.append(x)

        if not res:
            await ctx.send(f"{ctx.author.mention}, nothing matched your search!")
            return
        elif len(res) <= (page - 1) * p_len:
            await ctx.send(f"{ctx.author.mention}, you don't have any cards on page {page}!")
            return

        all_cards = []

        for x in res[(page - 1) * p_len:(page - 1) * p_len + p_len]:
            card = f"[{u.rarity_cost(x[1])}] **{x[1]}**, " \
                   f"lv: **{x[2]}**, id: `{x[0]}` "
            if x[0] in deck_ids:
                card = f"**>**{card}"
            all_cards.append(card)

        embed = discord.Embed(
            title="Results",
            description="\n".join(all_cards),
            color=discord.Color.gold()
        )

        show_start = (page - 1) * p_len + 1
        show_end = min(show_start + 14, len(res))
        embed.set_footer(
            text=f"{show_start}-{show_end}/{len(res)} cards displayed in page {page}"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="links",
        description="Displays an embed containing some official bot info.",
        aliases=["invite", "support", "guild", "supports", "link", "join"]
    )
    async def links(self, ctx: Context) -> None:
        """Displays an embed containing some official bot info."""
        embed = discord.Embed(title="Official Links", description=None, color=discord.Color.green())
        embed.add_field(
            name="Bot Invite",
            value=f"[Link](https://discordapp.com/oauth2/authorize?&client_id={self.bot.config['application_id']}&scope=bot+applications.commands&permissions={self.bot.config['permissions']})"
        )
        embed.add_field(
            name="Official Server",
            value="[Link](https://discord.gg/w2CkRtkj57)"
        )
        embed.add_field(
            name="Official Wiki",
            value="[Link](https://discord-adventurers-bot.fandom.com)"
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Stats(bot))
