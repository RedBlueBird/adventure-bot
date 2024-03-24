import asyncio
import random
import math
import typing as t

import discord
from discord.ext import commands

import db
from helpers import util as u, resources as r, checks
from helpers.battle import BattleData
from views.battle import RaidInvite, Select


class Raid(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.hybrid_command(description="Band with other players to fight an OP boss!")
    @checks.level_check(4)
    @checks.is_registered()
    @checks.not_preoccupied("raiding a boss")
    async def raid(self, ctx: commands.Context, difficulty: t.Literal[1, 2, 3, 4]):
        a = ctx.author

        members = 2
        view = Select(a, members - 1, members - 1)
        msg = await ctx.reply(view=view)
        while True:
            await view.wait()
            people = view.selected
            for p in people:
                db_p = db.Player.get_by_id(p.id)

                level_req = 4
                if db_p.level < level_req:
                    await ctx.reply(f"{p.mention} isn't level {level_req} yet!")
                    break

                if db_p.raid_tickets == 0:
                    await ctx.reply(f"{p.mention} doesn't have any raid tickets!")
                    break

                if len(db.get_deck(db_p.id)) != 12:
                    await ctx.reply(f"{p.mention} doesn't have 12 cards in their deck!")
                    break
            else:
                break

            view = Select(a)
            await msg.edit(view=view)

        people: list[discord.Member] = [ctx.author] + people
        req_msg = (
            "Hey "
            + "\n".join(c.mention for c in people[1:])
            + "!\n"
            f"Wanna raid a level {difficulty} boss with {a.mention}?\n"
            f"Keep in mind that you'll need one {r.ICONS['tick']}."
        )
        view = RaidInvite(ctx.author, people)
        await msg.edit(content=req_msg, view=view)
        await view.wait()

        if not view.start:
            return

        ids = []
        names = []
        decks = []
        hps = []
        bps = []
        db_vals = {}
        for p in people:
            ids.append(p.id)
            names.append(p.name)
            db_vals[p.id] = db.Player.get_by_id(p.id)

            deck = [f"{c.name}.{c.level}" for c in db.get_deck(p.id)]
            random.shuffle(deck)
            decks.append(deck)

            hp = u.level_hp(db_vals[p.id].level)
            hps.append([hp, 0, hp, 0, 0])

            bps.append(db_vals[p.id].inventory)

        for i in ids:
            if i != ctx.author.id:
                db.lock_user(i, "raid", "raiding a boss")

        embed = discord.Embed(
            title="A Raid Has Begun!",
            description=", ".join([str(x) for x in names]),
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)

        levels = [1, 15, 20, 30, 45][difficulty]
        enemies = ["Lich Lord"]
        enemy_stats = [r.mob(e, levels) for e in enemies]
        ad_decks = [
            random.sample(
                [f"{levels}.{x}" for x in e.deck],
                len(e.deck),
            )
            for e in enemy_stats
        ]
        ad_hps = [[e.health, 0, e.health, 0, 0] for e in enemy_stats]

        # Initialize the battlefield
        teams = {
            1: [i + 1 for i in range(members)],
            2: [i + members + 1 for i in range(len(enemies))],
        }
        dd = BattleData(
            teams=teams,
            players=names + enemies,
            p_ids=ids + [123 for _ in range(len(enemies))],
            decks=decks + ad_decks,
            backpacks=bps + [{} for _ in range(len(enemies))],
            hps=hps + ad_hps,
            stamina=[35 for _ in range(members)] + [e.stamina for e in enemy_stats],
            counts=len(enemies) + members,
        )

        loading_embed = discord.Embed(title="Loading...", description=r.ICONS["load"])
        stats_msg = await ctx.send(embed=loading_embed)
        hands_msg = await ctx.send(embed=loading_embed)

        def stats_check() -> bool:
            alive = 0
            alive_list = []

            for team in dd.teams:
                for p in dd.teams[team]:
                    if dd.hps.info[p][0] > 0 and dd.staminas.info[p] > 0:
                        alive += 1
                        alive_list.append(team)
                        break

            if alive < 2:
                if not alive_list:
                    dd.afk = 7
                else:
                    dd.afk = alive_list[0]
            return alive > 1

        # region Battle simulation
        while stats_check() and dd.afk == 0:
            dd.turns += 1
            hand_embed = dd.show_hand()
            stats_embed = dd.show_stats()
            await stats_msg.edit(embed=stats_embed)
            await hands_msg.edit(embed=hand_embed)

            # Process the freeze effects for everyone
            for i in range(len(dd.descriptions.info)):
                dd.descriptions.info[i + 1] = []
                if "freeze" in dd.effects.info[i + 1]:
                    if dd.effects.info[i + 1]["freeze"] >= 0:
                        dd.freeze_skips.info[i + 1] = True

            players = []
            for ind in range(1, members + 1):
                if (
                    dd.afk == 0
                    and not dd.freeze_skips.info[ind]
                    and dd.hps.info[ind][0] > 0
                    and dd.staminas.info[ind] > 0
                ):
                    players.append(dd.p_ids.info[ind])

                elif dd.hps.info[ind][0] < 0 or dd.staminas.info[ind] < 0:
                    dd.descriptions.info[ind].append(f"•{r.ICONS['dead']}")
                    dd.effects.info[ind] = {}

            print(players)
            # Process player commands
            while players:
                try:
                    replied_message = await self.bot.wait_for(
                        "message",
                        timeout=120.0,
                        check=checks.valid_reply("", people, ctx.channel),
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
                    msg = dd.interpret_message(
                        replied_message.content[len(r.PREF) :],
                        str(dd.players.info[index]),
                        index,
                    )

                    if type(msg) is str and msg not in [
                        "skip",
                        "flee",
                        "refresh",
                        "backpack",
                    ]:
                        await ctx.send(msg)

                    elif msg == "refresh":
                        stats_msg = await ctx.send(embed=stats_embed)
                        hands_msg = await ctx.send(embed=hand_embed)

                    elif msg == "skip":
                        # dd.staminas.infos[index] += 1
                        players.remove(replied_message.author.id)

                        for y in range(dd.hand_sizes.info[index]):
                            if dd.decks.info[index][y] not in [
                                ".".join(x.split(".")[0:2]) for x in dd.used_cards.info[index]
                            ]:
                                card = dd.decks.info[index][y].split(".")

                                if "on_hand" in u.cards_dict(card[0], card[1]):
                                    dd.execute_card_offense(
                                        int(card[0]), card[1], index, index, "on_hand"
                                    )

                        if not dd.hand_sizes.info[index] == 6:
                            dd.hand_sizes.info[index] += 1

                        dd.descriptions.info[index].append(f"{r.ICONS['ski']}{r.ICONS['kip']}\n")

                    elif msg == "flee":
                        players.remove(replied_message.author.id)
                        dd.hps.info[index][0] = 0
                        dd.staminas.info[index] = 0
                        dd.descriptions.info[index].append(f"{r.ICONS['fle']}{r.ICONS['lee']}\n")

                    elif msg == "backpack":
                        await ctx.send(
                            embed=u.container_embed(dd.backpacks.info[index], "Backpack")
                        )
                    else:
                        players.remove(replied_message.author.id)
                        dd.staminas.info[index] -= len(msg)
                        dd.move_numbers.info[index] = msg
                        dd.used_cards.info[index] = [
                            dd.decks.info[index][int(str(x)[0]) - 1] + "." + str(x)[1:]
                            for x in dd.move_numbers.info[index]
                        ]
                        dd.stored_energies.info[index] -= sum([
                            u.cards_dict(
                                int(dd.decks.info[index][int(str(x)[0]) - 1].split(".")[0]),
                                dd.decks.info[index][int(str(x)[0]) - 1].split(".")[1],
                            )["cost"]
                            for x in dd.move_numbers.info[index]
                        ])
                        dd.move_numbers.info[index].sort()
                        z = 0

                        for y in range(dd.hand_sizes.info[index]):
                            if not dd.decks.info[index][y] in [
                                ".".join(x.split(".")[0:2]) for x in dd.used_cards.info[index]
                            ]:
                                card = dd.decks.info[index][y].split(".")

                                if "on_hand" in u.cards_dict(card[0], card[1]):
                                    dd.execute_card_offense(
                                        int(card[0]), card[1], index, index, "on_hand"
                                    )

                        for y in range(len(dd.move_numbers.info[index])):
                            x = int(str(dd.move_numbers.info[index][y])[0]) - y + z
                            card = dd.decks.info[index][x - 1].split(".")
                            card_info = u.cards_dict(card[0], card[1])

                            if card[1] not in dd.temporary_cards:
                                if "rewrite" in card_info:
                                    re_name = u.cards_dict(1, card[1])["rewrite"]
                                    dd.descriptions.info[index].append(
                                        f"*[{u.rarity_cost(card[1])}]"
                                        f" {card[1]} lv:{card[0]}* rewritten as"
                                        f" *[{u.rarity_cost(re_name)}]"
                                        f" {re_name} lv:{card[0]}*"
                                    )
                                    dd.decks.info[index][x - 1] = (
                                        dd.decks.info[index][x - 1].split(".")[0]
                                        + "."
                                        + card_info["rewrite"]
                                    )

                                if "stay" in card_info:
                                    if random.randint(1, 100) <= card_info["stay"]:
                                        z += 1
                                        dd.descriptions.info[index].append(
                                            f"*[{u.rarity_cost(card[1])}]"
                                            f" {card[1]} lv:{card[0]}* stayed in your"
                                            " hand!"
                                        )
                                    else:
                                        dd.decks.info[index].insert(
                                            len(dd.decks.info[index]),
                                            dd.decks.info[index].pop(x - 1),
                                        )
                                else:
                                    dd.decks.info[index].insert(
                                        len(dd.decks.info[index]),
                                        dd.decks.info[index].pop(x - 1),
                                    )
                            else:
                                if "stay" in card_info:
                                    if random.randint(1, 100) <= card_info["stay"]:
                                        z += 1
                                        dd.descriptions.info[index].append(
                                            f"*[{u.rarity_cost(card[1])}]"
                                            f" {card[1]} lv:{card[0]}* stayed in your"
                                            " hand!"
                                        )
                                    else:
                                        dd.decks.info[index].pop(x - 1)
                                else:
                                    dd.decks.info[index].pop(x - 1)

                        dd.hand_sizes.info[index] -= len(dd.move_numbers.info[index]) - z - 1
                    await replied_message.delete()

            alive_players = []
            for ind in range(1, members + 1):
                if dd.afk == 0 and dd.hps.info[ind][0] > 0 and dd.staminas.info[ind] > 0:
                    alive_players.append(ind)

            for e_index in range(members + 1, len(enemies) + members + 1):
                if (
                    dd.afk == 0
                    and dd.freeze_skips.info[e_index] == False
                    and dd.hps.info[e_index][0] > 0
                    and dd.staminas.info[e_index] > 0
                ):
                    rng_move = random.randint(1, dd.hand_sizes.info[e_index])
                    if (
                        dd.stored_energies.info[e_index]
                        >= u.cards_dict(
                            int(dd.decks.info[e_index][rng_move - 1].split(".")[0]),
                            dd.decks.info[e_index][rng_move - 1].split(".")[1],
                        )["cost"]
                    ):
                        msg = [rng_move]
                        for x in range(3):
                            rng_move = random.randint(1, dd.hand_sizes.info[e_index])
                            if (
                                dd.stored_energies.info[e_index]
                                >= sum([
                                    u.cards_dict(
                                        int(dd.decks.info[e_index][x - 1].split(".")[0]),
                                        dd.decks.info[e_index][x - 1].split(".")[1],
                                    )["cost"]
                                    for x in msg
                                ])
                                + u.cards_dict(
                                    int(dd.decks.info[e_index][rng_move - 1].split(".")[0]),
                                    dd.decks.info[e_index][rng_move - 1].split(".")[1],
                                )["cost"]
                            ):
                                msg.append(rng_move)
                    else:
                        msg = "skip"
                    if msg == "skip":
                        # dd.stamina[1] += 1
                        for y in range(dd.hand_sizes.info[e_index]):
                            if not dd.decks.info[e_index][y] in dd.used_cards.info[e_index]:
                                if "on_hand" in u.cards_dict(
                                    dd.decks.info[e_index][y].split(".")[0],
                                    dd.decks.info[e_index][y].split(".")[1],
                                ):
                                    dd.execute_card_offense(
                                        int(dd.decks.info[e_index][y].split(".")[0]),
                                        dd.decks.info[e_index][y].split(".")[1],
                                        e_index,
                                        e_index,
                                        "on_hand",
                                    )
                        if not dd.hand_sizes.info[e_index] == 6:
                            dd.hand_sizes.info[e_index] += 1
                        dd.descriptions.info[e_index].insert(
                            len(dd.descriptions.info[e_index]),
                            f"{r.ICONS['ski']}{r.ICONS['kip']}\n",
                        )
                        correct_format = True
                    elif msg == "flee":
                        dd.afk = len(dd.players.info) + e_index
                        break
                    else:
                        dd.staminas.info[e_index] -= 1
                        dd.move_numbers.info[e_index] = list(dict.fromkeys(msg))
                        correct_format = True
                        defense_cards = [
                            "shield",
                            "absorb",
                            "heal",
                            "aid",
                            "aim",
                            "relic",
                            "meditate",
                            "heavy shield",
                            "reckless assault",
                            "seed",
                            "sprout",
                            "sapling",
                            "holy tree",
                            "cache",
                            "blessed clover",
                            "dark resurrection",
                            "battle cry",
                            "enrage",
                            "devour",
                            "reform",
                            "harden scales",
                            "prideful flight",
                            "rejuvenate",
                            "regenerate",
                        ]
                        # a = [print(dd.decks.info[e_index][x - 1].lower().split(".")[1]) for x in dd.move_numbers.info[e_index]]
                        dd.used_cards.info[e_index] = [
                            (
                                f"{dd.decks.info[e_index][x - 1]}.{e_index}"
                                if dd.decks.info[e_index][x - 1].lower().split(".")[1]
                                in defense_cards
                                else (
                                    f"{dd.decks.info[e_index][x - 1]}.{random.choice(dd.decks.info[e_index][x - 1])}"
                                )
                            )
                            for x in dd.move_numbers.info[e_index]
                        ]
                        dd.stored_energies.info[e_index] -= sum([
                            u.cards_dict(
                                int(dd.decks.info[e_index][x - 1].split(".")[0]),
                                dd.decks.info[e_index][x - 1].split(".")[1],
                            )["cost"]
                            for x in dd.move_numbers.info[e_index]
                        ])
                        dd.move_numbers.info[e_index].sort()
                        z = 0
                        for y in range(dd.hand_sizes.info[e_index]):
                            if not dd.decks.info[e_index][y] in dd.used_cards.info[e_index]:
                                if "on_hand" in u.cards_dict(
                                    dd.decks.info[e_index][y].split(".")[0],
                                    dd.decks.info[e_index][y].split(".")[1],
                                ):
                                    dd.execute_card_offense(
                                        int(dd.decks.info[e_index][y].split(".")[0]),
                                        dd.decks.info[e_index][y].split(".")[1],
                                        e_index,
                                        e_index,
                                        "on_hand",
                                    )
                        for y in range(len(dd.move_numbers.info[e_index])):
                            x = dd.move_numbers.info[e_index][y] - y + z
                            card = dd.decks.info[e_index][x - 1].split(".")
                            card_info = u.cards_dict(card[0], card[1])

                            if not card[1] in dd.temporary_cards:
                                if "rewrite" in card_info:
                                    re_name = u.cards_dict(1, card[1])["rewrite"]
                                    dd.descriptions.info[e_index].append(
                                        f"*{card[1]}* rewritten as *{re_name}*"
                                    )
                                    dd.decks.info[e_index][x - 1] = (
                                        card[0] + "." + card_info["rewrite"]
                                    )
                                if "stay" in card_info:
                                    if random.randint(1, 100) <= card_info["stay"]:
                                        z += 1
                                        dd.descriptions.info[e_index].append(
                                            f"*[{u.rarity_cost(card[1])}]"
                                            f" {card[1]} lv:{card[0]}* stayed in your"
                                            " hand!"
                                        )
                                    # dd.new_line(e_index)
                                    else:
                                        dd.decks.info[e_index].insert(
                                            len(dd.decks.info[e_index]),
                                            dd.decks.info[e_index].pop(x - 1),
                                        )
                                else:
                                    dd.decks.info[e_index].insert(
                                        len(dd.decks.info[e_index]),
                                        dd.decks.info[e_index].pop(x - 1),
                                    )
                            else:
                                if "stay" in card_info:
                                    if random.randint(1, 100) <= card_info["stay"]:
                                        z += 1
                                        dd.descriptions.info[e_index].append(
                                            f"*[{u.rarity_cost(card[1])}]"
                                            f" {card[1]} lv:{card[0]}* stayed in your"
                                            " hand!"
                                        )
                                    # dd.new_line(e_index)
                                    else:
                                        dd.decks.info[e_index].pop(x - 1)
                                else:
                                    dd.decks.info[e_index].pop(x - 1)
                        dd.hand_sizes.info[e_index] -= len(dd.move_numbers.info[e_index]) - z - 1
                # dd.deck_index.insert(dd.move_numbere_index - 1, dd.deck_index.pop(dd.hand_size[1]-1))
                elif dd.hps.info[e_index][0] <= 0 or dd.staminas.info[e_index] <= 0:
                    dd.descriptions.info[e_index].append(f"•{r.ICONS['dead']}")
                    dd.effects.info[e_index] = {}
            if dd.afk == 0:
                cards_length = [len(i) for i in list(dd.used_cards.info.values())]
                cards_length.sort()
                for x in dd.item_used.info:
                    if dd.item_used.info[x][0] != "None":
                        dd.execute_card_defense(
                            -1, dd.item_used.info[x][0], x, dd.item_used.info[x][1]
                        )
                        dd.execute_card_offense(
                            -1, dd.item_used.info[x][0], x, dd.item_used.info[x][1]
                        )
                        dd.execute_card_special(
                            -1, dd.item_used.info[x][0], x, dd.item_used.info[x][1]
                        )
                for x in range(cards_length[-1]):
                    for y in range(1, len(dd.used_cards.info) + 1):
                        if len(dd.used_cards.info[y]) > x:
                            dd.execute_card_defense(
                                int(dd.used_cards.info[y][x].split(".")[0]),
                                dd.used_cards.info[y][x].split(".")[1],
                                y,
                                int(dd.used_cards.info[y][x].split(".")[2]),
                            )
                    for y in range(1, len(dd.used_cards.info) + 1):
                        if len(dd.used_cards.info[y]) > x:
                            dd.execute_card_offense(
                                int(dd.used_cards.info[y][x].split(".")[0]),
                                dd.used_cards.info[y][x].split(".")[1],
                                y,
                                int(dd.used_cards.info[y][x].split(".")[2]),
                            )
                    for y in range(1, len(dd.used_cards.info) + 1):
                        if len(dd.used_cards.info[y]) > x:
                            dd.execute_card_special(
                                int(dd.used_cards.info[y][x].split(".")[0]),
                                dd.used_cards.info[y][x].split(".")[1],
                                y,
                                int(dd.used_cards.info[y][x].split(".")[2]),
                            )
                for i in range(1, len(dd.effects.info) + 1):
                    dd.execute_effects(i)
                for i in range(1, len(dd.used_cards.info) + 1):
                    dd.used_cards.info[i] = []
                for i in range(1, len(dd.players.info) + 1):
                    energy_lags = r.mob(dd.players.info[i]).energy_lag if i > members else 4
                    if dd.stored_energies.info[i] + math.ceil(dd.turns / energy_lags) > 12:
                        dd.stored_energies.info[i] = 12
                    else:
                        dd.stored_energies.info[i] += math.ceil(dd.turns / energy_lags)
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
        # endregion

        loot_factor = [1, 2, 4, 6, 8][difficulty]
        if dd.afk <= 6:
            if dd.afk == 1:
                await stats_msg.edit(embed=dd.show_stats())
                await hands_msg.edit(embed=dd.show_hand())

                coin_loot = loot_factor * sum(
                    [random.randint(*e.death_rwd.coins) for e in enemy_stats]
                )
                exp_loot = loot_factor * sum(
                    [random.randint(*e.death_rwd.exps) for e in enemy_stats]
                )
                gem_loot = (
                    loot_factor
                    * sum([random.randint(*e.death_rwd.gems) for e in enemy_stats])
                    // 100
                )

                death_award_msg = [
                    f"+{coin_loot} golden coins",
                    f"+{exp_loot} XP",
                    f"+{gem_loot} shiny gems!",
                ]

                for player in db_vals.values():
                    player.coins += coin_loot
                    player.xp += exp_loot
                    player.gems += gem_loot
                    player.raid_tickets -= 1
                    player.save()

                embed = discord.Embed(
                    title="Battle Ended!",
                    description=(
                        "**You defeated"
                        f" {','.join(list(dict.fromkeys(enemies)))}!**\n\nEveryone"
                        " gained: "
                    )
                    + "\n".join(death_award_msg),
                    color=discord.Color.green(),
                )
            else:
                await stats_msg.edit(embed=dd.show_stats())
                await hands_msg.edit(embed=dd.show_hand())

                exp_loot = dd.turns * 2
                for i in dd.p_ids.info:
                    player = db_vals[i]
                    player.xp += exp_loot
                    player.raid_tickets -= 1
                    player.save()

                embed = discord.Embed(
                    title="Battle Ended!",
                    description=f"**You failed to beat the boss!**\nEveryone gained {exp_loot} XP",
                    color=discord.Color.gold(),
                )
        else:
            await stats_msg.edit(embed=dd.show_stats())
            await hands_msg.edit(embed=dd.show_hand())

            exp_loot = dd.turns * 2
            for i in dd.p_ids.info:
                player = db_vals[i]
                player.xp += exp_loot
                player.raid_tickets -= 1
                player.save()

            embed = discord.Embed(
                title="Battle Ended!",
                description=f"**It's a Tie!**\nEveryone gained {exp_loot} XP",
                color=discord.Color.gold(),
            )

        embed.set_footer(text=f"This battle took {dd.turns} turns")
        await ctx.send(embed=embed)

        for i in ids:
            if i != ctx.author.id:
                db.lock_user(i, "raid", "raiding a boss")


async def setup(bot: commands.Bot):
    await bot.add_cog(Raid(bot))
