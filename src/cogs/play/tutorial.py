import asyncio
import math
import random
from copy import deepcopy

import discord
from discord.ext import commands

import resources as r
from helpers import checks
from helpers import util as u
from helpers.battle import BattleData
from views import Confirm


class Tutorial(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        aliases=["tutorials", "tutor"], description="New to the bot? Here's a tutorial!"
    )
    @checks.is_registered()
    @checks.not_preoccupied("learning how to play the bot")
    async def tutorial(self, ctx: commands.Context):
        author = ctx.author
        mention = author.mention
        a_id = author.id

        view = Confirm(ctx.author, "Yeah!", "No thanks.")
        start_msg = await ctx.reply(
            "Hello!\nYou want to learn the basics of fighting in this bot? :smiley:",
            view=view,
        )
        await view.wait()

        if view.value is None:
            await start_msg.edit(content="did you go afk? :weary:", view=None)
            return
        if not view.value:
            await start_msg.edit(content="oh well. :frowning:", view=None)
            return

        await start_msg.edit(content="Alright, let's get started then! :smile:", view=None)
        loading_embed_message = discord.Embed(title="Loading...", description=r.ICONS["load"])
        stats_msg = await ctx.send(embed=loading_embed_message)
        hand_msg = await ctx.send(embed=loading_embed_message)

        tutorial = deepcopy(r.TUTORIAL)
        tutorial["procedure"] = [msg.format(prefix=r.PREF) for msg in tutorial["procedure"]]
        tutorial["triggered_message"] = {
            step: [msg.format(prefix=r.PREF) for msg in msgs]
            for step, msgs in tutorial["triggered_message"].items()
        }
        tutorial["players"][0] = author
        tutorial["p_ids"][0] = a_id
        dd = BattleData(
            tutorial["teams"],
            tutorial["players"],
            tutorial["p_ids"],
            tutorial["decks"],
            tutorial["backpacks"],
            tutorial["hps"],
            tutorial["staminas"],
            tutorial["counts"],
        )
        dd.stored_energies.info[1] = tutorial["stored_energies"][0]
        dd.stored_energies.info[2] = tutorial["stored_energies"][1]
        dd.stored_energies.info[3] = tutorial["stored_energies"][2]
        procedure = tutorial["procedure"]
        expected_message = tutorial["expected_message"]
        expected_item = tutorial["expected_item"]
        triggered_message = tutorial["triggered_message"]
        buffs = tutorial["buffs"]
        enemy_moves = tutorial["enemy_moves"]
        step = 0

        await stats_msg.edit(embed=dd.show_stats())
        await hand_msg.edit(embed=dd.show_hand())

        view = Confirm(ctx.author, "Continue", "Exit tutorial")
        msg = await ctx.reply(procedure[step], view=view)
        while step < 4:
            await view.wait()
            if view.value is None:
                await msg.edit(content="how DAre you sLeEp dUring my lEcTuRe! :triumph:", view=None)
                return
            if not view.value:
                await msg.edit(content="You exited the tutorial! :cry:", view=None)
                return

            step += 1
            view = Confirm(ctx.author, "Continue", "Exit tutorial")
            await msg.edit(content=procedure[step], view=view)

        def check_status():
            alive = []
            for team in dd.teams:
                for p in dd.teams[team]:
                    if dd.hps.info[p][0] > 0 and dd.staminas.info[p] > 0:
                        alive.append(team)
                        break
            if not alive:
                dd.afk = 7
            elif len(alive) == 1:
                dd.afk = alive[0]
            return dd.afk == 0

        while check_status():
            triggered = 0
            is_turn_over = False
            while (
                not is_turn_over
                and dd.afk == 0
                and not dd.freeze_skips.info[1]
                and dd.hps.info[1][0] > 0
                and dd.staminas.info[1] > 0
            ):
                try:
                    reply = await self.bot.wait_for(
                        "message",
                        timeout=120.0,
                        check=checks.valid_reply("", author, ctx.channel),
                    )
                    await reply.delete()
                except asyncio.TimeoutError:
                    dd.hps.info[1][0] = 0
                    dd.staminas.info[1] = 0
                    dd.descriptions.info[1].append("Went afk!")
                    await ctx.reply("did you go afk? :weary:")
                    return

                action = dd.interpret_message(
                    reply.content[len(r.PREF) :], str(dd.players.info[1]), 1
                )
                content = reply.content[len(r.PREF) :].lower()
                if content == "exit":
                    action = "exit"

                if action == "exit":
                    await ctx.send("You exited the tutorial!")
                    return

                elif (
                    step < 21
                    and action != "refresh"
                    and (
                        (expected_message[step] != "None" and action != expected_message[step])
                        or expected_item[step] != dd.item_used.info[1]
                    )
                ):
                    if triggered < len(triggered_message[step]):
                        await ctx.send(f"{mention}\n" + triggered_message[step][triggered])
                    else:
                        await ctx.send(f"{mention}\n" + triggered_message[step][-1])
                    triggered += 1
                elif action == "refresh":
                    stats_msg = await ctx.send(embed=dd.show_stats())
                    hand_msg = await ctx.send(embed=dd.show_hand())
                    if step == 7 or step == 13:
                        triggered = 0
                        step += 1
                        await msg.delete()
                        msg = await ctx.send(procedure[step])
                elif action == "backpack":
                    embed = u.container_embed(dd.backpacks.info[1], "Backpack")
                    embed.add_field(
                        name="Your Stats:",
                        value=(
                            f"Health - {str(dd.hps.info[1][0])}\nStamina -"
                            f" {str(dd.staminas.info[1])}"
                        ),
                    )
                    await ctx.send(embed=embed)
                    if step == 11 or step == 16:
                        triggered = 0
                        step += 1
                        await msg.delete()
                        msg = await ctx.send(procedure[step])
                elif action == "skip":
                    # dd.stamina[0] += 1
                    for y in range(dd.hand_sizes.info[1]):
                        if dd.decks.info[1][y] not in [
                            ".".join(x.split(".")[0:2]) for x in dd.used_cards.info[1]
                        ]:
                            if "on_hand" in u.cards_dict(
                                dd.decks.info[1][y].split(".")[0],
                                dd.decks.info[1][y].split(".")[1],
                            ):
                                dd.execute_card_offense(
                                    int(dd.decks.info[1][y].split(".")[0]),
                                    dd.decks.info[1][y].split(".")[1],
                                    1,
                                    1,
                                    "on_hand",
                                )
                    if dd.hand_sizes.info[1] != 6:
                        dd.hand_sizes.info[1] += 1
                    dd.descriptions.info[1].append(f"{r.ICONS['ski']}{r.ICONS['kip']}\n")
                    is_turn_over = True
                elif action == "flee":
                    for y in range(dd.hand_sizes.info[1]):
                        if dd.decks.info[1][y] not in [
                            ".".join(x.split(".")[0:2]) for x in dd.used_cards.info[1]
                        ]:
                            if "on_hand" in u.cards_dict(
                                dd.decks.info[1][y].split(".")[0],
                                dd.decks.info[1][y].split(".")[1],
                            ):
                                dd.execute_card_offense(
                                    int(dd.decks.info[1][y].split(".")[0]),
                                    dd.decks.info[1][y].split(".")[1],
                                    1,
                                    1,
                                    "on_hand",
                                )
                    if dd.hand_sizes.info[1] != 6:
                        dd.hand_sizes.info[1] += 1
                    if random.randint(1, 100) > 0:
                        dd.descriptions.info[1].append(
                            f"{r.ICONS['fle']}{r.ICONS['lee']} {r.ICONS['mi']}{r.ICONS['ss']}\n"
                        )
                    else:
                        dd.descriptions.info[1].append(f"{r.ICONS['fle']}{r.ICONS['lee']}\n")
                        dd.afk = 8
                    if step == 20:
                        try:
                            dd.decks.info[3][dd.decks.info[3].index("20.Terminate")] = "4.Terminate"
                        except:
                            pass
                    is_turn_over = True
                elif type(action) is list:
                    dd.move_numbers.info[1] = action
                    dd.used_cards.info[1] = [
                        dd.decks.info[1][int(str(x)[0]) - 1] + "." + str(x)[1:]
                        for x in dd.move_numbers.info[1]
                    ]
                    dd.stored_energies.info[1] -= sum([
                        u.cards_dict(
                            int(dd.decks.info[1][int(str(x)[0]) - 1].split(".")[0]),
                            dd.decks.info[1][int(str(x)[0]) - 1].split(".")[1],
                        )["cost"]
                        for x in dd.move_numbers.info[1]
                    ])
                    dd.move_numbers.info[1].sort()
                    z = 0
                    for y in range(dd.hand_sizes.info[1]):
                        if dd.decks.info[1][y] not in [
                            ".".join(x.split(".")[0:2]) for x in dd.used_cards.info[1]
                        ]:
                            if "on_hand" in u.cards_dict(
                                dd.decks.info[1][y].split(".")[0],
                                dd.decks.info[1][y].split(".")[1],
                            ):
                                dd.execute_card_offense(
                                    int(dd.decks.info[1][y].split(".")[0]),
                                    dd.decks.info[1][y].split(".")[1],
                                    1,
                                    1,
                                    "on_hand",
                                )
                    for y in range(len(dd.move_numbers.info[1])):
                        x = int(str(dd.move_numbers.info[1][y])[0]) - y + z
                        card_info = u.cards_dict(
                            dd.decks.info[1][x - 1].split(".")[0],
                            dd.decks.info[1][x - 1].split(".")[1],
                        )
                        if dd.decks.info[1][x - 1].split(".")[1] not in dd.temporary_cards:
                            if "rewrite" in card_info:
                                re_name = u.cards_dict(1, dd.decks.info[1][x - 1].split(".")[1])[
                                    "rewrite"
                                ]
                                dd.descriptions.info[1].append(
                                    f"*{dd.decks.info[1][x - 1].split('.')[1]}*"
                                    f" rewritten as *{re_name}*"
                                )
                                dd.decks.info[1][x - 1] = (
                                    dd.decks.info[1][x - 1].split(".")[0]
                                    + "."
                                    + card_info["rewrite"]
                                )
                            if "stay" in card_info:
                                if random.randint(1, 100) <= card_info["stay"]:
                                    z += 1
                                    dd.descriptions.info[1].append(
                                        f"*[{u.rarity_cost(dd.decks.info[1][x - 1].split('.')[1])}]"
                                        f" {dd.decks.info[1][x - 1].split('.')[1]} lv:{dd.decks.info[1][x - 1].split('.')[0]}*"
                                        " stayed in your hand!"
                                    )
                                # dd.new_line(1)
                                else:
                                    dd.decks.info[1].insert(
                                        len(dd.decks.info[1]),
                                        dd.decks.info[1].pop(x - 1),
                                    )
                            else:
                                dd.decks.info[1].insert(
                                    len(dd.decks.info[1]), dd.decks.info[1].pop(x - 1)
                                )
                        else:
                            if "stay" in card_info:
                                if random.randint(1, 100) <= card_info["stay"]:
                                    z += 1
                                    dd.descriptions.info[1].append(
                                        f"*[{u.rarity_cost(dd.decks.info[1][x - 1].split('.')[1])}]"
                                        f" {dd.decks.info[1][x - 1].split('.')[1]} lv:{dd.decks.info[1][x - 1].split('.')[0]}*"
                                        " stayed in your hand!"
                                    )
                                # dd.new_line(1)
                                else:
                                    dd.decks.info[1].pop(x - 1)
                            else:
                                dd.decks.info[1].pop(x - 1)
                    dd.hand_sizes.info[1] -= len(dd.move_numbers.info[1]) - z - 1
                    is_turn_over = True
                else:
                    await ctx.send(action)

            for enemy in range(2, 4):
                enemy_action = None
                if (
                    dd.afk == 0
                    and not dd.freeze_skips.info[enemy]
                    and dd.hps.info[enemy][0] > 0
                    and dd.staminas.info[enemy] > 0
                ):
                    if step < 21:
                        enemy_action = enemy_moves[step][enemy - 2]
                    else:
                        rng_move = random.randint(1, dd.hand_sizes.info[enemy])
                        if (
                            dd.stored_energies.info[enemy]
                            >= u.cards_dict(
                                int(dd.decks.info[enemy][rng_move - 1].split(".")[0]),
                                dd.decks.info[enemy][rng_move - 1].split(".")[1],
                            )["cost"]
                        ):
                            enemy_action = [rng_move]
                            for x in range(3):
                                rng_move = random.randint(1, dd.hand_sizes.info[enemy])
                                if dd.stored_energies.info[enemy] >= (
                                    sum([
                                        u.cards_dict(
                                            int(dd.decks.info[enemy][x - 1].split(".")[0]),
                                            dd.decks.info[enemy][x - 1].split(".")[1],
                                        )["cost"]
                                        for x in enemy_action
                                    ])
                                    + u.cards_dict(
                                        int(dd.decks.info[enemy][rng_move - 1].split(".")[0]),
                                        dd.decks.info[enemy][rng_move - 1].split(".")[1],
                                    )["cost"]
                                ):
                                    enemy_action.append(rng_move)
                        else:
                            enemy_action = "skip"

                    if enemy_action == "skip":
                        # dd.stamina[1] += 1
                        for y in range(dd.hand_sizes.info[enemy]):
                            if dd.decks.info[enemy][y] not in dd.used_cards.info[enemy]:
                                if "on_hand" in u.cards_dict(
                                    dd.decks.info[enemy][y].split(".")[0],
                                    dd.decks.info[enemy][y].split(".")[1],
                                ):
                                    dd.execute_card_offense(
                                        int(dd.decks.info[enemy][y].split(".")[0]),
                                        dd.decks.info[enemy][y].split(".")[1],
                                        enemy,
                                        enemy,
                                        "on_hand",
                                    )
                        if not dd.hand_sizes.info[enemy] != 6:
                            dd.hand_sizes.info[enemy] += 1
                        dd.descriptions.info[enemy].insert(
                            len(dd.descriptions.info[enemy]),
                            f"{r.ICONS['ski']}{r.ICONS['kip']}\n",
                        )
                    elif enemy_action == "flee":
                        dd.afk = len(dd.players.info) + enemy
                        break
                    else:
                        dd.staminas.info[enemy] -= 1
                        dd.move_numbers.info[enemy] = list(dict.fromkeys(enemy_action))
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
                        dd.used_cards.info[enemy] = [
                            (
                                dd.decks.info[enemy][x - 1] + f".{enemy}"
                                if dd.decks.info[enemy][x - 1].lower().split(".")[1]
                                in defense_cards
                                else dd.decks.info[enemy][x - 1] + ".1"
                            )
                            for x in dd.move_numbers.info[enemy]
                        ]
                        dd.stored_energies.info[enemy] -= sum([
                            u.cards_dict(
                                int(dd.decks.info[enemy][x - 1].split(".")[0]),
                                dd.decks.info[enemy][x - 1].split(".")[1],
                            )["cost"]
                            for x in dd.move_numbers.info[enemy]
                        ])
                        dd.move_numbers.info[enemy].sort()
                        z = 0
                        for y in range(dd.hand_sizes.info[enemy]):
                            if dd.decks.info[enemy][y] not in dd.used_cards.info[enemy]:
                                if "on_hand" in u.cards_dict(
                                    dd.decks.info[enemy][y].split(".")[0],
                                    dd.decks.info[enemy][y].split(".")[1],
                                ):
                                    dd.execute_card_offense(
                                        int(dd.decks.info[enemy][y].split(".")[0]),
                                        dd.decks.info[enemy][y].split(".")[1],
                                        enemy,
                                        enemy,
                                        "on_hand",
                                    )
                        for y in range(len(dd.move_numbers.info[enemy])):
                            x = dd.move_numbers.info[enemy][y] - y + z
                            card_info = u.cards_dict(
                                dd.decks.info[enemy][x - 1].split(".")[0],
                                dd.decks.info[enemy][x - 1].split(".")[1],
                            )
                            if dd.decks.info[enemy][x - 1].split(".")[1] not in dd.temporary_cards:
                                if "rewrite" in card_info:
                                    re_name = u.cards_dict(
                                        1, dd.decks.info[enemy][x - 1].split(".")[1]
                                    )["rewrite"]
                                    dd.descriptions.info[enemy].append(
                                        f"*{dd.decks.info[enemy][x - 1].split('.')[1]}*"
                                        f" rewritten as *{re_name}*"
                                    )
                                    dd.decks.info[enemy][x - 1] = (
                                        dd.decks.info[enemy][x - 1].split(".")[0]
                                        + "."
                                        + card_info["rewrite"]
                                    )
                                if "stay" in card_info:
                                    if random.randint(1, 100) <= card_info["stay"]:
                                        z += 1
                                        dd.descriptions.info[enemy].append(
                                            f"*[{u.rarity_cost(dd.decks.info[enemy][x - 1].split('.')[1])}]"
                                            f" {dd.decks.info[enemy][x - 1].split('.')[1]} lv:{dd.decks.info[enemy][x - 1].split('.')[0]}*"
                                            " stayed in your hand!"
                                        )
                                    # dd.new_line(e_index)
                                    else:
                                        dd.decks.info[enemy].insert(
                                            len(dd.decks.info[enemy]),
                                            dd.decks.info[enemy].pop(x - 1),
                                        )
                                else:
                                    dd.decks.info[enemy].insert(
                                        len(dd.decks.info[enemy]),
                                        dd.decks.info[enemy].pop(x - 1),
                                    )
                            else:
                                if "stay" in card_info:
                                    if random.randint(1, 100) <= card_info["stay"]:
                                        z += 1
                                        dd.descriptions.info[enemy].append(
                                            f"*[{u.rarity_cost(dd.decks.info[enemy][x - 1].split('.')[1])}]"
                                            f" {dd.decks.info[enemy][x - 1].split('.')[1]} lv:{dd.decks.info[enemy][x - 1].split('.')[0]}*"
                                            " stayed in your hand!"
                                        )
                                    # dd.new_line(e_index)
                                    else:
                                        dd.decks.info[enemy].pop(x - 1)
                                else:
                                    dd.decks.info[enemy].pop(x - 1)
                        dd.hand_sizes.info[enemy] -= len(dd.move_numbers.info[enemy]) - z - 1
                # dd.decke_index.insert(dd.move_numbere_index - 1, dd.decke_index.pop(dd.hand_size[1]-1))
                elif dd.hps.info[enemy][0] <= 0 or dd.staminas.info[enemy] <= 0:
                    dd.descriptions.info[enemy].append(f"•{r.ICONS['dead']}")
                    dd.effects.info[enemy] = {}

            if dd.afk == 0:
                cards_length = [len(i) for i in list(dd.used_cards.info.values())]
                cards_length.sort()
                if step < 21:
                    for x in range(1, len(dd.multipliers.info) + 1):
                        dd.multipliers.info[x] = buffs[step][x - 1]
                for x in dd.item_used.info:
                    if dd.item_used.info[x][0].title() != "None":
                        dd.execute_card_defense(
                            -1,
                            dd.item_used.info[x][0].title(),
                            x,
                            dd.item_used.info[x][1],
                        )
                        dd.execute_card_offense(
                            -1,
                            dd.item_used.info[x][0].title(),
                            x,
                            dd.item_used.info[x][1],
                        )
                        dd.execute_card_special(
                            -1,
                            dd.item_used.info[x][0].title(),
                            x,
                            dd.item_used.info[x][1],
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

            if step < 21:
                step += 1
                await msg.delete()
                msg = await ctx.send(procedure[step])
            dd.turns += 1
            await stats_msg.edit(embed=dd.show_stats())
            await hand_msg.edit(embed=dd.show_hand())

            for i in range(len(dd.descriptions.info)):
                dd.descriptions.info[i + 1] = []
                if dd.effects.info[i + 1].get("freeze", -1) >= 0:
                    dd.freeze_skips.info[i + 1] = True

        dd.turns -= 1
        if dd.afk <= 6:
            winner = dd.teams[dd.afk]
            embed = discord.Embed(
                title="Battle Ended!",
                description=f"**Team {dd.pps[dd.afk]} won!** \n\nThis battle took {dd.turns} turns",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
            if winner == [1] and dd.hps.info[3][0] <= 0:
                step = 22
                final_step = 26
            elif winner == [1] and dd.staminas.info[3] <= 0:
                step = 35
                final_step = 38
                # badge stuff prone to change, left commented for now
                # badges = dm.get_user_badge(id)
                # badges |= (1 << 27)
                # dm.set_user_badge(id, badges)
            else:
                step = 27
                final_step = 29
        else:
            embed = discord.Embed(
                title="Battle Ended!",
                description=f"**It's a Tie!**\n\nThis battle took {dd.turns} turns",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
            step = 30
            final_step = 34

        await msg.delete()
        view = Confirm(ctx.author, "Continue", "Exit")
        msg = await ctx.send(procedure[step], view=view)
        while step < final_step:
            await view.wait()
            if view.value is None:
                await msg.edit(content="You went afk and the tutorial ended.", view=None)
            elif not view.value:
                await msg.edit(content="You exited the tutorial!", view=None)

            step += 1
            view = Confirm(ctx.author, "Continue", "Exit")
            await msg.edit(content=procedure[step], embed=None, view=view)


async def setup(bot):
    await bot.add_cog(Tutorial(bot))
