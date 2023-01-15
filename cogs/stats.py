import random
import math
import time as times
import datetime as dt

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks
from helpers import db_manager as dm
from helpers import asset_manager as am


class Stats(commands.Cog, name="informational"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="profile",
        description="Check player's general information.",
        aliases=["p", "pro"]
    )
    async def profile(self, ctx: Context, user: discord.User = None) -> None:
        """
        Check player's general information
        :param user: The user the information is obtained from
        """

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
            time = am.time_converter(int(prof[14].split(',')[1]) - int(times.time()))
            description_msg = f"14 \n{am.ICONS['timer']}**ᴘʀᴇᴍɪᴜᴍ**: {time} \n"
            tickets = "10"
        else:
            description_msg = "7 \n"
            tickets = "5"

        tick_msg = "" if prof[3] < 4 else f"{am.ICONS['tick']}**Raid Tickets: **{prof[9]}/{tickets}"

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
                value=f"{am.ICONS['exp']} {prof[4]}/{math.floor(int((prof[3] ** 2) * 40 + 60))}\n"
                      f"{am.ICONS['hp']} {round((100 * am.SCALE[1] ** math.floor(prof[3] / 2)) * am.SCALE[0])}",
                inline=False
            )
        else:
            embed.add_field(
                name=f"Max Level: {prof[3]}",
                value=f"{am.ICONS['exp']} {prof[4]}\n"
                      f"{am.ICONS['hp']} {round((100 * am.SCALE[1] ** math.floor(prof[3] / 2)) * am.SCALE[0])}",
                inline=False
            )

        if prof[10] != str(dt.date.today()):
            dts = "Right Now!"
        else:
            dts = am.remain_time()
        embed.add_field(
            name="Currency: ",
            value=f"{am.ICONS['coin']}**Golden Coins: **{prof[5]}\n"
                  f"{am.ICONS['gem']}**Shiny Gems: **{prof[6]}\n"
                  f"{am.ICONS['token']}**Confetti: **{prof[7]}\n"
                  f"{am.ICONS['medal']}**Medals: **{prof[8]}\n"
                  f"{tick_msg}",
            inline=False
        )
        embed.add_field(
            name="Times: ",
            value=f"{am.ICONS['streak']}**Current daily streak: **{int(prof[13])}/" +
                  description_msg +
                  f"{am.ICONS['timer']}**Next daily: **{dts} \n"
                  f"{am.ICONS['timer']}**Next quest: "
                  f"**{am.time_converter(int(prof[15].split(',')[-1]) - int(times.time()))}",
            inline=False
        )

        if achivement_info[3] != "0000000000000000000000000000000000000000":
            badges = ["beta b", "pro b", "art b", "egg b", "fbi b", "for b"]
            owned_badges = []
            for i, value in enumerate(achivement_info[3]):
                if value == "1":
                    owned_badges.append(am.ICONS[badges[i]])
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
                    quest_id = math.ceil(am.log_level_gen(random.randint(1, 2 ** 8)) / 2) - 2
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

                dm.cur.execute(
                    f"update playersinfo set quests = '{','.join(quests)}' where userid = '{member.id}'")
                dm.mydb.commit()

        if len(quests) == 1:
            embed = discord.Embed(title=f"{member.display_name}'s Quests:",
                                  description="You don't have any quests, \nCome back later for more!",
                                  color=discord.Color.green())
        else:
            if len(quests) == 4 and not is_premium:
                embed = discord.Embed(title=f"{member.display_name}'s Quests:",
                                      description="You can't have more than 3 quests active!",
                                      color=discord.Color.gold())
            elif len(quests) == 5 and is_premium:
                embed = discord.Embed(title=f"{member.display_name}'s Quests:",
                                      description="You can't have more than 4 quests active!",
                                      color=discord.Color.gold())
            else:
                embed = discord.Embed(title=f"{member.display_name}'s Quests:", description=None,
                                      color=discord.Color.gold())

            for x in range(len(quests) - 1):
                quest = am.quest_index(quests[x])
                embed.add_field(name=f"**{quest[2]} {am.quest_str_rep(quests[x].split('.')[1], quest[0])}**",
                                value=f"Finished {math.floor(100 * int(quests[x].split('.')[2]) / quest[0])}% \n"
                                      f"Reward: **{''.join(quest[1::2])} {quest[4]} {am.ICONS['exp']}**",
                                inline=False)  # **1 {am.icon['token']}**", inline=False)

        embed.set_thumbnail(url=member.avatar.url)
        if is_premium == 0:
            embed.set_footer(
                text=f"There's {am.time_converter(int(quests[-1]) - int(times.time()))} left till a new quest")
        elif is_premium == 1:
            embed.set_footer(
                text=f"There's {am.time_converter(int(quests[-1]) - int(times.time()))} left till a new quest")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="inventory",
        description="Displays all the cards in a member's inventory in the form of an embed.",
        aliases=["card", "i", "inv"]
    )
    async def inventory(self, ctx: Context, page: str = "1", user: discord.User = None) -> None:
        """
        Displays all the cards in a member's inventory in the form of an embed.

        :param page: The page of cards to display
        :param user: The user whose cards to display
        """
        page = max(math.floor(int(page) + 1 - 1), 1) if page.isdigit() else 1

        if user == None:
            user = ctx.message.author
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)

        dm.cur.execute(f"select id from playersinfo where userid = '{member.id}'")
        if not dm.cur.fetchall():
            await ctx.send(f"{ctx.message.author.mention}, the user id is invalid!")
            return

        dm.cur.execute(
            f"select inventory_order, deck_slot from playersinfo where userid = '{ctx.message.author.id}'")
        result = dm.cur.fetchall()[0]
        order = result[0]
        deck_slot = result[1]
        dm.cur.execute(f"select deck{deck_slot} from playersachivements where userid = '{ctx.message.author.id}'")
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
        dm.cur.execute(f"select * from cardsinfo where owned_user = '{member.id}' order by {order_by}")

        result = dm.cur.fetchall()
        if order in [7, 8]:
            result = am.order_by_rarity(result, 1)
            result = am.order_by_cost(result, order - 7)
        if order in [9, 10]:
            result = am.order_by_cost(result, 1)
            result = am.order_by_rarity(result, order - 9)

        if len(result) < (page - 1) * 15:
            await ctx.send(f"{ctx.message.author.mention}, there is no cards in this page!")
            return

        result = result[(page - 1) * 15:(page - 1) * 15 + 15]
        dm.cur.execute(f"select * from cardsinfo where owned_user = '{member.id}'")
        total_cards = len(dm.cur.fetchall())
        if total_cards > (page - 1) * 15:
            all_cards = []

            def card_properties(cardinfo):
                if cardinfo[0] in decks:
                    all_cards.append(f"**>**[{am.rarity_cost(cardinfo[3])}] **{cardinfo[3]}**, "
                                     f"lv: **{cardinfo[4]}**, id: `{cardinfo[0]}` ")
                else:
                    all_cards.append(f"[{am.rarity_cost(cardinfo[3])}] **{cardinfo[3]}**, "
                                     f"lv: **{cardinfo[4]}**, id: `{cardinfo[0]}` ")

            for x in result:
                card_properties(x)

            embed = discord.Embed(title=member.display_name + "'s cards:",
                                  description="%s" % ("\n".join(all_cards)),
                                  color=discord.Color.gold())
            embed.set_thumbnail(url=member.avatar.url)

            if page * 15 > total_cards:
                embed.set_footer(text=str((page - 1) * 15 + 1) + "-" + str(total_cards) + "/" + str(
                    total_cards) + " cards displayed in page " + str(page))
            else:
                embed.set_footer(text=str((page - 1) * 15 + 1) + "-" + str(page * 15) + "/" + str(
                    total_cards) + " cards displayed in page " + str(page))
            await ctx.send(embed=embed)

        else:
            await ctx.send(
                ctx.message.author.mention + f", you don't have any cards on page {page}!")

    @commands.hybrid_command(
        name="leaderboard",
        description="Displays the world's top players.",
        aliases=["lb", "leaderboards", "lbs"]
    )
    async def leaderboard(self, ctx: Context, leaderboard_type="None") -> None:
        """
        Displays the world's top players.
        
        :param leaderboard_type: The type of leaderboard to display
        """
        selected_players = []
        if leaderboard_type.lower() in ["levels", "level", "exps", "exp", "l", "e"]:
            dm.cur.execute("select id, userid, level, exps from playersinfo order by level desc, exps desc limit 10")
            all_players = dm.cur.fetchall()
            for x in range(10):
                y = await self.bot.fetch_user(str(all_players[x][1]))
                if not str(all_players[x][1]) == str(ctx.message.author.id):
                    selected_players.insert(len(selected_players),
                                            "**[" + str(x + 1) + "]**. **" + str(y) + "** \n• Level: " + str(
                                                all_players[x][2]) + ", Experience Points: " + str(
                                                all_players[x][3]) + " \n")
                else:
                    selected_players.insert(len(selected_players),
                                            "**[" + str(x + 1) + "]**. **" + str(y) + "** __\n• Level: " + str(
                                                all_players[x][2]) + ", Experience Points: " + str(
                                                all_players[x][3]) + "__ \n")
            embed = discord.Embed(title="Leaderboard - most experience points",
                                  description=" ".join(selected_players),
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)

        elif leaderboard_type.lower() in ["coins", "golden_coins", "goldencoins", "goldencoins", "coin", "gc", "c"]:
            dm.cur.execute("select id, userid, coins, gems from playersinfo order by coins desc, gems desc limit 10")
            all_players = dm.cur.fetchall()
            for x in range(10):
                y = await self.bot.fetch_user(str(all_players[x][1]))
                if not str(all_players[x][1]) == str(ctx.message.author.id):
                    selected_players.insert(len(selected_players), "**[" + str(x + 1) + "]**. **" + str(
                        y) + "** \n• Golden Coins: " + str(all_players[x][2]) + ", Shiny Gems: " + str(
                        all_players[x][3]) + " \n")
                else:
                    selected_players.insert(len(selected_players), "**[" + str(x + 1) + "]**. **" + str(
                        y) + "** __\n• Golden Coins: " + str(all_players[x][2]) + ", Shiny Gems: " + str(
                        all_players[x][3]) + "__ \n")
            embed = discord.Embed(title="Leaderboard - most golden coins",
                                  description=" ".join(selected_players),
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)

        elif leaderboard_type.lower() in ["shiny_gems", "shinygems", "shiny_gem", "shinygem", "gems", "gem", "g", "sg"]:
            dm.cur.execute(
                "select id, userid, gems, coins from playersinfo order by gems desc, coins desc limit 10")
            all_players = dm.cur.fetchall()
            for x in range(10):
                y = await self.bot.fetch_user(str(all_players[x][1]))
                if not str(all_players[x][1]) == str(ctx.message.author.id):
                    selected_players.insert(len(selected_players), "**[" + str(x + 1) + "]**. **" + str(
                        y) + "** \n• Shiny gems: " + str(all_players[x][2]) + ", Golden Coins: " + str(
                        all_players[x][3]) + " \n")
                else:
                    selected_players.insert(len(selected_players), "**[" + str(x + 1) + "]**. **" + str(
                        y) + "** __\n• Shiny gems: " + str(all_players[x][2]) + ", Golden Coins: " + str(
                        all_players[x][3]) + "__ \n")
            embed = discord.Embed(title="Leaderboard - most shiny gems",
                                  description=" ".join(selected_players),
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)

        elif leaderboard_type.lower() in ["medals", "medal", "m"]:
            dm.cur.execute("select id, userid, medals from playersinfo order by medals desc limit 10")
            all_players = dm.cur.fetchall()
            for x in range(10):
                y = await self.bot.fetch_user(str(all_players[x][1]))
                if not str(all_players[x][1]) == str(ctx.message.author.id):
                    selected_players.insert(len(selected_players),
                                            "**[" + str(x + 1) + "]**. **" + str(y) + "** \n• Medals: " + str(
                                                all_players[x][2]) + " \n")
                else:
                    selected_players.insert(len(selected_players),
                                            "**[" + str(x + 1) + "]**. **" + str(y) + "** __\n• Medals: " + str(
                                                all_players[x][2]) + "__ \n")
            embed = discord.Embed(title="Leaderboard - most medals", description=" ".join(selected_players),
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)

        elif leaderboard_type.lower() in ["tokens", "t", "event_tokens", "token"]:
            dm.cur.execute(
                "select id, userid, event_token from playersinfo order by event_token desc limit 10")
            all_players = dm.cur.fetchall()
            for x in range(10):
                y = await self.bot.fetch_user(str(all_players[x][1]))
                if not str(all_players[x][1]) == str(ctx.message.author.id):
                    selected_players.insert(len(selected_players),
                                            "**[" + str(x + 1) + "]**. **" + str(y) + "** \n• Tokens: " + str(
                                                all_players[x][2]) + " \n")
                else:
                    selected_players.insert(len(selected_players),
                                            "**[" + str(x + 1) + "]**. **" + str(y) + "** __\n• Tokens: " + str(
                                                all_players[x][2]) + "__ \n")
            embed = discord.Embed(title="Leaderboard - most tokens", description=" ".join(selected_players),
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(title="Here is a list of leaderboards the bot can show",
                                  description="`" + am.PREF + "leaderboard (leaderboard_type)`",
                                  color=discord.Color.gold())
            embed.add_field(name="Most experience points players",
                            value=f"`{am.PREF}leaderboard levels`", inline=False)
            embed.add_field(name="Most golden coins players", value=f"`{am.PREF}leaderboard coins`",
                            inline=False)
            embed.add_field(name="Most shiny gems players", value=f"`{am.PREF}leaderboard gems`",
                            inline=False)
            embed.add_field(name="Most medals players", value=f"`{am.PREF}leaderboard medals`",
                            inline=False)
            embed.add_field(name="Most tokens players", value=f"`{am.PREF}leaderbord tokens`",
                            inline=False)
            embed.set_footer(text="Showing top 10 players only")
            embed.set_thumbnail(url=ctx.message.author.avatar.url)
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="deck",
        description="Displays the deck in the memeber's current deck slot",
        aliases=["decks"]
    )
    async def deck(self, ctx: Context, deck_slot=None, user: discord.User = None) -> None:
        """
        Displays the deck in the memeber's current deck slot
        :param deck_slot: The deck slot to search.
        :param user: The user whose deck slots to search.
        """
        if user is None:
            user = ctx.message.author
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)

        try:
            deck_slot = round(int(deck_slot))
            if deck_slot < 1 or deck_slot > 6:
                await ctx.send("The deck slot number must between 1-6!")
                return
        except (TypeError, ValueError):
            if deck_slot is not None and deck_slot.lower() in ["list", "li"]:
                deck_slot = "list"
            deck_slot = 0 if deck_slot != "list" else "list"

        dm.cur.execute(f"select inventory_order from playersinfo where userid = '{ctx.message.author.id}'")
        order = dm.cur.fetchall()[0][0]
        dm.cur.execute(f"select level, deck_slot from playersinfo where userid = '{member.id}'")
        result = dm.cur.fetchall()[0]
        level = result[0]
        selected_slot = result[1]
        deck_slots = {1: 0, 2: 0, 3: 6, 4: 15, 5: 21, 6: 29}
        deck_slot = deck_slot if deck_slot != 0 else selected_slot

        if deck_slot == "list":
            all_decks = []
            for i in range(6):
                dm.cur.execute(f"select deck{i + 1} from playersachivements where userid = '{member.id}'")
                deck = dm.cur.fetchall()[0][0].split(",")
                deck_length = len(deck) if deck != ["0"] else 0
                all_decks.append(deck_length)

            embed = discord.Embed(title=member.display_name + "'s decks",
                                  description=f"`{am.PREF}deck #` to view a specific deck",
                                  color=discord.Color.gold())

            for i in range(6):
                if selected_slot == i + 1:
                    embed.add_field(name=f"**Deck {i + 1}** - selected", value=f"{all_decks[i]}/12 cards", inline=False)
                elif level < deck_slots[i + 1]:
                    embed.add_field(name=f"**Deck {i + 1}**", value=f"unlocked at level {deck_slots[i + 1]}",
                                    inline=False)
                else:
                    embed.add_field(name=f"**Deck {i + 1}**", value=f"{all_decks[i]}/12 cards", inline=False)

            embed.set_thumbnail(url=member.avatar.url)
            await ctx.send(embed=embed)
            return

        if level < deck_slots[deck_slot]:
            await ctx.send("The deck slot you selected is currently locked!")
            return

        dm.cur.execute(f"select deck{deck_slot} from playersachivements where userid = '{member.id}'")
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
            f"select * from cardsinfo where owned_user = {member.id} and id in ({str(decks)[1:-1]}) order by {lookup}")
        result = dm.cur.fetchall()
        if order in [7, 8]:
            result = am.order_by_rarity(result, 1)
            result = am.order_by_cost(result, order - 7)
        if order in [9, 10]:
            result = am.order_by_cost(result, 1)
            result = am.order_by_rarity(result, order - 9)

        if not result:
            dm.cur.execute(f"select * from cardsinfo where owned_user = '{member.id}'")
            if not dm.cur.fetchall():
                await ctx.send(f"{ctx.message.author.mention}, the user id you put in is invalid!")
                return

        all_cards = []

        def card_properties(c_info):
            if deck_slot == selected_slot:
                all_cards.append(f"**>**[{am.rarity_cost(c_info[3])}] **{c_info[3]}**, "
                                 f"lv: **{c_info[4]}**, id: `{c_info[0]}` ")
            else:
                all_cards.append(f"[{am.rarity_cost(c_info[3])}] **{c_info[3]}**, "
                                 f"lv: **{c_info[4]}**, id: `{c_info[0]}` ")

        total_energy_cost = 0
        for x in result:
            card_properties(x)
            total_energy_cost += am.cards_dict(x[4], x[3])["cost"]

        mod_msg = ""
        if deck_slot != selected_slot:
            mod_msg = f"\n`{am.PREF}select {deck_slot}` to modify this deck"

        embed = discord.Embed(title=member.display_name + f"'s Deck #{deck_slot}:",
                              description="`" + am.PREF + "deck list` to display all your decks" + mod_msg + "\n\n" + "%s" % (
                                  "\n".join(all_cards)),
                              color=discord.Color.gold())
        embed.set_thumbnail(url=member.avatar.url)

        if not result:
            embed.add_field(name="You have __NO__ cards in your deck!",
                            value=f"`{am.PREF}add (card_id)` to start adding cards!")
        if not len(result) == 12:
            embed.set_footer(text="You need " + str(12 - len(result)) + " more cards needed to complete this deck!")
        else:
            embed.set_footer(text="Average energy cost: " + str(round(total_energy_cost * 100 / 12) / 100))
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="info",
        description="Looks up entities, from effects to mobs and displays an embed containing info about it.",
        aliases=["in", "ins", "ifs", "informations", "check"]
    )
    async def info(self, ctx: Context, dictionary_name=None, name=None, level: str = "bruh moment") -> None:
        """
        Looks up entities, from effects to mobs and displays an embed containing info about it.
        :param dictionary_name: The type of the thing which to look up (can be a card, mob, item, or effect)
        :param name: The name of the thing to look up
        :param level: The level of the thing for number crunching
        """
        if name is None or dictionary_name is None:
            await ctx.send(f"{ctx.message.author.mention}, the correct format for this command is `" +
                           am.PREF + "info (card/mob/item/effect) (name) (level)`!")
            return

        level = max(1, math.floor(int(level) + 1 - 1)) if level.isdigit() else 1
        rarity_translator = {"C": "Common", "R": "Rare", "E": "Epic", "EX": "Exclusive",
                             "L": "Legendary", "M": "N/A", "NA": "N/A"}

        dictionary_name = dictionary_name.lower()
        if dictionary_name in ["card", "cards", "c", "ca"]:
            card_info = am.cards_dict(level, " ".join(name.lower().split("_")))
            card_information = [
                f"**Name:** {card_info['name']}",
                f"**Level:** {level}",
                f"**Rarity:** {rarity_translator[card_info['rarity']]}",
                f"**Energy Cost:** {card_info['cost']}",
                f"**Accuracy:** {card_info['acc']}%",
                f"**Critical Chance:** {card_info['crit']}%"
            ]

            if card_info["rarity"] == "M":
                card_information.insert(len(card_information), "**[Monster Card]** - Unobtainable")
            if card_info["rarity"] == "EX":
                card_information.insert(len(card_information), "**[Exclusive Card]** - Obtainable in events")

            embed = discord.Embed(title="Card's info:", description=None, color=discord.Color.green())
            embed.add_field(name="Description: ", value="%s" % ("\n".join(card_information)), inline=False)
            embed.add_field(name="Uses: ", value=am.fill_args(card_info, level), inline=False)
            # if card_info["requirement"] != "None":
            # embed.add_field(name="Requirements: ", value=card_info["requirement"], inline=False)
            embed.add_field(name="Brief: ", value="" + card_info["brief"], inline=False)
            """
            if "journal" in card_info:
                embed.add_field(name="Scout's Journal: ", value="*" + card_info["journal"] + "*", inline=False)
            embed.set_thumbnail(url=ctx.message.author.avatar.url)
            """
            await ctx.send(embed=embed)

        elif dictionary_name in ["monster", "mon", "mob", "mobs", "m"]:
            mob_info = am.mobs_dict(level, " ".join(name.lower().split("_")))
            card_information = [f"**Name:** {mob_info['name']}",
                                f"**Level:** " + str(level),
                                f"**Rarity:** {rarity_translator[mob_info['rarity']]}",
                                f"**Energy Lag:** {mob_info['energy_lag']} turns",
                                f"**Health:** {mob_info['health']}",
                                f"**Stamina:** {mob_info['stamina']}"]

            embed = discord.Embed(title="Mob's info:", description=None, color=discord.Color.green())
            embed.add_field(name="Description: ", value="%s" % ("\n".join(card_information)), inline=False)
            embed.add_field(name="Brief: ", value="*" + mob_info["brief"] + "*", inline=False)
            """
            if "tip" in mob_info:
                embed.add_field(name="Fighting Tips: ", value="*" + mob_info["tip"] + "*", inline=False)
            if "journal" in mob_info:
                embed.add_field(name="Scout's Journal: ", value="*" + mob_info["journal"] + "*", inline=False)
            embed.set_thumbnail(url=ctx.message.author.avatar.url)
            """
            await ctx.send(embed=embed)

        elif dictionary_name in ["item", "items", "ite", "it", "i", "object", "objects", "obj", "objec", "o"]:
            item_info = am.items_dict(" ".join(name.lower().split("_")))
            item_information = [f"**Name:** {item_info['name']}",
                                f"**Weight:** {item_info['weight']}",
                                f"**Rarity:** {rarity_translator[item_info['rarity']]}",
                                f"**Accuracy:** {item_info['acc']}%",
                                f"**Critical Chance:** {item_info['crit']}%",
                                f"**One Use:** {item_info['one_use']}",
                                f"**Use In Battle:** {item_info['in_battle']}",
                                f"**Sell Price:** {item_info['sell']}gc",
                                f"**Abbreviation:** {item_info['abb']}"]

            embed = discord.Embed(title="Item's info:", description=None, color=discord.Color.green())
            embed.add_field(name="Description: ", value="%s" % ("\n".join(item_information)), inline=False)
            embed.add_field(name="Uses: ", value=item_info["description"], inline=False)
            embed.add_field(name="Brief: ", value=f"*{item_info['brief']}*", inline=False)

            """
            if "journal" in item_info:
                embed.add_field(name="Scout's Journal: ", value="*" + item_info["journal"] + "*", inline=False)
            embed.set_thumbnail(url=ctx.message.author.avatar.url)
            """
            embed.set_image(
                url=f"https://cdn.discordapp.com/emojis/{am.ICONS[item_info['name'].lower()][len(''.join(item_info['name'].split(' '))) + 3:-1]}.png")

            await ctx.send(embed=embed)

        elif dictionary_name in ["effect", "effects", "eff", "ef", "e"]:
            effect_info = am.effs_dict(" ".join(name.lower().split("_")))
            eff_information = ["**Name:** " + effect_info["name"]]
            embed = discord.Embed(title="Effect's info:", description=None, color=discord.Color.green())
            embed.add_field(name="Description: ", value="%s" % ("\n".join(eff_information)), inline=False)
            embed.add_field(name="Uses: ", value=effect_info["description"], inline=False)
            embed.set_thumbnail(url=ctx.message.author.avatar.url)
            embed.set_image(url=f"https://cdn.discordapp.com/emojis/"
                                f"{am.CONVERT[effect_info['name'].lower()][4:-1]}.png")
            await ctx.send(embed=embed)

        else:
            await ctx.send(f"{ctx.message.author.mention}, the correct format for this command is "
                           f"`{am.PREF}info (card/mob/item/effect) (name) (level)`!")

    @commands.hybrid_command(
        name="shop",
        description="The player can buy cards and other things here.",
        aliases=["shops"]
    )
    async def shop(self, ctx: Context, page=None) -> None:
        """
        The player can buy cards and other things here.
        :param page: The page of the stop to display.
                     1- Daily deals
                     2- Card packs
                     3- Gem shop (coins, raid tickets, etc.)
        """
        dm.cur.execute("select level from playersinfo where userid = " + str(ctx.message.author.id))
        player_level = int(dm.cur.fetchall()[0][0])
        if player_level < 3:
            await ctx.send(f"{ctx.message.author.mention}, the shop unlocks at level 3!")

        if page is not None:
            if page.isdigit():
                page = abs(int(page))
                if not 1 <= page <= 3:
                    await ctx.send(f"{ctx.message.author.mention}, the page number has to be between 1 and 3!")
                    return
            else:
                await ctx.send(f"{ctx.message.author.mention}, the page number has to be a number!")
                return
        else:
            embed = discord.Embed(title="Cards Shop", description=None, color=discord.Color.gold())
            embed.add_field(name="Daily Deals", value="**»** page 1", inline=False)
            embed.add_field(name="Card Packs", value="**»** page 2", inline=False)
            embed.add_field(name="Currencies", value="**»** page 3", inline=False)
            embed.set_footer(text=am.PREF + "shop (page_number)")
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
                description=f"{am.ICONS['coin']} **{coins}** {am.ICONS['gem']} **{gems}**",
                color=discord.Color.gold()
            )  # {am.icon['token']} **{tokens}**")

            def card_deal(the_card, place):
                card = the_card.split('.')
                if the_card[0] != "-":
                    cost = round(1.6 ** int(card[0]) * 50 * am.price_factor(card[1]))
                    embed.add_field(
                        name=f"**[{am.rarity_cost(card[1])}] {card[1]} lv: {card[0]}**",
                        value=f"Cost: **{cost}** {am.ICONS['coin']} \n`{am.PREF}buy {place}`"
                    )
                else:
                    embed.add_field(name=f"**[{am.rarity_cost(card[1])}] {card[1]} lv: {card[0][1:]}**",
                                    value="Purchased")

            for x in range(len(the_deals)):
                card_deal(the_deals[x], x + 1)
            embed.set_footer(text=f"Wait {am.remain_time()} or {am.PREF}buy r to refresh shop")
            await ctx.send(embed=embed)

        elif page == 2:
            embed = discord.Embed(
                title="Shop - Card Packs:",
                description=f"{am.ICONS['coin']} **{coins}** {am.ICONS['gem']} **{gems}** {am.ICONS['token']} **{tokens}**",
                color=discord.Color.green()
            )

            packs = [
                {'name': "**Basic Pack**",
                 'value': f"Cost: **3** {am.ICONS['gem']} \n"
                          "• contains 3 (lv 4-10) cards \n"
                          f"`{am.PREF}buy basic`"},
                {'name': "**Fire Pack**",
                 'value': f"Cost: **5** {am.ICONS['gem']} \n"
                          "• contains 4 (lv 4-10) cards with a \nhigher chance of fire cards \n"
                          f"`{am.PREF}buy fire`"},
                {'name': "**Evil Pack**",
                 'value': f"Cost: **5** {am.ICONS['gem']} \n"
                          "• contains 4 (lv 4-10) cards with a \nhigher chance of curse cards \n"
                          f"`{am.PREF}buy evil`"},
                {'name': "**Electric Pack**",
                 'value': f"Cost: **5** {am.ICONS['gem']} \n"
                          "• contains 4 (lv 4-10) cards with a \nhigher chance of electric cards \n"
                          f"`{am.PREF}buy electric`"},
                {'name': "**Defensive Pack**",
                 'value': f"Cost: **5** {am.ICONS['gem']} \n"
                          "• contains 4 (lv 4-10) cards with a \nhigher chance of defense cards \n"
                          f"`{am.PREF}buy defensive`"},
                {'name': "**Pro Pack**",
                 'value': f"Cost: **24** {am.ICONS['gem']} \n"
                          "• contains 6 (lv 7-10) cards \n"
                          f"`{am.PREF}buy pro`"},
                # {'name': "**Anniversary Pack**",
                # 'value': f"Cost: **40** {am.icon['token']} \n"
                #          "• contains **[EX/7] Confetti Cannon** \n"
                #          f"`{am.prefix}buy confetti`"}
            ]

            for p in packs:
                embed.add_field(**p)
            embed.set_footer(text="Let the buyers beware")
            await ctx.send(embed=embed)

        elif page == 3:
            embed = discord.Embed(title="Shop - Currencies:",
                                  description=f"{am.ICONS['coin']} **{coins}** {am.ICONS['gem']} **{gems}**",
                                  color=discord.Color.green())  # {am.icon['token']} **{tokens}**")

            currency_offers = [
                {"name": "**1000 Golden Coins**", "value": f"Cost: **3** {am.ICONS['gem']} \n`{am.PREF}buy gc1`"},
                {"name": "**2250 Golden Coins**", "value": f"Cost: **6** {am.ICONS['gem']} \n`{am.PREF}buy gc2`"},
                {"name": "**11000 Golden Coins**", "value": f"Cost: **24** {am.ICONS['gem']} \n`{am.PREF}buy gc3`"},
                {"name": "**1 Raid Ticket**", "value": f"Cost: **2** {am.ICONS['gem']} \n`{am.PREF}buy rt1`"},
                {"name": "**2 Raid Ticket**", "value": f"Cost: **4** {am.ICONS['gem']} \n`{am.PREF}buy rt2`"},
                {"name": "**3 Raid Ticket**", "value": f"Cost: **6** {am.ICONS['gem']} \n`{am.PREF}buy rt3`"}
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
        dm.cur.execute(
            f"select inventory_order, deck_slot from playersinfo where userid = '{ctx.message.author.id}'")
        result = list(dm.cur.fetchall())[0]
        order = result[0]
        assert 1 <= order <= 6
        deck_slot = result[1]
        dm.cur.execute(f"select deck{deck_slot} from playersachivements where userid = '{ctx.message.author.id}'")
        decks = [int(k) for i in dm.cur.fetchall()[0] for k in i.split(",")]

        orders = ""
        if order == 1:
            orders = " order by card_level, card_name"
        elif order in [2, 7, 8, 9, 10]:
            orders = " order by card_level desc, card_name"
        elif order == 3:
            orders = " order by card_name"
        elif order == 4:
            orders = " order by card_name desc"
        elif order == 5:
            orders = " order by id, card_name"
        elif order == 6:
            orders = " order by id desc, card_name"

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
                if filter_.lower() in rarity_terms[am.cards_dict(x[4], x[3])["rarity"]]:
                    total_cards.append(x)

        elif search_type in ["energy_cost", "energycost", "energy", "cost", "en", "co", "ec", "e", "c"]:
            dm.cur.execute("select * from cardsinfo where owned_user = " + a_id + orders)
            all_cards = list(dm.cur.fetchall())
            total_cards = []
            for x in all_cards:
                if filter_ == str(am.cards_dict(x[4], x[3])["cost"]):
                    total_cards.append(x)

        else:
            await ctx.send(f"{ctx.message.author.mention}, your search was invalid! "
                           f"Do `{am.PREF}card_search "
                           f"(level/name/rarity/cost) (the level number/card name)` instead!")
            return

        if not total_cards:
            await ctx.send(f"{ctx.message.author.mention}, nothing matched your search!")

        elif len(total_cards) > (page - 1) * 15:
            if order in [7, 8]:
                total_cards = am.order_by_rarity(total_cards, 1)
                total_cards = am.order_by_cost(total_cards, order - 7)
            if order in [9, 10]:
                total_cards = am.order_by_cost(total_cards, 1)
                total_cards = am.order_by_rarity(total_cards, order - 9)
            all_cards = []

            def card_properties(cardinfo):
                if cardinfo[0] in decks:
                    all_cards.append(
                        f"**>**[{am.rarity_cost(cardinfo[3])}] **{cardinfo[3]}**, lv: **{cardinfo[4]}**, id: `{cardinfo[0]}` ")
                else:
                    all_cards.append(
                        f"[{am.rarity_cost(cardinfo[3])}] **{cardinfo[3]}**, lv: **{cardinfo[4]}**, id: `{cardinfo[0]}` ")

            for x in total_cards[(page - 1) * 15:(page - 1) * 15 + 15]:
                card_properties(x)
            embed = discord.Embed(title="Your search result", description="\n".join(all_cards),
                                  color=discord.Color.gold())
            if page * 15 > len(total_cards):
                embed.set_footer(text=f"{(page - 1) * 15 + 1}-{len(total_cards)}/" +
                                      f"{len(total_cards)} cards displayed in page {page}")
            else:
                embed.set_footer(text=f"{(page - 1) * 15 + 1}-{page * 15}/" +
                                      f"{len(total_cards)} cards displayed in page {page}")
            await ctx.send(embed=embed)

        else:
            await ctx.send(f"{ctx.message.author.mention}, you don't have any cards on page {page}!")

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
