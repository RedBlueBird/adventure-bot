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
    async def profile(self, ctx: Context, member: discord.Member = None) -> None:
        """Check a player's general information."""

        if member is None:
            member = ctx.message.author

        if not dm.is_registered(member.id):
            await ctx.send(f"{ctx.message.author.mention}, that user isn't registered!")
            return

        user_premium_date = dm.get_user_premium(member.id)
        user_id = dm.get_user_id(member.id)
        user_level = dm.get_user_level(member.id)
        user_exp = dm.get_user_exp(member.id)
        user_coin = dm.get_user_coin(member.id)
        user_gem = dm.get_user_gem(member.id)
        user_token = dm.get_user_token(member.id)
        user_medal = dm.get_user_gem(member.id)
        user_streak = dm.get_user_streak(member.id)
        user_daily = dm.get_user_daily(member.id)
        user_quest = dm.get_user_quest(member.id)
        user_badge = dm.get_user_badge(member.id)
        user_register_date = dm.get_user_register_date(member.id)

        if user_premium_date > dt.datetime.today():
            description_msg = f"14 \n{u.ICON['timer']}**ᴘʀᴇᴍɪᴜᴍ**: " \
                              f"{(user_premium_date - dt.datetime.today()).days} days remaining\n"
            tickets = "10"
        else:
            description_msg = "7 \n"
            tickets = "5"

        tick_msg = ""
        if user_level >= 4:
            tick_msg = f"{u.ICON['tick']}**Raid Tickets: **{dm.get_user_ticket(member.id)}/{tickets}"

        descr = f"```{dm.queues[str(member.id)]}```\n" if str(member.id) in dm.queues else None
        embed = discord.Embed(
            title=f"{member.display_name}'s profile:",
            description=descr,
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=member.avatar.url)

        hp = round((100 * u.SCALE[1] ** math.floor(user_level / 2)) * u.SCALE[0])
        if user_level < 30:
            embed.add_field(
                name=f"Current Level: {user_level}",
                value=f"{u.ICON['exp']} {user_exp}/{math.floor(int((user_level ** 2) * 40 + 60))}\n"
                      f"{u.ICON['hp']} {hp}",
                inline=False
            )
        else:
            embed.add_field(
                name=f"Max Level: {user_level}",
                value=f"{u.ICON['exp']} {user_exp}\n"
                      f"{u.ICON['hp']} {hp}",
                inline=False
            )

        dts = "Right now!" if user_daily.date() != dt.date.today() else u.remain_time()
        embed.add_field(
            name="Currency: ",
            value=f"{u.ICON['coin']}**Golden Coins: **{user_coin}\n"
                  f"{u.ICON['gem']}**Shiny Gems: **{user_gem}\n"
                  f"{u.ICON['token']}**Confetti: **{user_token}\n"
                  f"{u.ICON['medal']}**Medals: **{user_medal}\n"
                  f"{tick_msg}",
            inline=False
        )

        embed.add_field(
            name="Times: ",
            value=f"{u.ICON['streak']}**Current daily streak: **{user_streak}/" +
                  description_msg +
                  f"{u.ICON['timer']}**Next daily: **{dts} \n"
                  f"{u.ICON['timer']}**Next quest: "
                  f"**{u.time_converter(int(user_quest.split(',')[-1]) - int(times.time()))}",
            inline=False
        )

        if user_badge != 2 ** 30:
            badges = ["beta b", "pro b", "art b", "egg b", "fbi b", "for b"]
            owned_badges = []
            for i in range(29):
                if user_badge % 2 == 1:
                    owned_badges.append(u.ICON[badges[i]])
                user_badge = user_badge >> 1
            embed.add_field(name="Badges: ", value=" ".join(owned_badges))

        """
        embed.add_field(
            name="Personal Best: ",
            value=f"Traveled {profile_info[10]} Meters in one Adventure.",
            inline=False
        )
        """

        embed.set_footer(text=f"Player ID: {user_id}, Register Date: {user_register_date}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="quests",
        description="Displays all current quests of a user.",
        aliases=["q"]
    )
    async def quests(self, ctx: Context, user: discord.User = None) -> None:
        """Displays all current quests of a user."""

        if user is None:
            user = ctx.message.author
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)
        if not dm.is_registered(member.id):
            await ctx.send(f"{ctx.message.author.mention}, that's an invalid user id!")
            return

        user_quest = dm.get_user_quest(member.id)
        user_premium_date = dm.get_user_premium(member.id)

        quests = user_quest.split(",")
        is_premium = False
        if user_premium_date > dt.datetime.today():
            is_premium = True

        if (len(quests) < 4 and is_premium == False) or (len(quests) < 5 and is_premium == True):
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

                dm.set_user_quest(','.join(quests), member.id)

        if len(quests) == 1:
            embed = discord.Embed(
                title=f"{member.display_name}'s Quests:",
                description="You don't have any quests.\nCome back later for more!",
                color=discord.Color.green()
            )
        else:
            bad = 4 + is_premium
            if len(quests) == bad:
                embed = discord.Embed(
                    title=f"{member.display_name}'s Quests:",
                    description=f"You can't have more than {bad - 1} quests active!",
                    color=discord.Color.gold()
                )
            else:
                embed = discord.Embed(
                    title=f"{member.display_name}'s Quests:",
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

        embed.set_thumbnail(url=member.avatar.url)
        time_left = u.time_converter(int(quests[-1]) - int(times.time()))
        if time_left != "Right Now":
            embed.set_footer(text=f"There's {time_left} left till a new quest")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="inventory",
        description="Displays all the cards in a member's inventory in the form of an embed.",
        aliases=["card", "i", "inv"]
    )
    async def inventory(self, ctx: Context, page: int = 1, user: discord.User = None) -> None:
        """
        Displays all the cards in a member's inventory in the form of an embed.

        :param page: The page of cards to display
        :param user: The user whose cards to display
        """

        if user is None:
            user = ctx.message.author
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)
        if not dm.is_registered(member.id):
            await ctx.send(f"{ctx.message.author.mention}, that's an invalid user id!")
            return

        user_order = dm.get_user_order(member.id)
        user_slot = dm.get_user_deck_slot(member.id)
        user_deck = dm.get_user_deck(user_slot, user_order, member.id)
        deck_ids = [card[0] for card in user_deck]
        user_cards = dm.get_user_cards(member.id, user_order, start=(page - 1) * 15, length=15)
        user_cards_count = dm.get_user_cards_count(member.id)

        if len(user_cards) == 0:
            await ctx.send(f"{ctx.message.author.mention}, you don't have any cards on page {page}!")
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
            title=f"{member.display_name}'s cards:",
            description="\n".join(all_cards),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=member.avatar.url)
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
        description_param = "", ""
        if lb_type.lower() in ["levels", "level", "exps", "exp", "l", "e"]:
            lb_type = "XP"
            description_param = "• Level: {player[2]}, Exp: {player[3]}"
        elif lb_type.lower() in ["coins", "golden_coins", "goldencoins", "goldencoins", "coin", "gc", "c"]:
            lb_type = "Golden Coins"
            description_param = "• Golden Coins: {player[2]}, Shiny Gems: {player[3]}"
        elif lb_type.lower() in ["shiny_gems", "shinygems", "shiny_gem", "shinygem", "gems", "gem", "g", "sg"]:
            lb_type = "Shiny Gems"
            description_param = "• Shiny Gems: {player[2]}, Golden Coins: {player[3]}"
        elif lb_type.lower() in ["medals", "medal", "m"]:
            lb_type = "Medals"
            description_param = "• Medals: {player[2]}"
        elif lb_type.lower() in ["tokens", "t", "event_tokens", "token"]:
            lb_type = "Tokens"
            description_param = "• Tokens: {player[2]}"
        else:
            embed = discord.Embed(
                title="Leaderboards the bot can show",
                description=f"`{u.PREF}leaderboard (leaderboard_type)`",
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
            description = eval("f'" + description_param + "'")
            if str(player[1]) == str(ctx.message.author.id):
                description = f"__{description}__"
            selected_players.append("".join([name, description + "\n"]))

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
    async def deck(self, ctx: Context, slot: int = 0, user: discord.User = None) -> None:
        """
        Displays the deck in the member's current deck slot
        :param slot: The deck slot to search.
        :param user: The user whose deck slots to search.
        """

        if user is None:
            user = ctx.message.author
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)
        if not dm.is_registered(member.id):
            await ctx.send(f"{ctx.message.author.mention}, that's an invalid user id!")
            return

        if not 0 <= slot <= 6:
            await ctx.send("The deck slot number must between 1-6!")
            return

        user_order = dm.get_user_order(member.id)
        user_slot = dm.get_user_deck_slot(member.id)
        user_level = dm.get_user_level(member.id)
        slot = slot if slot != 0 else user_slot

        deck_slots = {1: 0, 2: 0, 3: 6, 4: 15, 5: 21, 6: 29}
        if user_level < deck_slots[slot]:
            await ctx.send("You don't have access to that deck slot yet!")
            return

        user_deck = dm.get_user_deck(slot, user_order, member.id)
        all_cards = []
        total_energy_cost = 0
        for x in user_deck:
            card = f"[{u.rarity_cost(x[1])}] **{x[1]}**, lv: **{x[2]}**, id: `{x[0]}` "
            if slot == user_slot:
                card = f"**>**{card}"
            all_cards.append(card)
            total_energy_cost += u.cards_dict(x[2], x[1])["cost"]

        mod_msg = "" if slot == user_slot else f"\n`{u.PREF}select {slot}` to modify this deck"
        embed = discord.Embed(
            title=f"{member.display_name}'s Deck #{slot}:",
            description=f"`{u.PREF}decklist` to display all your decks{mod_msg}\n\n" +
                        "\n".join(all_cards),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=member.avatar.url)
        if not user_deck:
            embed.add_field(
                name="You don't have any cards in your deck!",
                value=f"`{u.PREF}add (card_id)` to start adding cards!"
            )
        if len(user_deck) != 12:
            embed.set_footer(text=f"You need {12 - len(user_deck)} more cards needed to complete this deck")
        else:
            embed.set_footer(text=f"Average energy cost: {round(total_energy_cost * 100 / 12) / 100}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="decklist",
        description="Displays all decks of a user."
    )
    async def decklist(self, ctx: Context, user: discord.User = None):
        if user is None:
            user = ctx.message.author
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)
        if not dm.is_registered(member.id):
            await ctx.send(f"{ctx.message.author.mention}, that's an invalid user id!")
            return

        user_level = dm.get_user_level(member.id)
        user_slot = dm.get_user_deck_slot(member.id)
        deck_slots = {1: 0, 2: 0, 3: 6, 4: 15, 5: 21, 6: 29}

        embed = discord.Embed(
            title=f"{member.display_name}'s decks",
            description=f"`{u.PREF}deck #` to view a specific deck",
            color=discord.Color.gold()
        )

        for i in range(6):
            name = f"**Deck {i + 1}**"
            if user_slot == i + 1:
                name += " - selected"

            if user_level < deck_slots[i + 1]:
                card_info = f"Unlocked at level {deck_slots[i + 1]}"
            else:
                deck_lens = dm.get_user_deck_count(i + 1, member.id)
                card_info = f"{deck_lens}/12 cards"

            embed.add_field(name=name, value=card_info, inline=False)

        embed.set_thumbnail(url=member.avatar.url)
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
            # if card_info["requirement"] != "None":
            # embed.add_field(name="Requirements: ", value=card_info["requirement"], inline=False)
            embed.add_field(name="Brief: ", value=card_info["brief"], inline=False)
            """
            if "journal" in card_info:
                embed.add_field(name="Scout's Journal: ", value="*" + card_info["journal"] + "*", inline=False)
            embed.set_thumbnail(url=ctx.message.author.avatar.url)
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
            embed.set_thumbnail(url=ctx.message.author.avatar.url)
            """

        elif type_ == "item":
            item_info = u.items_dict(" ".join(name.lower().split("_")))
            info_str = [
                f"**Name:** {item_info['name']}",
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
            embed.set_thumbnail(url=ctx.message.author.avatar.url)
            """
            embed.set_image(
                url=f"https://cdn.discordapp.com/emojis/{u.ICON[item_info['name'].lower()][len(''.join(item_info['name'].split(' '))) + 3:-1]}.png")

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
        a = ctx.message.author
        if not 1 <= page <= 3:
            embed = discord.Embed(title="Card Shop", description=None, color=discord.Color.gold())
            embed.add_field(name="Daily Deals", value="**»** page 1", inline=False)
            embed.add_field(name="Card Packs", value="**»** page 2", inline=False)
            embed.add_field(name="Currency", value="**»** page 3", inline=False)
            embed.set_footer(text=f"{u.PREF}shop (page_number)")
            await ctx.send(embed=embed)
            return

        user_coin = dm.get_user_coin(a.id)
        user_gem = dm.get_user_gem(a.id)
        user_token = dm.get_user_token(a.id)

        embed = None
        if page == 1:
            user_deals = dm.get_user_deals(a.id).split(",")
            embed = discord.Embed(
                title="Shop - Daily Deals:",
                description=f"{u.ICON['coin']} **{user_coin}** {u.ICON['gem']} **{user_gem}**",
                color=discord.Color.gold()
            )  # {u.icon['token']} **{user_token}**")

            for x in range(len(user_deals)):
                card = user_deals[x].split('.')
                print(user_deals)
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
            embed.set_footer(text=f"Wait {u.remain_time()} or {u.PREF}buy r to refresh shop")

        elif page == 2:
            embed = discord.Embed(
                title="Shop - Card Packs:",
                description=f"{u.ICON['coin']} **{user_coin}** {u.ICON['gem']} "
                            f"**{user_gem}** {u.ICON['token']} **{user_token}**",
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
                description=f"{u.ICON['coin']} **{user_coin}** {u.ICON['gem']} **{user_gem}**",
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

        page = max(page, 1)

        member = ctx.message.author
        user_order = dm.get_user_order(member.id)
        user_slot = dm.get_user_deck_slot(member.id)
        user_deck = dm.get_user_deck(user_slot, user_order, member.id)
        deck_ids = [card[0] for card in user_deck]

        res = []
        search_type = search_type.lower()
        if search_type == "level":
            additional = "" if query is None else f"AND card_level = {query}"
            res = dm.get_user_cards(member.id, user_order, additional)

        elif search_type == "name":
            res = dm.get_user_cards(
                member.id, user_order,
                "" if query is None else f"AND card_name LIKE '%{query}%'"
            )

        elif search_type == "rarity":
            user_cards = dm.get_user_cards(member.id, user_order)
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
            user_cards = dm.get_user_cards(member.id, user_order)

            if query is None:
                res = user_cards
            else:
                for x in user_cards:
                    if query == str(u.cards_dict(x[2], x[1])["cost"]):
                        res.append(x)

        if not res:
            await ctx.send(f"{ctx.message.author.mention}, nothing matched your search!")
            return
        elif len(res) <= (page - 1) * 15:
            await ctx.send(f"{ctx.message.author.mention}, you don't have any cards on page {page}!")
            return

        all_cards = []

        for x in res[(page - 1) * 15:(page - 1) * 15 + 15]:
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

        show_start = (page - 1) * 15 + 1
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
        embed = discord.Embed(title="[SUPPORT]", description=None, color=discord.Color.green())
        embed.add_field(
            name="Bot Invite",
            value=f"[Link](https://discordapp.com/oauth2/authorize?&client_id={self.bot.config['application_id']}&scope=bot+applications.commands&permissions={self.bot.config['permissions']})",
            inline=False
        )
        embed.add_field(
            name="Official Server",
            value="[Link](https://discord.gg/w2CkRtkj57)",
            inline=False
        )
        embed.add_field(
            name="Official Wiki",
            value="[Link](https://discord-adventurers-bot.fandom.com)",
            inline=False
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Stats(bot))
