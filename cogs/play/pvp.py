import random
import math
import asyncio
import json

import discord
from discord.ext import commands

import util as u
from helpers import checks
from helpers import db_manager as dm
from helpers import BattleData
from views import BattleSelect, PvpInvite


class Pvp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases=["challenge", "battles", "bat", "pvp"],
        description="Battle with other players!"
    )
    @checks.level_check(5)
    @checks.not_preoccupied("in a friendly battle")
    @checks.is_registered()
    async def battle(
            self, ctx: commands.Context,
            gamble_medals: int = 0,
    ):
        a = ctx.author

        if not 0 <= gamble_medals <= 10:
            await ctx.reply("You can't bet that amount of medals!")
            return

        view = BattleSelect(a)
        msg = await ctx.reply(view=view)
        while True:
            await view.wait()
            people = view.selected
            for p in people:
                id_ = p.id
                if not dm.is_registered(id_):
                    await ctx.reply("That user doesn't exist in the bot yet!")
                    break

                if id_ in dm.queues and id_ != a.id:
                    await ctx.reply(f"{p.mention} is still {dm.queues[id_]}!")
                    break

                level = dm.get_user_level(id_)
                # if level < 5:
                #     await ctx.reply(f"{u.mention} isn't level 5 yet!")
                #     break

                if dm.get_user_medal(id_) < gamble_medals:
                    await ctx.reply(f"{p.mention} doesn't have {gamble_medals}!")
                    break

                if dm.get_user_deck_count(id_) != 12:
                    await ctx.reply(f"{p.mention} doesn't have 12 cards in their deck!")
                    break
            else:
                break
            
            view = BattleSelect(a)
            msg.edit(view=view)

        c_ids = [a.id] + [p.id for p in people]
        people = [ctx.author] + people
        names = []
        decks = []
        hps = []
        bps = []

        for p in people:
            deck = [f"{c[2]}.{c[1]}" for c in dm.get_user_deck(p.id)]
            random.shuffle(deck)
            decks.append(deck)

            hp = round((100 * u.SCALE[1] ** math.floor(level / 2)) * u.SCALE[0])
            hps.append([hp, 0, hp, 0, 0])

            bps.append(json.loads(dm.get_user_inventory(id_)))
            names.append(p.name)

        req_msg = "Hey " + '\n'.join(c.mention for c in people[1:]) + "!\n"
        if gamble_medals > 0:
            req_msg += f"{a.mention} wants to battle with {gamble_medals} {u.ICON['medal']}!\n"
        else:
            req_msg += f"{a.mention} wants to have a friendly battle!\n"

        view = PvpInvite(ctx.author, people, 6)
        await msg.edit(content=req_msg, view=view)
        await view.wait()

        if not view.start:
            return

        teams = {k: [m.id for m in v] for k, v in view.teams.items()}
        joined_users = list(view.user_team)
        counter = 1
        for t in teams:  # initialize the pvp fields
            for id_ in teams[t]:
                k = c_ids.index(id_)
                teams[t][teams[t].index(id_)] = counter
                c_ids.append(c_ids.pop(k))
                names.append(names.pop(k))
                decks.append(decks.pop(k))
                hps.append(hps.pop(k))
                bps.append(bps.pop(k))
                counter += 1

        if gamble_medals > 0:
            desc = " vs ".join([str(x) for x in names[len(c_ids) - len(joined_users):]])
            s = "s" if gamble_medals > 1 else ""
            embed = discord.Embed(
                title=f"A {gamble_medals}-Medal{s} Battle Just Started!",
                description=desc,
                color=discord.Color.gold()
            )
        else:
            embed = discord.Embed(
                title="A Friendly Battle Just Started!",
                description=" vs ".join([str(x) for x in names]),
                color=discord.Color.gold()
            )

        await ctx.send(embed=embed)

        # START THE BATTLE!
        offset = len(c_ids) - len(joined_users)
        dd = BattleData(
            teams,  # teams
            names[offset:],  # [str(x) for x in challenger_names], #players
            c_ids[offset:],  # players ids
            decks[offset:],  # decks
            bps[offset:],  # backpack
            hps[offset:],  # hps
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

            for p in range(len(dd.descriptions.info)):
                dd.descriptions.info[p + 1] = []
                if "freeze" in dd.effects.info[p + 1]:
                    if dd.effects.info[p + 1]["freeze"] >= 0:
                        dd.freeze_skips.info[p + 1] = True

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
                    for p in players:
                        index = list(dd.p_ids.info.values()).index(p) + 1
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

                        for id_ in range(dd.hand_sizes.info[index]):
                            if not dd.decks.info[index][id_] in [".".join(x.split(".")[0:2]) for x in
                                                               dd.used_cards.info[index]]:
                                card = dd.decks.info[index][id_].split(".")

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

                        for id_ in range(dd.hand_sizes.info[index]):
                            if not dd.decks.info[index][id_] in [".".join(x.split(".")[0:2]) for x in
                                                               dd.used_cards.info[index]]:
                                card = dd.decks.info[index][id_].split(".")

                                if "on_hand" in u.cards_dict(card[0], card[1]):
                                    dd.execute_card_offense(int(card[0]), card[1], index, index, "on_hand")

                        for id_ in range(len(dd.move_numbers.info[index])):
                            t = int(str(dd.move_numbers.info[index][id_])[0]) - id_ + z
                            card = dd.decks.info[index][t - 1].split('.')
                            card_info = u.cards_dict(card[0], card[1])

                            if not card[1] in dd.temporary_cards:
                                if "rewrite" in card_info:
                                    re_name = u.cards_dict(1, card[1])['rewrite']
                                    dd.descriptions.info[index].append(
                                        f"*[{u.rarity_cost(card[1])}] {card[1]} lv:{card[0]}* rewritten as *[{u.rarity_cost(re_name)}] {re_name} lv:{card[0]}*")
                                    dd.decks.info[index][t - 1] = dd.decks.info[index][t - 1].split(".")[0] + "." + \
                                                                  card_info["rewrite"]

                                if "stay" in card_info:
                                    if random.randint(1, 100) <= card_info['stay']:
                                        z += 1
                                        dd.descriptions.info[index].append(
                                            f"*[{u.rarity_cost(card[1])}] {card[1]} lv:{card[0]}* stayed in your hand!")
                                    else:
                                        dd.decks.info[index].insert(len(dd.decks.info[index]),
                                                                    dd.decks.info[index].pop(t - 1))
                                else:
                                    dd.decks.info[index].insert(len(dd.decks.info[index]),
                                                                dd.decks.info[index].pop(t - 1))
                            else:
                                if "stay" in card_info:
                                    if random.randint(1, 100) <= card_info['stay']:
                                        z += 1
                                        dd.descriptions.info[index].append(
                                            f"*[{u.rarity_cost(card[1])}] {card[1]} lv:{card[0]}* stayed in your hand!")
                                    else:
                                        dd.decks.info[index].pop(t - 1)
                                else:
                                    dd.decks.info[index].pop(t - 1)

                        dd.hand_sizes.info[index] -= len(dd.move_numbers.info[index]) - z - 1
                    await replied_message.delete()

            if dd.afk == 0:
                cards_length = [len(i) for i in list(dd.used_cards.info.values())]
                cards_length.sort()

                for t in dd.item_used.info:
                    if dd.item_used.info[t][0].title() != "None":
                        dd.execute_card_defense(-1, dd.item_used.info[t][0].title(), t, dd.item_used.info[t][1])
                        dd.execute_card_offense(-1, dd.item_used.info[t][0].title(), t, dd.item_used.info[t][1])
                        dd.execute_card_special(-1, dd.item_used.info[t][0].title(), t, dd.item_used.info[t][1])

                for t in range(cards_length[-1]):
                    for id_ in range(1, len(dd.used_cards.info) + 1):
                        if len(dd.used_cards.info[id_]) > t:
                            dd.execute_card_defense(int(dd.used_cards.info[id_][t].split(".")[0]),
                                                    dd.used_cards.info[id_][t].split(".")[1], id_,
                                                    int(dd.used_cards.info[id_][t].split(".")[2]))

                    for id_ in range(1, len(dd.used_cards.info) + 1):
                        if len(dd.used_cards.info[id_]) > t:
                            dd.execute_card_offense(int(dd.used_cards.info[id_][t].split(".")[0]),
                                                    dd.used_cards.info[id_][t].split(".")[1], id_,
                                                    int(dd.used_cards.info[id_][t].split(".")[2]))

                    for id_ in range(1, len(dd.used_cards.info) + 1):
                        if len(dd.used_cards.info[id_]) > t:
                            dd.execute_card_special(int(dd.used_cards.info[id_][t].split(".")[0]),
                                                    dd.used_cards.info[id_][t].split(".")[1], id_,
                                                    int(dd.used_cards.info[id_][t].split(".")[2]))

                for p in range(1, len(dd.effects.info) + 1):
                    dd.execute_effects(p)

                for p in range(1, len(dd.used_cards.info) + 1):
                    dd.used_cards.info[p] = []

                for p in range(1, len(dd.players.info) + 1):
                    if dd.stored_energies.info[p] + math.ceil(dd.turns / 4) > 12:
                        dd.stored_energies.info[p] = 12
                    else:
                        dd.stored_energies.info[p] += math.ceil(dd.turns / 4)
                    dd.hps.info[p][0] -= dd.total_damages.info[p]
                    if dd.hps.info[p][0] > dd.hps.info[p][2]:
                        dd.hps.info[p][0] = dd.hps.info[p][2]
                    if dd.hps.info[p][0] <= 0:
                        dd.hps.info[p][0] = 0
                    dd.item_used.info[p] = ["None", p]
                    dd.multipliers.info[p] = [0, 0, 0, 0, 0]
                    dd.total_damages.info[p] = 0
                    dd.hps.info[p][3] = 0
                    dd.hps.info[p][4] = 0
                    dd.freeze_skips.info[p] = False

                if dd.turns >= 50:
                    for p in range(1, len(dd.players.info) + 1):
                        dd.hps.info[p][2] = 0
                        dd.hps.info[p][0] = 0

        if dd.afk <= 6:
            winner = dd.teams[dd.afk]
            await stats_msg.edit(embed=dd.show_stats())
            await hands_msg.edit(embed=dd.show_hand())

            medal_amt = gamble_medals * (len(dd.players.info) - len(winner)) // len(winner)
            xp_amt = dd.turns * 2
            for p in dd.p_ids.info:
                id_ = dd.p_ids.info[p]
                if p in winner:
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
                                f"Each winner gained {medal_amt} medals\n"
                                f"Everyone else lost {gamble_medals} medals\n"
                                f"Everyone gained {dd.turns * 2} XP",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="Battle Ended!",
                    description=f"**Team {dd.pps[dd.afk]} won the friendly battle!**\n\n"
                                f"Everyone gained {dd.turns * 2} XP",
                    color=discord.Color.green()
                )
            
            embed.set_footer(f"This battle took {dd.turns} turns")
            await ctx.send(embed=embed)

        else:
            await stats_msg.edit(embed=dd.show_stats())
            await hands_msg.edit(embed=dd.show_hand())

            xp_amt = dd.turns * 2
            for p in dd.p_ids.info:
                id_ = dd.p_ids.info[p]
                dm.set_user_exp(id_, dm.get_user_exp(id_) + xp_amt)

            embed = discord.Embed(
                title="Battle Ended!",
                description=f"**It's a Tie!**\n\n"
                            f"No one gained or lost any medals!\n"
                            f"Everyone gained {dd.turns * 2} experience points",
                color=discord.Color.green()
            )
            embed.set_footer(f"This battle took {dd.turns} turns")
            await ctx.send(embed=embed)

        for u_ in set(dd.p_ids.info.values()):
            del dm.queues[u_]


async def setup(bot):
    await bot.add_cog(Pvp(bot))
