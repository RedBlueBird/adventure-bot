import random
import math
import time as times
import datetime as dt

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db_manager as dm
from helpers import util as u
from helpers import checks


class Stats(commands.Cog, name="informational"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="profile",
        description="Check a player's general information.",
        aliases=["p", "pro"]
    )
    async def profile(self, ctx: Context, user: discord.User = None) -> None:
        """Check a player's general information."""

        if user is None:
            user = ctx.message.author
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)

        dm.cur.execute(f"SELECT * FROM playersinfo WHERE userid = '{member.id}'")
        prof = dm.cur.fetchall()  # short for profile

        if not prof:
            await ctx.send(f"{ctx.message.author.mention}, that's an invalid user id!")
            return
        else:
            prof = prof[0]
            dm.cur.execute(f"SELECT * from playersachivements WHERE userid = '{member.id}'")
            achivement_info = dm.cur.fetchall()[0]

        if prof[14].split(",")[0] == "1":
            time = u.time_converter(int(prof[14].split(',')[1]) - int(times.time()))
            description_msg = f"14 \n{u.ICONS['timer']}**ᴘʀᴇᴍɪᴜᴍ**: {time} \n"
            tickets = "10"
        else:
            description_msg = "7 \n"
            tickets = "5"

        tick_msg = "" if prof[3] < 4 else f"{u.ICONS['tick']}**Raid Tickets: **{prof[9]}/{tickets}"

        embed_descr = f"```{dm.queues[str(member.id)]}``` \n" if str(member.id) in dm.queues else None
        embed = discord.Embed(
            title=member.display_name + "'s profile:",
            description=embed_descr,
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=member.avatar.url)

        if int(prof[3]) < 30:
            embed.add_field(
                name=f"Current Level: {prof[3]}",
                value=f"{u.ICONS['exp']} {prof[4]}/{math.floor(int((prof[3] ** 2) * 40 + 60))}\n"
                      f"{u.ICONS['hp']} {round((100 * u.SCALE[1] ** math.floor(prof[3] / 2)) * u.SCALE[0])}",
                inline=False
            )
        else:
            embed.add_field(
                name=f"Max Level: {prof[3]}",
                value=f"{u.ICONS['exp']} {prof[4]}\n"
                      f"{u.ICONS['hp']} {round((100 * u.SCALE[1] ** math.floor(prof[3] / 2)) * u.SCALE[0])}",
                inline=False
            )

        if prof[10] != str(dt.date.today()):
            dts = "Right Now!"
        else:
            dts = u.remain_time()
        embed.add_field(
            name="Currency: ",
            value=f"{u.ICONS['coin']}**Golden Coins: **{prof[5]}\n"
                  f"{u.ICONS['gem']}**Shiny Gems: **{prof[6]}\n"
                  f"{u.ICONS['token']}**Confetti: **{prof[7]}\n"
                  f"{u.ICONS['medal']}**Medals: **{prof[8]}\n"
                  f"{tick_msg}",
            inline=False
        )
        embed.add_field(
            name="Times: ",
            value=f"{u.ICONS['streak']}**Current daily streak: **{int(prof[13])}/" +
                  description_msg +
                  f"{u.ICONS['timer']}**Next daily: **{dts} \n"
                  f"{u.ICONS['timer']}**Next quest: "
                  f"**{u.time_converter(int(prof[15].split(',')[-1]) - int(times.time()))}",
            inline=False
        )

        if achivement_info[3] != "0000000000000000000000000000000000000000":
            badges = ["beta b", "pro b", "art b", "egg b", "fbi b", "for b"]
            owned_badges = []
            for i, value in enumerate(achivement_info[3]):
                if value == "1":
                    owned_badges.append(u.ICONS[badges[i]])
            embed.add_field(name="Badges: ", value=" ".join(owned_badges))

        """
        embed.add_field(
            name="Personal Best: ",
            value=f"Traveled {profile_info[10]} Meters in one Adventure.",
            inline=False
        )
        """

        embed.set_footer(text=f"Player ID: {prof[0]}, Register Date: {achivement_info[2]}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="quests",
        description="Displays all current quests of a user.",
        aliases=["quest", "que", "qu"]
    )
    async def quests(self, ctx: Context, user: discord.User = None) -> None:
        """Displays all current quests of a user."""

        user = ctx.message.author if user is None else user
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)

        dm.cur.execute(f"select quests, user_identity from playersinfo where userid = '{member.id}'")
        result = dm.cur.fetchall()[0]
        quests = result[0].split(",")
        is_premium = int(result[1].split(",")[0])

        if (len(quests) < 4 and is_premium == 0) or (len(quests) < 5 and is_premium == 1):
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

                dm.cur.execute(f"UPDATE playersinfo SET quests = '{','.join(quests)}' WHERE userid = '{member.id}'")
                dm.db.commit()

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
                          f"Reward: **{''.join(quest[1::2])} {quest[4]} {u.ICONS['exp']}**",
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

        uid = ctx.message.author.id if user is None else user.id
        member = ctx.guild.get_member(uid) or await ctx.guild.fetch_member(uid)

        dm.cur.execute(f"SELECT id FROM playersinfo WHERE userid = '{member.id}'")
        if not dm.cur.fetchall():
            await ctx.send(f"{ctx.message.author.mention}, the user id is invalid!")
            return

        dm.cur.execute(f"SELECT inventory_order, deck_slot FROM playersinfo WHERE userid = '{uid}'")
        result = dm.cur.fetchall()[0]
        order = result[0]
        db_deck = f"deck{result[1]}"
        dm.cur.execute(f"SELECT {db_deck} FROM playersachivements WHERE userid = '{uid}'")
        decks = dm.cur.fetchall()[0]
        decks = [int(k) for i in decks for k in i.split(",")]

        if order == 1:
            order_by = "card_level, card_name"
        elif order in [2, 7, 8, 9, 10]:
            order_by = "card_level desc, card_name"
        elif order == 3:
            order_by = "card_name"
        elif order == 4:
            order_by = "card_name desc"
        elif order == 5:
            order_by = "id, card_name"
        elif order == 6:
            order_by = "id desc, card_name"
        dm.cur.execute(f"SELECT * FROM cardsinfo WHERE owned_user = '{member.id}' ORDER BY {order_by}")

        result = dm.cur.fetchall()
        if order in [7, 8]:
            result = u.order_by_rarity(result, 1)
            result = u.order_by_cost(result, order - 7)
        if order in [9, 10]:
            result = u.order_by_cost(result, 1)
            result = u.order_by_rarity(result, order - 9)

        if len(result) < (page - 1) * 15:
            await ctx.send(f"{ctx.message.author.mention}, there's no cards here!")
            return

        result = result[(page - 1) * 15:(page - 1) * 15 + 15]
        dm.cur.execute(f"SELECT * FROM cardsinfo WHERE owned_user = '{member.id}'")
        card_num = len(dm.cur.fetchall())

        if card_num <= (page - 1) * 15:
            await ctx.send(f"{ctx.message.author.mention}, you don't have any cards on page {page}!")
            return

        all_cards = []

        def card_properties(cardinfo):
            if cardinfo[0] in decks:
                all_cards.append(
                    f"**>**[{u.rarity_cost(cardinfo[3])}] **{cardinfo[3]}**, "
                    f"lv: **{cardinfo[4]}**, id: `{cardinfo[0]}` "
                )
            else:
                all_cards.append(
                    f"[{u.rarity_cost(cardinfo[3])}] **{cardinfo[3]}**, "
                    f"lv: **{cardinfo[4]}**, id: `{cardinfo[0]}` "
                )

        for x in result:
            card_properties(x)

        embed = discord.Embed(
            title=f"{member.display_name}'s cards:",
            description="\n".join(all_cards),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=member.avatar.url)

        show_start = (page - 1) * 15 + 1
        show_end = card_num if page * 15 > card_num else page * 15
        embed.set_footer(text=f"{show_start}-{show_end}/{card_num} cards displayed in page {page}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="leaderboard",
        description="Displays the world's top players.",
        aliases=["lb", "leaderboards", "lbs"]
    )
    async def leaderboard(self, ctx: Context, lb_type: str = "") -> None:
        """
        Displays the world's top players.
        :param lb_type: The type of leaderboard to display
        """

        lb_type = lb_type.lower()

        selected_players = []
        lim = 10
        if lb_type.lower() in ["levels", "level", "exps", "exp", "l", "e"]:
            dm.cur.execute(
                f"SELECT id, userid, level, exps FROM playersinfo ORDER BY level DESC, exps DESC LIMIT {lim}"
            )
            all_players = dm.cur.fetchall()
            for v, p in enumerate(all_players):
                y = await self.bot.fetch_user(str(p[1]))
                player = f"**[{v + 1}]**. **{y}** \n• XP: {p[2]}\n"
                if str(p[1]) == str(ctx.message.author.id):
                    player = f"_{player}_"
                selected_players.append(player)

            embed = discord.Embed(
                title="Leaderboard - most XP",
                description="".join(selected_players),
                color=discord.Color.gold()
            )

        elif lb_type.lower() in ["coins", "golden_coins", "goldencoins", "goldencoins", "coin", "gc", "c"]:
            dm.cur.execute(
                f"SELECT id, userid, coins, gems FROM playersinfo ORDER BY coins DESC, gems DESC LIMIT {lim}"
            )
            all_players = dm.cur.fetchall()
            for v, p in enumerate(all_players):
                y = await self.bot.fetch_user(str(p[1]))
                player = f"**[{v + 1}]**. **{y}** \n• Golden Coins: {p[2]}, Shiny Gems: {p[3]}\n"
                if str(p[1]) == str(ctx.message.author.id):
                    player = f"_{player}_"
                selected_players.append(player)

            embed = discord.Embed(
                title="Leaderboard - most golden coins",
                description="".join(selected_players),
                color=discord.Color.gold()
            )

        elif lb_type.lower() in ["shiny_gems", "shinygems", "shiny_gem", "shinygem", "gems", "gem", "g", "sg"]:
            dm.cur.execute(
                f"SELECT id, userid, gems, coins FROM playersinfo ORDER BY gems DESC, coins DESC LIMIT {lim}"
            )
            all_players = dm.cur.fetchall()
            for v, p in enumerate(all_players):
                y = await self.bot.fetch_user(str(p[1]))
                player = f"**[{v + 1}]**. **{y}** \n• Shiny Gems: {p[2]}, Golden Coins: {p[3]}\n"
                if str(p[1]) == str(ctx.message.author.id):
                    player = f"_{player}_"
                selected_players.append(player)

            embed = discord.Embed(
                title="Leaderboard - most shiny gems",
                description="".join(selected_players),
                color=discord.Color.gold()
            )

        elif lb_type.lower() in ["medals", "medal", "m"]:
            dm.cur.execute(f"SELECT id, userid, medals FROM playersinfo ORDER BY medals DESC LIMIT {lim}")
            all_players = dm.cur.fetchall()
            for v, p in enumerate(all_players):
                y = await self.bot.fetch_user(str(p[1]))
                player = f"**[{v + 1}]**. **{y}** \n• Medals: {p[2]}\n"
                if str(p[1]) == str(ctx.message.author.id):
                    player = f"_{player}_"
                selected_players.append(player)

            embed = discord.Embed(
                title="Leaderboard - most medals",
                description="".join(selected_players),
                color=discord.Color.gold()
            )

        elif lb_type.lower() in ["tokens", "t", "event_tokens", "token"]:
            dm.cur.execute(f"SELECT id, userid, event_token FROM playersinfo ORDER BY event_token DESC LIMIT {lim}")
            all_players = dm.cur.fetchall()
            for v, p in enumerate(all_players):
                y = await self.bot.fetch_user(str(p[1]))
                player = f"**[{v + 1}]**. **{y}** \n• Tokens: {p[2]}\n"
                if str(p[1]) == str(ctx.message.author.id):
                    player = f"_{player}_"
                selected_players.append(player)

            embed = discord.Embed(
                title="Leaderboard - most tokens",
                description="".join(selected_players),
                color=discord.Color.gold()
            )

        else:
            embed = discord.Embed(
                title="Leaderboards the bot can show",
                description=f"`{u.PREF}leaderboard (leaderboard_type)`",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Players with the most XP",
                value=f"`{u.PREF}leaderboard levels`", inline=False
            )
            embed.add_field(
                name="Players with the most golden coins",
                value=f"`{u.PREF}leaderboard coins`",
                inline=False
            )
            embed.add_field(
                name="Players with the most shiny gems",
                value=f"`{u.PREF}leaderboard gems`",
                inline=False
            )
            embed.add_field(
                name="Players with the most medals",
                value=f"`{u.PREF}leaderboard medals`",
                inline=False
            )
            embed.add_field(
                name="Players with the most tokens",
                value=f"`{u.PREF}leaderbord tokens`",
                inline=False
            )
            embed.set_footer(text=f"Shows the top {lim} players only.")
            await ctx.send(embed=embed)

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="deck",
        description="Displays the deck in the member's current deck slot",
        aliases=["decks"]
    )
    async def deck(self, ctx: Context, slot: int = -1, user: discord.User = None) -> None:
        """
        Displays the deck in the member's current deck slot
        :param slot: The deck slot to search.
        :param user: The user whose deck slots to search.
        """
        user = ctx.message.author if user is None else user
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)

        if not 1 <= slot <= 6:
            await ctx.send("The deck slot number must between 1-6!")
            return

        dm.cur.execute(f"select inventory_order from playersinfo where userid = '{ctx.message.author.id}'")
        order = dm.cur.fetchall()[0][0]
        dm.cur.execute(f"select level, deck_slot from playersinfo where userid = '{member.id}'")
        result = dm.cur.fetchall()[0]
        level = result[0]
        selected_slot = result[1]
        deck_slots = {1: 0, 2: 0, 3: 6, 4: 15, 5: 21, 6: 29}
        slot = slot if slot != 0 else selected_slot

        if level < deck_slots[slot]:
            await ctx.send("You don't have access to that deck slot yet!")
            return

        db_deck = f"deck{slot}"
        dm.cur.execute(f"select {db_deck} from playersachivements where userid = '{member.id}'")
        decks = dm.cur.fetchall()[0][0].split(",")
        decks = decks if decks != ["0"] else [0]

        if order == 1:
            lookup = "card_level, card_name"
        elif order in [2, 7, 8, 9, 10]:
            lookup = "card_level desc, card_name"
        elif order == 3:
            lookup = "card_name"
        elif order == 4:
            lookup = "card_name desc"
        elif order == 5:
            lookup = "id, card_name"
        elif order == 6:
            lookup = "id desc, card_name"

        dm.cur.execute(
            f"select * from cardsinfo where owned_user = {member.id} and id in ({str(decks)[1:-1]}) ORDER BY {lookup}")
        result = dm.cur.fetchall()
        if order in [7, 8]:
            result = u.order_by_rarity(result, 1)
            result = u.order_by_cost(result, order - 7)
        if order in [9, 10]:
            result = u.order_by_cost(result, 1)
            result = u.order_by_rarity(result, order - 9)

        if not result:
            dm.cur.execute(f"select * from cardsinfo where owned_user = '{member.id}'")
            if not dm.cur.fetchall():
                await ctx.send(f"{ctx.message.author.mention}, that user ID's invalid!")
                return

        all_cards = []
        total_energy_cost = 0
        for x in result:
            card = f"[{u.rarity_cost(x[3])}] **{x[3]}**, lv: **{x[4]}**, id: `{x[0]}` "
            if slot == selected_slot:
                card = f"**>**{card}"
            all_cards.append(card)
            total_energy_cost += u.cards_dict(x[4], x[3])["cost"]

        mod_msg = "" if slot == selected_slot else f"\n`{u.PREF}select {slot}` to modify this deck"

        embed = discord.Embed(
            title=f"{member.display_name}'s Deck #{slot}:",
            description=f"`{u.PREF}deck list` to display all your decks{mod_msg}\n\n" +
                        "\n".join(all_cards),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=member.avatar.url)

        if not result:
            embed.add_field(
                name="You don't have any cards in your deck!",
                value=f"`{u.PREF}add (card_id)` to start adding cards!"
            )
        if len(result) != 12:
            embed.set_footer(text=f"You need {12 - len(result)} more cards needed to complete this deck")
        else:
            embed.set_footer(text=f"Average energy cost: {round(total_energy_cost * 100 / 12) / 100}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="decklist",
        description="Displays all decks of a user."
    )
    async def decklist(self, ctx: Context, user: discord.User = None):
        user = ctx.message.author if user is None else user
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)

        dm.cur.execute(f"select level, deck_slot from playersinfo where userid = '{member.id}'")
        result = dm.cur.fetchall()[0]
        level = result[0]
        selected_slot = result[1]
        deck_slots = {1: 0, 2: 0, 3: 6, 4: 15, 5: 21, 6: 29}

        deck_lens = []
        for i in range(6):
            db_deck = f"deck{i + 1}"
            dm.cur.execute(f"select {db_deck} from playersachivements where userid = '{member.id}'")
            deck = dm.cur.fetchall()[0][0].split(",")
            deck_lens.append(len(deck) if deck != ["0"] else 0)

        embed = discord.Embed(
            title=f"{member.display_name}'s decks",
            description=f"`{u.PREF}deck #` to view a specific deck",
            color=discord.Color.gold()
        )

        for i in range(6):
            name = f"**Deck {i + 1}**"
            if selected_slot == i + 1:
                name += " - selected"

            if level < deck_slots[i + 1]:
                card_info = f"Unlocked at level {deck_slots[i + 1]}"
            else:
                card_info = f"{deck_lens[i]}/12 cards"

            embed.add_field(name=name, value=card_info, inline=False)

        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="info",
        description="Looks up entities, from effects to mobs and displays an embed containing info about it.",
        aliases=["in", "ins", "ifs", "informations", "check"]
    )
    async def info(self, ctx: Context, dict_name: str, name: str, level: int = 1) -> None:
        """
        Looks up entities, from effects to mobs and displays an embed containing info about it.
        :param dict_name: The type of the thing which to look up (can be a card, mob, item, or effect)
        :param name: The name of the thing to look up
        :param level: The level of the thing for number crunching
        """

        rarity_translator = {
            "C": "Common", "R": "Rare", "E": "Epic", "EX": "Exclusive",
            "L": "Legendary", "M": "N/A", "NA": "N/A"
        }

        dict_name = dict_name.lower()
        if dict_name in ["card", "cards", "c", "ca"]:
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

        elif dict_name in ["monster", "mon", "mob", "mobs", "m"]:
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

        elif dict_name in ["item", "items", "ite", "it", "i", "object", "objects", "obj", "objec", "o"]:
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
                url=f"https://cdn.discordapp.com/emojis/{u.ICONS[item_info['name'].lower()][len(''.join(item_info['name'].split(' '))) + 3:-1]}.png")

        elif dict_name in ["effect", "effects", "eff", "ef", "e"]:
            fx_info = u.fx_dict(" ".join(name.lower().split("_")))
            embed = discord.Embed(title="Effect's info:", description=None, color=discord.Color.green())
            embed.add_field(name="Description: ", value=f"**Name:** {fx_info['name']}", inline=False)
            embed.add_field(name="Uses: ", value=fx_info["description"], inline=False)
            embed.set_image(
                url=f"https://cdn.discordapp.com/emojis/"
                    f"{u.CONVERT[fx_info['name'].lower()][4:-1]}.png"
            )

        else:
            await ctx.send(
                f"{ctx.message.author.mention}, the correct format for this command is "
                f"`{u.PREF}info (card/mob/item/effect) (name) (level)`!"
            )
            return

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="shop",
        description="The player can buy cards and other things here.",
        aliases=["shops"]
    )
    @checks.level_check(3)
    async def shop(self, ctx: Context, page: int = -1) -> None:
        """
        The player can buy cards and other things here.
        :param page: The page of the stop to display.
        """
        if not 1 <= page <= 3:
            embed = discord.Embed(title="Card Shop", description=None, color=discord.Color.gold())
            embed.add_field(name="Daily Deals", value="**»** page 1", inline=False)
            embed.add_field(name="Card Packs", value="**»** page 2", inline=False)
            embed.add_field(name="Currency", value="**»** page 3", inline=False)
            embed.set_footer(text=f"{u.PREF}shop (page_number)")
            await ctx.send(embed=embed)
            return

        dm.cur.execute(
            "select coins, gems, event_token from playersinfo where userid = " + str(ctx.message.author.id))
        currencies = dm.cur.fetchall()
        coins = currencies[0][0]
        gems = currencies[0][1]
        tokens = currencies[0][2]
        if page == 1:
            dm.cur.execute("select deals from playersinfo where userid = " + str(ctx.message.author.id))
            the_deals = dm.cur.fetchall()[0][0].split(",")
            embed = discord.Embed(
                title="Shop - Daily Deals:",
                description=f"{u.ICONS['coin']} **{coins}** {u.ICONS['gem']} **{gems}**",
                color=discord.Color.gold()
            )  # {u.icon['token']} **{tokens}**")

            def card_deal(the_card, place):
                card = the_card.split('.')
                if the_card[0] != "-":
                    cost = round(1.6 ** int(card[0]) * 50 * u.price_factor(card[1]))
                    embed.add_field(
                        name=f"**[{u.rarity_cost(card[1])}] {card[1]} lv: {card[0]}**",
                        value=f"Cost: **{cost}** {u.ICONS['coin']} \n`{u.PREF}buy {place}`"
                    )
                else:
                    embed.add_field(
                        name=f"**[{u.rarity_cost(card[1])}] {card[1]} lv: {card[0][1:]}**",
                        value="Purchased"
                    )

            for x in range(len(the_deals)):
                card_deal(the_deals[x], x + 1)
            embed.set_footer(text=f"Wait {u.remain_time()} or {u.PREF}buy r to refresh shop")

        elif page == 2:
            embed = discord.Embed(
                title="Shop - Card Packs:",
                description=f"{u.ICONS['coin']} **{coins}** {u.ICONS['gem']} "
                            f"**{gems}** {u.ICONS['token']} **{tokens}**",
                color=discord.Color.green()
            )

            packs = [
                {
                    "name": "**Basic Pack**",
                    "value": f"Cost: **3** {u.ICONS['gem']} \n"
                             "• contains 3 (lv 4-10) cards \n"
                             f"`{u.PREF}buy basic`"
                },
                {
                    "name": "**Fire Pack**",
                    "value": f"Cost: **5** {u.ICONS['gem']} \n"
                             "• contains 4 (lv 4-10) cards with a \nhigher chance of fire cards \n"
                             f"`{u.PREF}buy fire`"
                },
                {
                    "name": "**Evil Pack**",
                    "value": f"Cost: **5** {u.ICONS['gem']} \n"
                             "• contains 4 (lv 4-10) cards with a \nhigher chance of curse cards \n"
                             f"`{u.PREF}buy evil`"
                },
                {
                    "name": "**Electric Pack**",
                    "value": f"Cost: **5** {u.ICONS['gem']} \n"
                             "• contains 4 (lv 4-10) cards with a \nhigher chance of electric cards \n"
                             f"`{u.PREF}buy electric`"
                },
                {
                    "name": "**Defensive Pack**",
                    "value": f"Cost: **5** {u.ICONS['gem']} \n"
                             "• contains 4 (lv 4-10) cards with a \nhigher chance of defense cards \n"
                             f"`{u.PREF}buy defensive`"
                },
                {
                    "name": "**Pro Pack**",
                    "value": f"Cost: **24** {u.ICONS['gem']} \n"
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
                description=f"{u.ICONS['coin']} **{coins}** {u.ICONS['gem']} **{gems}**",
                color=discord.Color.green()
            )  # {u.icon['token']} **{tokens}**")

            currency_offers = [
                {"name": "**1000 Golden Coins**", "value": f"Cost: **3** {u.ICONS['gem']} \n`{u.PREF}buy gc1`"},
                {"name": "**2250 Golden Coins**", "value": f"Cost: **6** {u.ICONS['gem']} \n`{u.PREF}buy gc2`"},
                {"name": "**11000 Golden Coins**", "value": f"Cost: **24** {u.ICONS['gem']} \n`{u.PREF}buy gc3`"},
                {"name": "**1 Raid Ticket**", "value": f"Cost: **2** {u.ICONS['gem']} \n`{u.PREF}buy rt1`"},
                {"name": "**2 Raid Ticket**", "value": f"Cost: **4** {u.ICONS['gem']} \n`{u.PREF}buy rt2`"},
                {"name": "**3 Raid Ticket**", "value": f"Cost: **6** {u.ICONS['gem']} \n`{u.PREF}buy rt3`"}
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
            search_type="nothing", filter_="nothing",
            page: str = "bruh moment"
    ) -> None:
        """
        Searches your cards according to a query.
        :param search_type: What to search by
        :param filter_: The actual search query that the bot will search by
        :param page: The page of the card results to go to.
        """

        page = int(page) if page.isdigit() else 1
        page = 1 if page <= 0 else page

        a_id = str(ctx.message.author.id)
        dm.cur.execute(f"select inventory_order, deck_slot from playersinfo where userid = '{a_id}'")
        result = list(dm.cur.fetchall())[0]
        order = result[0]
        assert 1 <= order <= 6
        deck_slot = result[1]
        db_deck = f"deck{deck_slot}"
        dm.cur.execute(f"select {db_deck} from playersachivements where userid = '{a_id}'")
        decks = [int(k) for i in dm.cur.fetchall()[0] for k in i.split(",")]

        orders = ""
        if order == 1:
            orders = " ORDER BY card_level, card_name"
        elif order in [2, 7, 8, 9, 10]:
            orders = " ORDER BY card_level desc, card_name"
        elif order == 3:
            orders = " ORDER BY card_name"
        elif order == 4:
            orders = " ORDER BY card_name desc"
        elif order == 5:
            orders = " ORDER BY id, card_name"
        elif order == 6:
            orders = " ORDER BY id desc, card_name"

        search_type = search_type.lower()
        if search_type in ["level", "lvl", "l"]:
            dm.cur.execute(f"select * from cardsinfo where owned_user = {a_id} and card_level = {filter_}{orders}")
            total_cards = list(dm.cur.fetchall())

        elif search_type in ["name", "na", "n"]:
            dm.cur.execute(f"select * from cardsinfo where owned_user = {a_id} and card_name like '" +
                           " ".join(filter_.split("_")) + "%'" + orders)
            total_cards = list(dm.cur.fetchall())

        elif search_type in ["rarity", "rare", "ra", "r"]:
            dm.cur.execute(f"select * from cardsinfo where owned_user = {a_id}{orders}")
            all_cards = list(dm.cur.fetchall())
            total_cards = []
            rarity_terms = {
                "L": ["legendary", "legend", "leg", "le", "l"],
                "EX": ["exclusive", "exclu", "exc", "ex"],
                "E": ["epic", "ep", "e"],
                "R": ["rare", "ra", "rr", "r"],
                "C": ["common", "com", "co", "c"],
                "M": ["monsters", "monster", "mon", "mons", "mo", "most", "mosts", 'm', "ms"],
                "NA": ["not_available", "notavailable", "not_ava", "notava", "not", "no", "na", "n/a", "n"]
            }
            for x in all_cards:
                if filter_.lower() in rarity_terms[u.cards_dict(x[4], x[3])["rarity"]]:
                    total_cards.append(x)

        elif search_type in ["energy_cost", "energycost", "energy", "cost", "en", "co", "ec", "e", "c"]:
            dm.cur.execute("select * from cardsinfo where owned_user = " + a_id + orders)
            all_cards = list(dm.cur.fetchall())
            total_cards = []
            for x in all_cards:
                if filter_ == str(u.cards_dict(x[4], x[3])["cost"]):
                    total_cards.append(x)

        else:
            await ctx.send(
                f"{ctx.message.author.mention}, your search was invalid! "
                f"Do `{u.PREF}card_search "
                f"(level/name/rarity/cost) (the level number/card name)`."
            )
            return

        if not total_cards:
            await ctx.send(f"{ctx.message.author.mention}, nothing matched your search!")
            return
        elif len(total_cards) <= (page - 1) * 15:
            await ctx.send(f"{ctx.message.author.mention}, you don't have any cards on page {page}!")
            return

        if order in [7, 8]:
            total_cards = u.order_by_rarity(total_cards, 1)
            total_cards = u.order_by_cost(total_cards, order - 7)
        if order in [9, 10]:
            total_cards = u.order_by_cost(total_cards, 1)
            total_cards = u.order_by_rarity(total_cards, order - 9)
        all_cards = []

        for x in total_cards[(page - 1) * 15:(page - 1) * 15 + 15]:
            card = f"[{u.rarity_cost(x[3])}] **{x[3]}**, " \
                   f"lv: **{x[4]}**, id: `{x[0]}` "
            if x[0] in decks:
                card = f"**>**{card}"
            all_cards.append(card)

        embed = discord.Embed(
            title="Results",
            description="\n".join(all_cards),
            color=discord.Color.gold()
        )

        show_start = (page - 1) * 15 + 1
        show_end = min(page * 15, len(total_cards))
        embed.set_footer(
            text=f"{show_start}-{show_end}/{len(total_cards)} cards displayed in page {page}"
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
