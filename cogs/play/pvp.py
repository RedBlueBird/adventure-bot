import random
import math
import asyncio
import json

import discord
from discord.ext import commands

import util as u
from helpers import checks
from helpers import db_manager as dm
from helpers.battle import BattleData


class Pvp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["challenge", "battles", "bat", "pvp"], description="Battle with other players!")
    @checks.level_check(5)
    @checks.not_preoccupied("in a friendly battle")
    @checks.is_registered()
    async def battle(
            self, ctx: commands.Context,
            people: commands.Greedy[discord.Member],
            gamble_medals: int = 0,
    ):
        a = ctx.author

        if not 0 <= gamble_medals <= 10:
            await ctx.reply("You can't bet that amount of medals!")
            return

        if not 1 <= len(people) <= 5:
            await ctx.reply("You need to invite at least 1 player and at most 5 players!")
            return

        challenger_ids = [a.id] + [i.id for i in people]
        people = [ctx.author] + people
        challenger_names = []
        challenger_decks = []
        challenger_hps = []
        challenger_backpacks = []

        # performs some checks on the user seeing if they're valid
        for i in people:
            id_ = i.id
            # checks if the people that you challenged are valid
            if not dm.is_registered(id_):
                await ctx.reply("That user doesn't exist in the bot's database yet!")
                return

            if id_ in dm.queues and id_ != a.id:
                await ctx.reply(f"{i.mention} is still {dm.queues[id_]}!")
                return

            level = dm.get_user_level(id_)
            # if level < 5:
            #     await ctx.reply(f"{i.mention} isn't level 5 yet!")
            #     return

            if dm.get_user_medal(id_) < gamble_medals:
                await ctx.reply(f"{i.mention} doesn't have {gamble_medals}!")
                return

            challenger_backpacks.append(json.loads(dm.get_user_inventory(id_)))
            deck = dm.get_user_deck(id_)
            if len(deck) != 12:
                await ctx.reply(f"{i.mention} doesn't have 12 cards in their deck!")
                return

            challenger_decks.append(random.sample([f"{x[2]}.{x[1]}" for x in deck], len(deck)))
            hp = round((100 * u.SCALE[1] ** math.floor(level / 2)) * u.SCALE[0])
            challenger_hps.append([hp, 0, hp, 0, 0])
            challenger_names.append(i.name)

        request_msg = await ctx.send(u.ICON['load'])
        # you need a list because of how strings work
        for r in ["✅", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "❎", "⏬"]:
            await request_msg.add_reaction(r)

        request_content = "Hey " + '\n'.join(c.mention for c in people[1:]) + "!\n"
        if gamble_medals > 0:
            request_content += f"{a.mention} wants to battle with {gamble_medals} {u.ICON['medal']}!\n"
        else:
            request_content += f"{a.mention} wants to have a friendly battle!\n"
        request_content += "Host ✅ to start the battle, ❎ to cancel\n" \
                           f"{a} joined `team #1` :smiley:"

        await request_msg.edit(content=request_content)
        joined_users = [a.id]
        teams = {1: [a.id]}
        rejected_users = []
        team_assign = {'1️⃣': 1, '2️⃣': 2, '3️⃣': 3, '4️⃣': 4, '5️⃣': 5, '6️⃣': 6}
        host_ready = False

        # region Wait for the other players
        while not host_ready:
            try:
                check = checks.valid_reaction(
                    ['❎', '✅', '⏬'] + list(team_assign.keys()),
                    people, [request_msg]
                )
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=120.0, check=check
                )
            except asyncio.TimeoutError:
                await ctx.reply("The host went afk... :man_facepalming: ")
                for u_ in joined_users:
                    del dm.queues[u_]
                return

            if reaction.emoji == '✅' and user.id == a.id:
                if len(joined_users) < 2:
                    await ctx.reply("No one joined your battle yet, feels bad man :grimacing:")

                elif len(teams) < 2:
                    await ctx.reply(f"There has to be at least 2 teams to start! :eyes:")

                else:
                    counter = 1
                    for x in teams:  # initialize the pvp fields
                        for y in teams[x]:
                            k = challenger_ids.index(y)
                            teams[x][teams[x].index(y)] = counter
                            challenger_ids.append(challenger_ids.pop(k))
                            challenger_names.append(challenger_names.pop(k))
                            challenger_decks.append(challenger_decks.pop(k))
                            challenger_hps.append(challenger_hps.pop(k))
                            challenger_backpacks.append(challenger_backpacks.pop(k))
                            counter += 1
                    break

            elif reaction.emoji == '❎' and user.id not in rejected_users:
                inv_teams = {i: k for k, v in teams.items() for i in v}
                rejected_users.append(user.id)

                if user.id == a.id:  # well, the host cancelled the battle, call it off
                    await ctx.send(f"{user} the host, cancelled the battle :scream: ")
                    for u_ in joined_users:
                        del dm.queues[u_]
                    return

                elif user.id not in joined_users:
                    await ctx.send(f"{user} rejected the battle request :frowning: ")
                    if len(rejected_users) == len(challenger_names):  # ok call it off, no one joined
                        await ctx.send(f"All players rejected the invite from {user}...")
                        for u_ in joined_users:
                            del dm.queues[u_]
                        return

                else:
                    joined_users.remove(user.id)
                    teams[inv_teams[user.id]].remove(user.id)
                    # await ctx.send(f"\n{user} joined `team #{inv_teams[user.id]}` :smiley: ")
                    request_content = request_content.replace(
                        f"\n{user} joined `team #{inv_teams[user.id]}` :smiley: ", "")
                    await request_msg.edit(content=request_content)
                    await ctx.send(f"{user} joined, then left `team #{inv_teams[user.id]}`...")
                    del dm.queues[user.id]

                    if len(rejected_users) == len(challenger_names):
                        await ctx.send(f"All players rejected the invites from the host {user} :woozy_face")
                        for u_ in joined_users:
                            del dm.queues[u_]
                        return

            elif reaction.emoji in team_assign and user.id in dm.queues and user.id not in rejected_users:
                rejected_users.append(user.id)
                await ctx.send(f"<@{user.id}> can't accept the battling request :frowning: "
                               f"\n`They're still {dm.queues[user.id]}!`")

            elif user.id not in joined_users and reaction.emoji in team_assign:
                joined_users.append(user.id)

                if team_assign[reaction.emoji] not in teams:
                    teams[team_assign[reaction.emoji]] = [user.id]
                else:
                    teams[team_assign[reaction.emoji]].append(user.id)

                dm.queues[user.id] = "in a battle"
                request_content += f"\n{user} joined `team #{team_assign[reaction.emoji]}` :smiley: "
                await request_msg.edit(content=request_content)

                if user.id not in rejected_users:
                    await ctx.send(f"{user} joined `team #{team_assign[reaction.emoji]}` :smiley: ")
                else:
                    rejected_users.remove(user.id)
                    await ctx.send(
                        f"{user} rejected at first, but joined again anyway on `team #{team_assign[reaction.emoji]}` :thinking:")

            elif reaction.emoji == '⏬' and user.id == a.id:
                request_msg = await ctx.send(u.ICON['load'])
                for r in ['✅', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '❎', '⏬']:
                    await request_msg.add_reaction(r)
                await request_msg.edit(content=request_content)

            else:
                continue
        # endregion

        if gamble_medals > 0:
            embed = discord.Embed(
                title=f"A {gamble_medals} Medal(s) Battle Just Started!",
                description=" vs ".join(
                    [str(x) for x in challenger_names[len(challenger_ids) - len(joined_users):]]),
                color=discord.Color.gold()
            )
        else:
            embed = discord.Embed(
                title="A Friendly Battle Just Started!",
                description=" vs ".join([str(x) for x in challenger_names]),
                color=discord.Color.gold()
            )

        await ctx.send(embed=embed)

        # START THE BATTLE!
        offset = len(challenger_ids) - len(joined_users)
        dd = BattleData(
            teams,  # teams
            challenger_names[offset:],  # [str(x) for x in challenger_names], #players
            challenger_ids[offset:],  # players ids
            challenger_decks[offset:],  # decks
            challenger_backpacks[offset:],  # backpack
            challenger_hps[offset:],  # hps
            [35 for _ in range(len(joined_users))],  # stamina
            len(joined_users)
        )

        loading_embed_message = discord.Embed(title="Loading...", description=u.ICON['load'])
        stats_msg = await ctx.send(embed=loading_embed_message)
        hands_msg = await ctx.send(embed=loading_embed_message)

        def stats_check():
            alive = 0
            alive_list = []

            for x in dd.teams:
                for y in dd.teams[x]:
                    if dd.hps.info[y][0] > 0 and dd.staminas.info[y] > 0:
                        alive += 1
                        alive_list.append(x)
                        break

            if alive < 2:
                if not alive_list:
                    dd.afk = 7
                else:
                    dd.afk = alive_list[0]
            return alive > 1

        while stats_check() and dd.afk == 0:
            dd.turns += 1
            hand_embed = dd.show_hand()
            stats_embed = dd.show_stats()
            await stats_msg.edit(embed=stats_embed)
            await hands_msg.edit(embed=hand_embed)

            for i in range(len(dd.descriptions.info)):
                dd.descriptions.info[i + 1] = []
                if "freeze" in dd.effects.info[i + 1]:
                    if dd.effects.info[i + 1]["freeze"] >= 0:
                        dd.freeze_skips.info[i + 1] = True

            players = []
            for ind in range(1, len(dd.players.info) + 1):
                if dd.afk == 0 and not dd.freeze_skips.info[ind] and dd.hps.info[ind][0] > 0 and \
                        dd.staminas.info[ind] > 0:
                    players.append(dd.p_ids.info[ind])

                elif dd.hps.info[ind][0] < 0 or dd.staminas.info[ind] < 0:
                    dd.descriptions.info[ind].append(f"•{u.ICON['dead']}")
                    dd.effects.info[ind] = {}

            while len(players) > 0:
                try:
                    check = lambda m: (
                            m.content.startswith(u.PREF)
                            and m.author.id in players
                            and m.channel == ctx.channel
                    )
                    replied_message = await self.bot.wait_for(
                        "message", timeout=120.0, check=check
                    )
                except asyncio.TimeoutError:
                    for i in players:
                        index = list(dd.p_ids.info.values()).index(i) + 1
                        dd.hps.info[index][0] = 0
                        dd.staminas.info[index] = 0
                        dd.descriptions.info[index].append("Went afk!")
                    players = []

                else:
                    index = list(dd.p_ids.info.values()).index(replied_message.author.id) + 1
                    the_message = dd.interpret_message(replied_message.content[len(u.PREF):],
                                                       str(dd.players.info[index]), index)

                    if type(the_message) is str and the_message not in ["skip", "flee", "refresh", "backpack"]:
                        await ctx.send(the_message)

                    elif the_message == "refresh":
                        stats_msg = await ctx.send(embed=stats_embed)
                        hands_msg = await ctx.send(embed=hand_embed)

                    elif the_message == "skip":
                        # dd.staminas.info[index] += 1
                        players.remove(replied_message.author.id)

                        for y in range(dd.hand_sizes.info[index]):
                            if not dd.decks.info[index][y] in [".".join(x.split(".")[0:2]) for x in
                                                               dd.used_cards.info[index]]:
                                card = dd.decks.info[index][y].split(".")

                                if "on_hand" in u.cards_dict(card[0], card[1]):
                                    dd.execute_card_offense(int(card[0]), card[1], index, index, "on_hand")

                        if not dd.hand_sizes.info[index] == 6:
                            dd.hand_sizes.info[index] += 1

                        dd.descriptions.info[index].append(f"{u.ICON['ski']}{u.ICON['kip']}\n")

                    elif the_message == "flee":
                        players.remove(replied_message.author.id)
                        dd.hps.info[index][0] = 0
                        dd.staminas.info[index] = 0
                        dd.descriptions.info[index].append(f"{u.ICON['fle']}{u.ICON['lee']}\n")

                    elif the_message == "backpack":
                        await ctx.send(embed=u.display_backpack(dd.backpacks.info[index], dd.players.info[index],
                                                                "Backpack"))

                    else:
                        players.remove(replied_message.author.id)
                        dd.staminas.info[index] -= len(the_message)
                        dd.move_numbers.info[index] = the_message
                        dd.used_cards.info[index] = [dd.decks.info[index][int(str(x)[0]) - 1] + "." + str(x)[1:] for x
                                                     in dd.move_numbers.info[index]]
                        dd.stored_energies.info[index] -= sum([u.cards_dict(
                            int(dd.decks.info[index][int(str(x)[0]) - 1].split(".")[0]),
                            dd.decks.info[index][int(str(x)[0]) - 1].split(".")[1])["cost"] for x in
                                                               dd.move_numbers.info[index]])
                        dd.move_numbers.info[index].sort()
                        z = 0

                        for y in range(dd.hand_sizes.info[index]):
                            if not dd.decks.info[index][y] in [".".join(x.split(".")[0:2]) for x in
                                                               dd.used_cards.info[index]]:
                                card = dd.decks.info[index][y].split(".")

                                if "on_hand" in u.cards_dict(card[0], card[1]):
                                    dd.execute_card_offense(int(card[0]), card[1], index, index, "on_hand")

                        for y in range(len(dd.move_numbers.info[index])):
                            x = int(str(dd.move_numbers.info[index][y])[0]) - y + z
                            card = dd.decks.info[index][x - 1].split('.')
                            card_info = u.cards_dict(card[0], card[1])

                            if not card[1] in dd.temporary_cards:
                                if "rewrite" in card_info:
                                    re_name = u.cards_dict(1, card[1])['rewrite']
                                    dd.descriptions.info[index].append(
                                        f"*[{u.rarity_cost(card[1])}] {card[1]} lv:{card[0]}* rewritten as *[{u.rarity_cost(re_name)}] {re_name} lv:{card[0]}*")
                                    dd.decks.info[index][x - 1] = dd.decks.info[index][x - 1].split(".")[0] + "." + \
                                                                  card_info["rewrite"]

                                if "stay" in card_info:
                                    if random.randint(1, 100) <= card_info['stay']:
                                        z += 1
                                        dd.descriptions.info[index].append(
                                            f"*[{u.rarity_cost(card[1])}] {card[1]} lv:{card[0]}* stayed in your hand!")
                                    else:
                                        dd.decks.info[index].insert(len(dd.decks.info[index]),
                                                                    dd.decks.info[index].pop(x - 1))
                                else:
                                    dd.decks.info[index].insert(len(dd.decks.info[index]),
                                                                dd.decks.info[index].pop(x - 1))
                            else:
                                if "stay" in card_info:
                                    if random.randint(1, 100) <= card_info['stay']:
                                        z += 1
                                        dd.descriptions.info[index].append(
                                            f"*[{u.rarity_cost(card[1])}] {card[1]} lv:{card[0]}* stayed in your hand!")
                                    else:
                                        dd.decks.info[index].pop(x - 1)
                                else:
                                    dd.decks.info[index].pop(x - 1)

                        dd.hand_sizes.info[index] -= len(dd.move_numbers.info[index]) - z - 1
                    await replied_message.delete()

            if dd.afk == 0:
                cards_length = [len(i) for i in list(dd.used_cards.info.values())]
                cards_length.sort()

                for x in dd.item_used.info:
                    if dd.item_used.info[x][0].title() != "None":
                        dd.execute_card_defense(-1, dd.item_used.info[x][0].title(), x, dd.item_used.info[x][1])
                        dd.execute_card_offense(-1, dd.item_used.info[x][0].title(), x, dd.item_used.info[x][1])
                        dd.execute_card_special(-1, dd.item_used.info[x][0].title(), x, dd.item_used.info[x][1])

                for x in range(cards_length[-1]):
                    for y in range(1, len(dd.used_cards.info) + 1):
                        if len(dd.used_cards.info[y]) > x:
                            dd.execute_card_defense(int(dd.used_cards.info[y][x].split(".")[0]),
                                                    dd.used_cards.info[y][x].split(".")[1], y,
                                                    int(dd.used_cards.info[y][x].split(".")[2]))

                    for y in range(1, len(dd.used_cards.info) + 1):
                        if len(dd.used_cards.info[y]) > x:
                            dd.execute_card_offense(int(dd.used_cards.info[y][x].split(".")[0]),
                                                    dd.used_cards.info[y][x].split(".")[1], y,
                                                    int(dd.used_cards.info[y][x].split(".")[2]))

                    for y in range(1, len(dd.used_cards.info) + 1):
                        if len(dd.used_cards.info[y]) > x:
                            dd.execute_card_special(int(dd.used_cards.info[y][x].split(".")[0]),
                                                    dd.used_cards.info[y][x].split(".")[1], y,
                                                    int(dd.used_cards.info[y][x].split(".")[2]))

                for i in range(1, len(dd.effects.info) + 1):
                    dd.execute_effects(i)

                for i in range(1, len(dd.used_cards.info) + 1):
                    dd.used_cards.info[i] = []

                for i in range(1, len(dd.players.info) + 1):
                    if dd.stored_energies.info[i] + math.ceil(dd.turns / 4) > 12:
                        dd.stored_energies.info[i] = 12
                    else:
                        dd.stored_energies.info[i] += math.ceil(dd.turns / 4)
                    dd.hps.info[i][0] -= dd.total_damages.info[i]
                    if dd.hps.info[i][0] > dd.hps.info[i][2]:
                        dd.hps.info[i][0] = dd.hps.info[i][2]
                    if dd.hps.info[i][0] <= 0:
                        dd.hps.info[i][0] = 0
                    dd.item_used.info[i] = ["None", i]
                    dd.multipliers.info[i] = [0, 0, 0, 0, 0]
                    dd.total_damages.info[i] = 0
                    dd.hps.info[i][3] = 0
                    dd.hps.info[i][4] = 0
                    dd.freeze_skips.info[i] = False

                if dd.turns >= 50:
                    for i in range(1, len(dd.players.info) + 1):
                        dd.hps.info[i][2] = 0
                        dd.hps.info[i][0] = 0

        if dd.afk <= 6:
            winner = dd.teams[dd.afk]
            await stats_msg.edit(embed=dd.show_stats())
            await hands_msg.edit(embed=dd.show_hand())

            medal_amt = gamble_medals * (len(dd.players.info) - len(winner)) // len(winner)
            xp_amt = dd.turns * 2
            for i in dd.p_ids.info:
                id_ = dd.p_ids.info[i]
                if i in winner:
                    if dd.turns >= 10:
                        if gamble_medals > 0:
                            dm.log_quest(4, 1, id_)
                        dm.log_quest(6, gamble_medals, id_)

                    dm.set_user_medal(id_, dm.get_user_medal(id_) + medal_amt)
                    dm.set_user_exp(id_, dm.get_user_exp(id_) + xp_amt)
                else:
                    dm.set_user_medal(id_, dm.get_user_medal(id_) - gamble_medals)
                dm.set_user_exp(id_, dm.get_user_exp(id_) + xp_amt)

            if gamble_medals != 0:
                embed = discord.Embed(
                    title="Battle Ended!",
                    description=f"**Team {dd.pps[dd.afk]} won!**\n\n"
                                f"Each winner gained {medal_amt} medals \n"
                                f"Everyone else lost {gamble_medals} medals \n"
                                f"Everyone gained {dd.turns * 2} experience points \n"
                                f"This battle took {dd.turns} turns",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="Battle Ended!",
                    description=f"**Team {dd.pps[dd.afk]} won the friendly battle!** \n"
                                f"\nEveryone gained {dd.turns * 2} experience points \n"
                                f"This battle took {dd.turns} turns",
                    color=discord.Color.green()
                )
            await ctx.send(embed=embed)

        else:
            await stats_msg.edit(embed=dd.show_stats())
            await hands_msg.edit(embed=dd.show_hand())

            xp_amt = dd.turns * 2
            for i in dd.p_ids.info:
                id_ = dd.p_ids.info[i]
                dm.set_user_exp(id_, dm.get_user_exp(id_) + xp_amt)

            embed = discord.Embed(
                title="Battle Ended!",
                description=f"**It's a Tie!**\n\nNo one gained or lost any medals!"
                            f"\nEveryone gained {dd.turns * 2} experience points"
                            f"\nThis battle took {dd.turns} turns",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

        for u_ in list(set(list(dd.p_ids.info.values()))):
            del dm.queues[u_]


async def setup(bot):
    await bot.add_cog(Pvp(bot))
