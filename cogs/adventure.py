import random
import math
import string
import os
import asyncio
import json
from copy import deepcopy

from PIL import Image
import discord
from discord.ext import commands

from helpers import db_manager as dm
from helpers import checks
import util as u

from helpers.battle import BattleData

with open('resources/text/hometown.json') as json_file:
    H_TOWN = json.load(json_file)
with open('resources/text/adventure.json') as json_file:
    ADVENTURES = json.load(json_file)


class Adventure(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="adventure", aliases=["ad", "adv"], brief="Go on an adventure!")
    @checks.is_registered()
    @checks.not_preoccupied("on an adventure")
    async def adventure(self, ctx: commands.Context):
        """Takes the player on an adventure."""
        mention = ctx.message.author.mention
        a_id = ctx.message.author.id
        dm.cur.execute("select * from adventuredatas where userid = " + str(a_id))
        a_datas = dm.cur.fetchall()
        dm.cur.execute("select * from playersinfo where userid = " + str(a_id))
        p_datas = list(dm.cur.fetchall()[0])
        p_hp = round((100 * u.SCALE[1] ** math.floor(p_datas[3] / 2)) * u.SCALE[0])
        p_max_hp = p_hp
        p_sta = 100
        p_distance = 0
        deck_slot = p_datas[17]
        db_deck = f"deck{deck_slot}"
        dm.cur.execute(f"select {db_deck}, badges from playersachivements where userid = " + str(a_id))
        result = dm.cur.fetchall()[0]
        mydeck = result[0].split(",")
        badges = result[1]
        dm.cur.execute(f"select card_name, card_level from cardsinfo where owned_user = '{a_id}' and id in ({str(mydeck)[1:-1]})")
        mydeck = dm.cur.fetchall()
        p_hand = random.sample([f"{x[1]}.{x[0]}" for x in mydeck], len(mydeck))
        p_hand_size = 4
        p_effect = {}
        raid_levels = 1

        # p_inv = {"teleportation stone":{"items":"x"}}
        p_inv = eval(a_datas[0][3])
        p_stor = eval(a_datas[0][5])
        p_position = a_datas[0][2]
        if a_datas[0][4] == 'false':
            show_map = False
        else:
            show_map = True
        show_map = False

        afk = False
        leave = False
        adventure = False

        # region utilities
        mini_games = {
            "fishing": {
                "rules": [
                    "Each bait cost 50 golden coins", "0% catch rate when above `1.000` second",
                    "10% when between `1.000` and `0.750`",
                    "20% when between `0.749` and `0.500`",
                    "40% when between `0.499` and `0.250`",
                    "60% when between `0.249` and `0.125`",
                    "80% when between `0.124` and `0.050`",
                    "100% when below `0.049`",
                    f"Type `{u.PREF}fish` to start"
                ],
                "image": "resources/img/fishing_map.png"
            },
            "coin flip": {
                "rules": [
                    "Each coin flip takes 50 golden coins",
                    "You gain golden coins when coin landed as what you expected",
                    "You lose golden coins when it didn't",
                    f"Type `{u.PREF}flip (head/tail/edge)` to start"
                ],
                "image": None
            },
            "blackjack": {
                "rules": [
                    "Each blackjack bet 50 golden coins",
                    "You keep drawing cards in a standard card deck without jokers",
                    "Get a total value as close as you can to 21 or exact 21 without go over",
                    "Every card is equal to its own face value",
                    "However, face cards are all worth 10",
                    "Aces can be worth both 1 and 11",
                    "You win if your cards have a higher value than "
                    "the dealer's if no one went above 21",
                    "You also win when the dealer went above 21 but you didn't",
                    "You tie when you both have same total value",
                    f"Type `{u.PREF}start` to start"
                ],
                "image": None
            }
        }

        def choices_list(choices):
            logs = []
            for x in choices:
                logs.append("**[" + str(len(logs) + 1) + "]** " + x)
            return " \n".join(logs[:])

        def mark_location(bg_pic, x, y):
            background = Image.open(f"resources/img/{bg_pic}.png")
            new_image = Image.open("resources/img/marker.png")
            background.paste(new_image, (10 + 32 * x, 32 * y), new_image)
            background.save(f"resources/img/{a_id}.png")
            return f"resources/img/{a_id}.png"

        def setup_minigame(game_name):
            logs = []
            for x in mini_games[game_name]["rules"]:
                logs.append("• " + x)
            embed = discord.Embed(title="Mini Game - " + str(game_name) + "!", description=None, color=discord.Color.gold())
            embed.add_field(name="Rules", value=" \n".join(logs[:]))
            embed.set_thumbnail(url=ctx.message.author.avatar.url)
            embed.set_footer(text=u.PREF + "exit -quit mini game")
            if show_map:
                if mini_games[game_name]["image"] is not None:
                    return [embed,
                            discord.File(mini_games[game_name]["image"], filename=mini_games[game_name]["image"])]
                else:
                    return [embed, None]
            elif not show_map:
                return [embed, None]
        # endregion

        # HOMETOWN EXPLORATION
        loading_embed_message = discord.Embed(title="Loading...", description=u.ICON['load'])
        adventure_msg = await ctx.send(embed=loading_embed_message)

        while not leave and not afk and not adventure:
            embed = discord.Embed(title=None, description="```" + H_TOWN[p_position]["description"] + "```", color=discord.Color.gold())
            embed.add_field(name="Choices", value=choices_list(H_TOWN[p_position]["choices"]))
            embed.set_thumbnail(url=ctx.message.author.avatar.url)
            # embed.set_image(r"attachment://resources/img/hometown_map.png")
            embed.set_footer(text=f"{u.PREF}exit | {u.PREF}map | {u.PREF}backpack | {u.PREF}home | {u.PREF}refresh")

            if show_map:
                await adventure_msg.edit(embed=embed, attachments=discord.File(f"resources/img/{a_id}.png"))
                os.remove(f"resources/img/{a_id}.png")
            else:
                await adventure_msg.edit(embed=embed)

            decision = 0

            while True:
                try:
                    msg_reply = await self.bot.wait_for("message", timeout=60.0,
                                                        check=checks.valid_reply([''], [ctx.message.author], [ctx.message.channel]))
                except asyncio.TimeoutError:
                    afk = True
                    await ctx.send(f"{mention}, you went idling and the adventure was ended.")
                    break

                try:
                    decision = abs(math.floor(int(msg_reply.content[len(u.PREF):])) + 1 - 1)
                except:
                    decision = 0
                    msg_reply = msg_reply.content[len(u.PREF):].lower()
                    if msg_reply == "exit":
                        leave = True
                        await ctx.send(f"{mention}, you quit this adventure")
                        break

                    elif msg_reply in ["map", "m"]:
                        if show_map:
                            show_map = False
                            await ctx.send(f"{mention}, map now hidden")
                        else:
                            show_map = True
                            await ctx.send(f"{mention}, map now shown")
                        show_map = False

                    elif msg_reply in ["bp", "backpack"]:
                        await ctx.send(embed=u.display_backpack(p_inv, ctx.message.author, "Backpack"))

                    elif msg_reply in ["home", "ho", "h"]:
                        p_position = "south street"
                        decision = 6

                    elif msg_reply in ['r', 'ref', 'refresh']:
                        if show_map:
                            adventure_msg = await ctx.send(embed=embed, file=discord.File(f"resources/img/{a_id}.png",
                                                                                          filename=mark_location("hometown_map", H_TOWN[p_position]["coordinate"][0], H_TOWN[p_position]["coordinate"][1])))
                            os.remove(f"resources/img/{a_id}.png")
                        else:
                            adventure_msg = await ctx.send(embed=embed, file=None)

                if not 1 <= decision <= len(H_TOWN[p_position]["choices"]):
                    if msg_reply not in ['exit', 'map', 'm', 'bp', 'backpack', 'home', 'h', 'ho', 'ref', 'r', 'refresh']:
                        await ctx.send("You can only enter numbers `1-" + str(len(H_TOWN[p_position]["choices"])) + "`!")
                else:
                    await msg_reply.delete()
                    break

            position = H_TOWN[p_position]["choices"][list(H_TOWN[p_position]["choices"])[decision - 1]]

            if position[1] == "self" and not afk and not leave:
                if position[0] in H_TOWN:
                    p_position = position[0]
                else:
                    await ctx.send(f"{mention} Sorry, this route is still in development! (stupid devs)")

            elif position[1] == "selling" and not afk and not leave:
                exiting = False
                # dm.cur.execute(f"select coins from playersinfo where userid = '{a_id}'")
                await adventure_msg.edit(content=f"`{u.PREF}sell (item_name) (amount)` to sell items \n"
                                                 f"`{u.PREF}backpack` to check your backpack \n"
                                                 f"`{u.PREF}info item (item_name)` to check the item sell price \n"
                                                 f"`{u.PREF}exit` to exit the shops",
                                         embed=u.display_backpack(p_inv, ctx.message.author, "Backpack"))
                while not exiting:
                    try:
                        msg_reply = await self.bot.wait_for("message", timeout=60.0,
                                                            check=checks.valid_reply([''], [ctx.message.author], [ctx.message.channel]))
                    except asyncio.TimeoutError:
                        exiting = True
                        await ctx.send(f"{mention} You went idle and decided to exit the shops")
                        break

                    msg_reply = msg_reply.content[len(u.PREF):].lower().split(" ")
                    if len(msg_reply) < 1:
                        continue

                    elif msg_reply[0] == "exit":
                        break

                    elif msg_reply[0] in ["backpack", "bp"]:
                        await ctx.send(embed=u.display_backpack(p_inv, ctx.message.author, "Backpack"))
                        continue

                    elif msg_reply[0] in ['r', 'ref', 'refresh']:
                        adventure_msg = await ctx.send(content=f"`{u.PREF}sell (item_name) (amount)` to sell items \n" +
                                                               f"`{u.PREF}backpack` to check your backpack \n" +
                                                               f"`{u.PREF}info item (item_name)` to check the item sell price \n" +
                                                               f"`{u.PREF}exit` to exit the shops",
                                                       embed=u.display_backpack(p_inv, ctx.message.author, "Backpack"))
                        continue

                    elif len(msg_reply) < 3:
                        continue

                    elif msg_reply[0] == "sell":
                        try:
                            item = u.items_dict(" ".join(msg_reply[1].split("_")[:]))
                            counts = max(int(msg_reply[2]), 1)
                            if not item['name'].lower() in p_inv:
                                await ctx.send("The selected item(s) is not in your backpack!")
                                continue

                            elif p_inv[item['name'].lower()]["items"] < counts:
                                await ctx.send("You don't have these much items in your backpack!")
                                continue

                            else:
                                dm.cur.execute(f"update playersinfo set coins = coins + {item['sell'] * counts} where userid = '{a_id}'")
                                dm.db.commit()
                                if p_inv[item['name'].lower()]["items"] == counts:
                                    del p_inv[item['name'].lower()]
                                else:
                                    p_inv[item['name'].lower()]["items"] -= counts
                                await ctx.send(f"You just sold **[{item['rarity']}/{item['weight']}] {item['name']} x{counts}** "
                                               f"for {item['sell'] * counts} {u.ICON['coin']}!")
                                continue
                        except:
                            continue

            elif position[1] == "buying" and not afk and not leave:
                exiting = False
                dm.cur.execute(f"select coins from playersinfo where userid = '{a_id}'")
                coins = dm.cur.fetchall()[0][0]
                purchasables = ["Forest Fruit", "Fruit Salad", "Raft", "Torch", "Herb", "Health Potion", "Power Potion",
                                "Large Health Potion",
                                "Large Power Potion", "Resurrection Amulet", "Teleportation Stone"]
                offers = []
                for offer in purchasables:
                    item = u.items_dict(offer)
                    offers.append(f"[{item['rarity']}/{item['weight']}] {item['name']} - {item['buy']} gc")
                embed = discord.Embed(title="Jessie's Shop:",
                                      description="I have all the essential items you're going to need! \n" + \
                                                  "```" + "\n".join(offers[:]) + "```",
                                      color=discord.Color.gold())
                await adventure_msg.edit(content=f"`{u.PREF}purchase (item_name) (amount)` to purchase items \n" +
                                                 f"`{u.PREF}backpack` to check your backpack \n" +
                                                 f"`{u.PREF}refresh` to resend the items price list \n" +
                                                 f"`{u.PREF}exit` to exit the shops",
                                         embed=embed)
                while not exiting:
                    try:
                        msg_reply = await self.bot.wait_for("message", timeout=60.0,
                                                            check=checks.valid_reply([''], [ctx.message.author], [ctx.message.channel]))
                    except asyncio.TimeoutError:
                        exiting = True
                        await ctx.send(
                            f"{mention} You went idle and decided to exit the shops")
                        break

                    msg_reply = msg_reply.content[len(u.PREF):].split(" ")
                    if len(msg_reply) < 1:
                        continue
                    elif msg_reply[0].lower() == "exit":
                        break
                    elif msg_reply[0].lower() in ["backpack", "back", "bpack", "bp", "b"]:
                        await ctx.send(embed=u.display_backpack(p_inv, ctx.message.author, "Backpack"))
                        continue
                    elif msg_reply[0].lower() in ["refresh", "ref", "re", "r"]:
                        adventure_msg = await ctx.send(embed=embed)
                        continue
                    elif len(msg_reply) < 3:
                        continue
                    elif msg_reply[0].lower() in ["purchase", "pur"]:
                        try:
                            item = u.items_dict(" ".join(msg_reply[1].split("_")[:]))
                            counts = max(int(msg_reply[2]), 1)
                            if not item['name'] in purchasables:
                                await ctx.send("The selected item(s) is not in the offer!")
                                continue
                            elif item["weight"] * counts > 100 - u.get_bp_weight(p_inv):
                                await ctx.send(
                                    "You don't have enough space in your backpack to buy these much!")
                                continue
                            elif item["buy"] * counts > coins:
                                await ctx.send(
                                    "You don't have enough coins to afford the selected item(s)!")
                                continue
                            else:
                                dm.cur.execute(
                                    f"update playersinfo set coins = coins - {item['buy'] * counts} where userid = '{a_id}'")
                                dm.db.commit()
                                if item["name"].lower() in p_inv:
                                    p_inv[item["name"].lower()]["items"] += counts
                                else:
                                    p_inv[item["name"].lower()] = {"items": counts}
                                await ctx.send(
                                    f"You just bought **[{item['rarity']}/{item['weight']}] {item['name']} x{counts}** for {item['buy'] * counts} {u.ICON['coin']}!")
                                continue
                        except:
                            continue

            elif position[1] == "chest" and not afk and not leave:
                exiting = False
                await adventure_msg.edit(content=f"`{u.PREF}backpack` to check your backpack \n`" +
                                                 u.PREF + "chest` to check your chest \n`" +
                                                 u.PREF + "close` to close your chest and exit \n`" +
                                                 u.PREF + "withdraw/deposit (item_name) (amount)` to take or put items from your backpack and chest",
                                         embed=u.display_backpack(p_stor, ctx.message.author, "Chest", level=p_datas[3]))
                if H_TOWN[p_position]["choices"][list(H_TOWN[p_position]["choices"])[decision - 1]][0] == "chest":
                    while not exiting:
                        try:
                            msg_reply = await self.bot.wait_for("message", timeout=60.0,
                                                                check=checks.valid_reply([''], [ctx.message.author], [ctx.message.channel]))
                        except asyncio.TimeoutError:
                            exiting = True
                            await ctx.send(
                                f"{mention} You went idle and decided to close your treasure chest")
                        else:
                            if msg_reply.content[len(u.PREF):len(u.PREF) + 4].lower() == "exit" \
                                    or msg_reply.content[len(u.PREF):len(u.PREF) + 5].lower() == "close":
                                exiting = True
                                await ctx.send(
                                    f"{mention}, you closed your treasure chest")
                            else:
                                inputs = msg_reply.content[len(u.PREF):].lower().split(" ")
                                item = u.items_dict("Glitches")
                                amount = -1
                                try:
                                    amount = math.floor(int(inputs[2]))
                                    item = u.items_dict(" ".join(inputs[1].split("_")[:]))
                                except:
                                    pass
                                total_weight = item['weight'] * amount

                                if inputs[0] in ['r', 'ref', 'refresh']:
                                    adventure_msg = await ctx.send(content=f"`{u.PREF}backpack` to check your backpack \n" +
                                                                           f"`{u.PREF}chest` to check your chest \n" +
                                                                           f"`{u.PREF}close` to close your chest and exit \n" +
                                                                           f"`{u.PREF}withdraw/deposit (item_name) (amount) to take or put items from your backpack and chest",
                                                                   embed=u.display_backpack(p_stor, ctx.message.author, "Chest", level=p_datas[3]))

                                elif inputs[0] in ["backpack", "bp", "b"]:
                                    embed = u.display_backpack(p_inv, ctx.message.author, "Backpack")
                                    embed.add_field(name="Stats:", value=f"Health - {p_hp}/{p_max_hp} \n"
                                                                         f"Stamina - {p_sta} \n"
                                                                         f"Traveled {p_distance} meters", inline=False)
                                    # if perks:
                                    #     embed.add_field(name="Perks:",
                                    #                     value="".join([f"**{all_perks[i]['name']}** x{perks[i]}\n{u.ICON['alpha']}*{all_perks[i.lower()]['description']}*\n"
                                    #                                    for i in perks][:]))
                                    await ctx.send(embed=embed)

                                elif inputs[0] in ["chest", "ch", "c"]:
                                    await ctx.send(embed=u.display_backpack(p_stor, ctx.message.author, "Chest"))

                                elif len(inputs) < 3 or amount < 1:
                                    await ctx.send(
                                        f"{mention} You can only do `" + u.PREF + "backpack`, `" + u.PREF + "chest`, `" + u.PREF + "close`, or `" + u.PREF + "withdraw/deposit (item_name) (amount)`!")

                                elif inputs[0] in ["withdraw", "deposit", "with", "wd", "w", "dep", "de"]:
                                    location = p_inv if inputs[0] in ["deposit", "dep", "de"] else p_stor
                                    target = "Backpack" if inputs[0] in ['deposit', 'dep', 'de'] else 'Chest'
                                    if item["name"].lower() in location:
                                        if location[item["name"].lower()]["items"] < amount:
                                            await ctx.send(
                                                f"{mention} You don't have {amount} **[{item['rarity']}/{item['weight']}] {item['name']}** in your {target}!")

                                        elif (location == p_inv and u.get_bp_weight(
                                                p_stor) + total_weight > u.chest_storage(p_datas[3])) \
                                                or (location == p_stor and u.get_bp_weight(
                                            p_inv) + total_weight > 100):
                                            await ctx.send(
                                                f"{mention} Your {'Backpack' if location != p_inv else 'Chest'} don't have enough space for {amount} **[{item['rarity']}/{item['weight']}] {item['name']}**!")
                                        else:
                                            location[item['name'].lower()]['items'] -= amount
                                            if location == p_inv:
                                                if not item['name'].lower() in p_stor:
                                                    p_stor[item['name'].lower()] = {"items": amount}
                                                else:
                                                    p_stor[item['name'].lower()]['items'] += amount
                                                p_inv = u.clear_bp(p_inv)
                                                await ctx.send(
                                                    f"{mention} You put {amount} **[{item['rarity']}/{item['weight']}] {item['name']}** into your Chest from your backpack!")
                                            else:
                                                if not item['name'].lower() in p_inv:
                                                    p_inv[item['name'].lower()] = {"items": amount}
                                                else:
                                                    p_inv[item['name'].lower()]['items'] += amount
                                                p_stor = u.clear_bp(p_stor)
                                                await ctx.send(
                                                    f"{mention} You put {amount} **[{item['rarity']}/{item['weight']}] {item['name']}** into your backpack from your chest!")
                                    else:
                                        await ctx.send(
                                            f"{mention} **[{item['rarity']}/{item['weight']}] {item['name']}** doesn't exist in your {target}!")
                                else:
                                    await ctx.send(
                                        f"{mention} You can only do `" + u.PREF + "backpack`, `" + u.PREF + "chest`, `" + u.PREF + "close`, or `" + u.PREF + "withdraw/deposit (item_name) (amount)`!")

            elif position[1] == "mini game" and not afk and not leave:
                exit_game = False
                earned_loots = [0, 0, 0]
                random_number = random.randint(1, 1000)

                def reset(earned_loots):
                    sql = "update playersinfo set coins = coins + %s, gems = gems + %s, exps = exps + %s where userid = %s"
                    value = (earned_loots[0], earned_loots[1], earned_loots[2], str(a_id))
                    dm.cur.execute(sql, value)
                    p_datas[4] += earned_loots[2]
                    p_datas[5] += earned_loots[0]
                    p_datas[6] += earned_loots[1]

                await adventure_msg.edit(embed=setup_minigame(H_TOWN[p_position]["choices"][list(H_TOWN[p_position]["choices"])[decision - 1]][0])[0],
                                         file=setup_minigame(H_TOWN[p_position]["choices"][list(H_TOWN[p_position]["choices"])[decision - 1]][0])[1])
                if position[0] == "coin flip":
                    while not exit_game:
                        try:
                            msg_reply = await self.bot.wait_for("message", timeout=60.0,
                                                                check=checks.valid_reply(['flip', 'f', 'exit'],
                                                                                  [ctx.message.author], [ctx.message.channel]))
                        except asyncio.TimeoutError:
                            exit_game = True
                            await ctx.send(f"{mention} ```You accidentally fell asleep and got left ouf of the game.```")
                        else:
                            if msg_reply.content[len(u.PREF):len(u.PREF) + 4].lower() == "exit":
                                exit_game = True
                                await ctx.send(f"{mention}, you quit this mini game")
                            elif not (msg_reply.content[len(u.PREF + "flip "):].lower() in ["head", "tail", "edge", "h", "t", "e"] or
                                      msg_reply.content[len(u.PREF + "f "):].lower() in ["head", "tail", "edge", "h", "t", "e"]):
                                await ctx.send(f"{mention} ```You can only input {u.PREF}exit or {u.PREF}flip (head/tail/edge)```")
                            else:
                                print(p_datas[5])
                                if p_datas[5] < 100:
                                    await ctx.send(f"{mention} ```You need least 100 golden coins to place a bet!```")
                                else:
                                    bet = msg_reply.content[len(u.PREF + choice[1] + " "):].lower()
                                    if msg_reply.content.lower().startswith(u.PREF + "flip "):
                                        choice = [None, "flip"]
                                    elif msg_reply.content.lower().startswith(u.PREF + "f "):
                                        choice = [None, "f"]
                                    if bet in ['head', 'tail', 'edge']:
                                        choice = [msg_reply.content[len(u.PREF + choice[1] + " "):].lower(),
                                                  choice[1]]
                                    elif bet in list('hte'):
                                        translator = {"h": "head", "t": "tail", "e": "edge"}
                                        choice = [translator[msg_reply.content[len(u.PREF + choice[1] + " "):].lower()],
                                                  choice[1]]
                                    result = random.choice(["head", "tail"])
                                    if random_number == 1:
                                        result = "edge"
                                    if result != choice[0]:
                                        earned_loots[0] -= 100
                                        earned_loots[2] += 2
                                        await ctx.send(f"{mention} \n```You bet on {choice[0]} \n"
                                                       f"The coin landed on {result} \n"
                                                       f"You lost {abs(earned_loots[0])} golden coins! \n"
                                                       f"You still gained {earned_loots[2]} exp though... \n"
                                                       f"Better luck next time!``````>flip (head/tail/edge) -try again \n"
                                                       f">exit -quit the mini game```")
                                    else:
                                        if result != "edge":
                                            earned_loots[0] += 100
                                            earned_loots[2] += 3
                                            await ctx.send(f"{mention} \n```You bet on {choice[0]} \n"
                                                           f"The coins landed on {result} \n"
                                                           f"You won {earned_loots[0]} golden coins and {earned_loots[2]} experience points!```"
                                                           "```>flip (head/tail/edge) -try again \n"
                                                           ">exit -quit the mini game```")
                                        else:
                                            earned_loots[0] += 50000
                                            earned_loots[2] += 100
                                            await ctx.send(f"{mention} \n```You bet on {choice[0]} \n"
                                                           f"The coins landed on {result} \n"
                                                           f"You won {earned_loots[0]} GOLDEN COINS and {earned_loots[2]} experience points!"
                                                           f"``````>flip (head/tail/edge) -try again \n"
                                                           f">exit -quit the mini game```")
                                    reset(earned_loots)
                                    earned_loots = [0, 0, 0]
                                    random_number = random.randint(1, 1000)

                if position[0] == "fishing":
                    while not exit_game:
                        try:
                            msg_reply = await self.bot.wait_for("message", timeout=60.0,
                                                                check=checks.valid_reply(['exit', 'fish', 'f'],
                                                                                  [ctx.message.author], [ctx.message.channel]))
                        except asyncio.TimeoutError:
                            exit_game = True
                            await ctx.send(f"{mention} ```You went idle and decided to quit this mini game```")
                        else:
                            if msg_reply.content[len(u.PREF):len(u.PREF) + 4].lower() == "exit":
                                exit_game = True
                                await ctx.send(f"{mention}, you quit this mini game")
                            elif p_datas[5] < 50:
                                await ctx.send(f"{mention} ```You need least 50 golden coins to buy bait!```")
                            else:
                                fish_dict = {
                                    'c': ['Carp', 'Tuna', 'Cod', 'Herring', 'Salmon', 'Trout', 'Bass', 'Minnow'],
                                    'r': ['Lobster', 'Catfish', 'Pufferfish', 'Jellyfish', 'Stingray'],
                                    'e': ['Shark', 'Narwhal', 'Octopus', 'Dolphin'],
                                    'l': ['Kraken', 'Leviathan']
                                }
                                award_multiplier = 1
                                if random_number <= 800:
                                    waits = 6 + random_number % 5
                                    rarity = 'common'
                                elif random_number <= 960:
                                    award_multiplier = 1.5
                                    waits = 12 + random_number % 5
                                    rarity = 'rare'
                                elif random_number <= 992:
                                    award_multiplier = 2.5
                                    waits = 18 + random_number % 5
                                    rarity = 'epic'
                                else:
                                    award_multiplier = 4.5
                                    waits = 24 + random_number % 5
                                    rarity = 'LEGENDARY'
                                msg2 = await ctx.send(f"{mention} ```You saw a {rarity} fish! Try to reply {u.PREF}bait in exactly {waits} seconds!```")

                                try:
                                    msg_reply2 = await self.bot.wait_for("message", timeout=30.0,
                                                                         check=checks.valid_reply(['bait', 'b'], [ctx.message.author], [ctx.message.channel]))
                                except asyncio.TimeoutError:
                                    await ctx.send(f"{mention} ```the fish got away!```")
                                else:
                                    earned_loots[0] -= 50
                                    success_rate = 0
                                    reply_ms = waits - (msg_reply2.created_at - msg2.created_at).total_seconds() * 1000
                                    reply_time = round(abs(reply_ms)) / 1000
                                    if 0.750 <= reply_time <= 1.000:
                                        success_rate = 10
                                    elif 0.500 <= reply_time < 0.750:
                                        success_rate = 20
                                    elif 0.250 <= reply_time < 0.500:
                                        success_rate = 40
                                    elif 0.125 <= reply_time < 0.250:
                                        success_rate = 60
                                    elif 0.050 <= reply_time < 0.125:
                                        success_rate = 80
                                    elif reply_time < 0.050:
                                        success_rate = 100

                                    if random.randint(1, 100) <= success_rate:
                                        if round(reply_ms) == 0:  # BRUH HOW DID THEY DO IT RIGHT ON TIME
                                            earned_loots[0] += 100 * award_multiplier * 4
                                            earned_loots[2] += 50
                                            dm.log_quest(8, 1, str(a_id))
                                            to_send = f"{mention} ```You replied in EXACTLY {reply_ms / 1000} SECONDS!!! \n " \
                                                      f"0.000 SECONDS OFF FROM {waits} SECONDS!!! \n"
                                        else:
                                            earned_loots[0] += 100 * award_multiplier
                                            earned_loots[2] += 5
                                            dm.log_quest(8, 1, str(a_id))
                                            to_send = f"{mention} ```You replied in {reply_ms / 1000} seconds \n" \
                                                      f"{reply_time} seconds off from {waits} seconds! \n"

                                        to_send += f"You caught a {random.choice(fish_dict[{1: 'c', 1.5: 'r', 2.5: 'e', 4.5: 'l'}[award_multiplier]])}, " \
                                                   f"gaining {int(earned_loots[0])} golden coins and {earned_loots[2]} experience points in total! \n" \
                                                   f"``````{u.PREF}fish -try again \n{u.PREF}exit -quit the mini game```"
                                        await ctx.send(to_send)
                                    else:
                                        earned_loots[2] += 2
                                        await ctx.send(
                                            f"{mention} ```You replied in {reply_ms / 1000} seconds \n{reply_time} seconds off from {waits} seconds! \n" +
                                            f"The fish fled away and you wasted {abs(earned_loots[0])} golden coins on the bait \n"
                                            f"You only gained {earned_loots[2]} experience points \n"
                                            f"Better luck next time! \n``````{u.PREF}fish -try again \n{u.PREF}exit -quit the mini game```"
                                        )
                                    reset(earned_loots)
                                    earned_loots = [0, 0, 0]
                                    random_number = random.randint(1, 1000)
                            """
                            else:
                                await ctx.send(f"{mention} ```All the fishies in this river went extinct!```")
                            """

                if position[0] == "blackjack":
                    while not exit_game:
                        try:
                            msg_reply = await self.bot.wait_for("message", timeout=60.0,
                                                                check=checks.valid_reply(['exit', 'start', 's'],
                                                                                  [ctx.message.author], [ctx.message.channel]))
                        except asyncio.TimeoutError:
                            exit_game = True
                            await ctx.send(f"{mention} ```You dozed off and got kicked out of the blackjack table```")
                        else:
                            deck = deepcopy(u.deck)
                            aces = deepcopy(u.aces)
                            if msg_reply.content.lower().startswith(f"{u.PREF}exit"):
                                exit_game = True
                                await ctx.send(f"{mention}, you quit this mini game")
                            elif p_datas[5] < 100:
                                await ctx.send(f"{mention} ```You need least 100 golden coins to play!```")
                            else:
                                values = [0, 0]
                                cards = [[], []]
                                included_aces = [[], []]
                                end = False

                                def add_card(card, target):
                                    if target == "self":
                                        values[0] += deck[card]
                                        cards[0].append(card)
                                    else:
                                        values[1] += deck[card]
                                        cards[1].append(card)
                                    del deck[card]

                                add_card(random.choice(list(deck)), "self")
                                add_card(random.choice(list(deck)), "self")
                                add_card(random.choice(list(deck)), "opponent")
                                while not end and values[0] < 21:
                                    await ctx.send(f"{mention} \nYour total: {values[0]} \n{' '.join(cards[0])}"
                                                   f" \n------------------------------ \n"
                                                   f"Dealer's total: {values[1]} + ? \n"
                                                   f"{' '.join(cards[1])} [? ? ?] ```\n{u.PREF}hit -draw a card \n"
                                                   f"{u.PREF}stand -end your turn```")
                                    try:
                                        msg_reply = await self.bot.wait_for("message", timeout=30.0,
                                                                            check=checks.valid_reply(['hit', 'h', 'stand', 's'],
                                                                                              [ctx.message.author], [ctx.message.channel]))
                                    except asyncio.TimeoutError:
                                        values = [1000, 1000]
                                        await ctx.send(f"{mention}, you lost due to idle")
                                    else:
                                        action = msg_reply.content[len(u.PREF):].lower()
                                        if action in ['s', 'stand']:
                                            end = True
                                            add_card(random.choice(list(deck)), "opponent")
                                            while values[1] < 17:
                                                add_card(random.choice(list(deck)), "opponent")
                                                while values[1] > 21 and any(a in cards[1] and a not in included_aces[1] for a in aces):
                                                    for c in cards[1]:
                                                        if c in aces and c not in included_aces[1]:
                                                            values[1] -= 10
                                                            included_aces[1].append(c)
                                                            break

                                        elif action in ['h', 'hit']:
                                            add_card(random.choice(list(deck)), "self")
                                            while values[0] > 21 and any(a in cards[0] and a not in included_aces[0] for a in aces):
                                                for translator in cards[0]:
                                                    if c in aces and c not in included_aces[0]:
                                                        values[0] -= 10
                                                        included_aces[0].append(translator)
                                                        break

                                if len(cards[1]) == 1 and not values == [1000, 1000]:
                                    add_card(random.choice(list(deck)), "opponent")
                                if values[0] == values[1] and not values == [1000, 1000]:
                                    earned_loots[2] += 3
                                    await ctx.send(
                                        f"{mention}, **You Tied!** \n__At least you gained {earned_loots[2]} experience points__ \n"
                                        f"Your total: {values[0]} \n" + " ".join(cards[0]) + f" \n-------------------------------- \n"
                                                                                             f"Dealer's total: {values[1]} \n{' '.join(cards[1])}" +
                                        f" ```{u.PREF}start -try again \n{u.PREF}exit -quit the mini game```")
                                elif (values[0] > 21 and values[0] > values[1]) or (values[0] < values[1] < 22):
                                    earned_loots[0] -= 100
                                    earned_loots[2] += 2
                                    await ctx.send(
                                        f"{mention}, **Bust!** \n__You lost {abs(earned_loots[0])} golden coins and only received {earned_loots[2]} experience points! \n"
                                        f"Better luck next time!__ \nYour total: {values[0]} \n" + " ".join(cards[0]) +
                                        f" \n-------------------------------- \nDealer's total: {values[1]} \n{' '.join(cards[1])}" +
                                        f" ```{u.PREF}start -try again \n{u.PREF}exit -quit the mini game```")
                                elif (22 > values[0] > values[1]) or (values[1] > 21 and values[0] < values[1]):
                                    earned_loots[0] += 100
                                    earned_loots[2] += 5
                                    await ctx.send(
                                        f"{mention}, **You Won!** \n__You gained {earned_loots[0]} golden coins "
                                        f"and {earned_loots[2]} experience points!__ \nYour total: {values[0]}\n" +
                                        " ".join(cards[0]) + " \n-------------------------------- \nDealer's total: " +
                                        f"{values[1]}\n{''.join(cards[1])} ```{u.PREF}start -try again \n{u.PREF}exit -quit the mini game```")
                                reset(earned_loots)
                                earned_loots = [0, 0, 0]
                            """
                            else:  # jeff this code LITERALLY CANNOT BE REACHED
                                await ctx.send(f"{mention} ```The bar's BlackJack service went bankrupt!```")
                            """

            elif position[1] == "adventure" and not afk and not leave:
                dm.cur.execute("select deck_slot from playersinfo where userid = " + str(a_id))
                deck_slot = dm.cur.fetchall()[0][0]
                db_deck = f"deck{deck_slot}"
                dm.cur.execute(
                    f"select {db_deck} from playersachivements where userid = " + str(a_id))
                mydeck = dm.cur.fetchall()[0][0].split(",")
                dm.cur.execute(
                    f"select card_name, card_level from cardsinfo where owned_user = '{a_id}' and id in ({str(mydeck)[1:-1]})")
                mydeck = dm.cur.fetchall()

                if len(mydeck) == 12:
                    if position[0] == "boss raid":
                        dm.cur.execute(f"select level, tickets from playersinfo where userid = {a_id}")
                        result = dm.cur.fetchall()[0]

                        if result[0] < 9:
                            await ctx.send(f"{mention}, you need to be at least level 9 to start a boss raid!")
                        elif result[1] == 0:
                            await ctx.send(f"{mention}, you need a Raid Ticket to start a boss raid!")
                        else:
                            diff_msg = await ctx.send("Select Mob cards Level: \n"
                                                      "**[1]** Easy - Lv 1 \n"
                                                      "**[2]** Moderate - Lv 5 \n"
                                                      "**[3]** Difficult - Lv 10 \n"
                                                      "**[4]** Insane - Lv 15 \n"
                                                      "**[5]** Go Back")
                            for r in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]:
                                await diff_msg.add_reaction(r)

                            try:
                                reaction, user = await self.bot.wait_for("reaction_add", timeout=120.0,
                                                                         check=checks.valid_reaction(["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"],
                                                                                              [ctx.message.author], [diff_msg]))
                            except asyncio.TimeoutError:
                                await ctx.send(f"{ctx.message.author} the host, went afk... :man_facepalming: ")
                            else:
                                if reaction.emoji != "5️⃣":
                                    raid_levels = {"1️⃣": 1, "2️⃣": 5, "3️⃣": 10, "4️⃣": 15}[reaction.emoji]

                                    dm.cur.execute("update playersinfo set tickets = tickets - 1 where userid = " + str(a_id))
                                    dm.db.commit()
                                    adventure = True
                    else:
                        adventure = True
                else:
                    await ctx.send(f"{mention}, you need 12 cards in your deck in order to go on an adventure!")

        sql = "update adventuredatas set position = %s, inventory = %s, show_map = %s, storage = %s where userid = %s"
        val = (p_position, str(p_inv), 'true' if show_map else 'false', str(p_stor), str(a_id))
        dm.cur.execute(sql, val)
        dm.db.commit()

        if adventure:
            location = H_TOWN[p_position]["choices"][list(H_TOWN[p_position]["choices"])[decision - 1]][0]
            event = "main"
            section = "start"
            distance = 0
            travel_speed = 1
            perk_turn = 5
            perks = {}
            boss_spawn = False
            pre_message = []

        ##############################################################################################################################################
        all_perks = json.load(open('resources/text/perks.json'))
        # "hysterical maniac": {
        #     "name": "Hysterical Maniac",
        #     "description": "Use a card from your hand for 0 energy to a random enemy automatically every turn",
        #     "multiplier": [0, 0, 0, 0, 0]
        # },
        # "energized charge": {
        #     "name": "Energized Charge",
        #     "description": "Receive 2 max energy limit increase",
        #     "multiplier": [0, 0, 0, 0, 0]
        # },
        # "incarnation of god": {
        #     "name": "Incarnation of God",
        #     "description": "Receive 1000% damage, defense, accuracy, critical and effect chance increase",
        #     "multiplier": [10, 10, 1000, 1000, 1000]
        # }
        perk_list = list(all_perks.keys())

        def option_decider(path, traveled_distance, boss, msg=None, option=None):
            while option is None:
                if not boss:
                    for x, n in enumerate(path):
                        for a, b, c in n["spawn rate"]:
                            if a <= traveled_distance <= b and c >= random.randint(1, 10000):
                                option = x
                                break
                        if option is not None:
                            break
                else:
                    option = math.floor(traveled_distance / 1000) % len(path)
            if msg is None:
                embed = discord.Embed(title=None, description="```" + path[option]["description"] + "```", color=discord.Color.gold())
            else:
                embed = discord.Embed(title=None, description="```" + "\n".join(msg[:]) + "\n\n" + path[option]["description"] + "```",
                                      color=discord.Color.gold())
            if "choices" in path[option]:
                embed.add_field(name="Choices", value=choices_list(path[option]["choices"]))
            embed.set_thumbnail(url=ctx.message.author.avatar.url)
            embed.set_footer(text=f"{u.PREF}exit | {u.PREF}backpack | {u.PREF}refresh")
            return [embed, option]

        def perk_decider():
            random.shuffle(perk_list)
            embed = discord.Embed(title=None, description="```The tireless long journey has paid off! Choose 1 Perk:```", color=discord.Color.gold())
            embed.add_field(name="Choices", value=choices_list([i.title() for i in perk_list[:3]]))
            embed.set_footer(text=f"{u.PREF}exit | {u.PREF}backpack | {u.PREF}refresh")
            return [embed]

        while not leave and not afk and adventure and p_hp > 0 and p_sta > 0:
            boss_spawn = False
            if section == "start":
                perk_turn -= 1
                p_sta -= random.randint(3, 6)
                t_dis = round(travel_speed * random.randint(100, 200))
                if math.floor(p_distance / 1000) < math.floor((p_distance + t_dis) / 1000):
                    boss_spawn = True
                    perk_turn = 0
                p_distance += t_dis
            dm.log_quest(3, t_dis, a_id)

            if perk_turn != 0:
                options = option_decider(ADVENTURES[location][event][section], p_distance, boss_spawn, pre_message)
                pre_message = []
                option = options[1]
                choices = ADVENTURES[location][event][section][option]
                await adventure_msg.edit(embed=options[0])
            else:
                options = perk_decider()
                pre_message = []
                choices = {"choices": perk_list[:3]}
                await adventure_msg.edit(embed=options[0])

            choice = 0
            while not leave and not afk and p_hp > 0 and p_sta > 0 and "choices" in choices:
                try:
                    msg_reply = await self.bot.wait_for("message", timeout=60.0,
                                                        check=checks.valid_reply([''], [ctx.message.author], [ctx.message.channel]))
                except asyncio.TimeoutError:
                    afk = True
                    await ctx.send(f"{mention}, you went idling and the adventure was ended.")
                    break

                try:
                    choice = abs(math.floor(int(msg_reply.content[len(u.PREF):])) + 1 - 1)
                except:
                    msg_reply = msg_reply.content[len(u.PREF):].lower()
                    if msg_reply == "exit":
                        leave = True
                        await ctx.send(f"{mention}, you quit this adventure")
                        break
                    elif msg_reply in ["bp", "backpack"]:
                        embed = u.display_backpack(p_inv, ctx.message.author, "Backpack")
                        embed.add_field(name="Stats:", value=f"Health - {p_hp}/{p_max_hp} \n" + \
                                                             f"Stamina - {p_sta} \n" + \
                                                             f"Traveled {p_distance} meters", inline=False)
                        if perks != {}:
                            embed.add_field(name="Perks:", value="".join([f"**{all_perks[i]['name']}** x{perks[i]}\n{u.ICON['alpha']}*{all_perks[i.lower()]['description']}*\n" for i in perks][:]))
                        await ctx.send(embed=embed)
                    elif msg_reply in ['r', 'ref', 'refresh']:
                        adventure_msg = await ctx.send(embed=options[0], file=None)

                    choice = 0

                if not 1 <= choice <= len(choices["choices"]):
                    if not (msg_reply in ['exit', 'bp', 'backpack', 'r', 'refresh', 'ref']):
                        await ctx.send(f"You can only enter numbers `1-{len(choices['choices'])}`!")
                elif perk_turn != 0:
                    feed = u.fulfill_requirement(list(choices["choices"].values())[choice - 1], p_inv)

                    if feed[0]:
                        if not feed[2] is None:
                            pre_message.append(feed[2])
                        p_inv = feed[1]
                        await msg_reply.delete()
                        break
                    else:
                        if not feed[2] is None:
                            pre_message.append(feed[2])
                        options = option_decider(ADVENTURES[location][event][section], p_distance, boss_spawn, pre_message, option)
                        pre_message = []
                        await adventure_msg.edit(embed=options[0])
                else:
                    if perk_list[choice - 1] in perks:
                        perks[perk_list[choice - 1]] += 1
                    else:
                        perks[perk_list[choice - 1]] = 1

                    if perk_list[choice - 1] == 'vigorous endurance':
                        p_max_hp = round(p_max_hp * 1.2)
                    elif perk_list[choice - 1] == 'hot spring':
                        p_sta += 40
                    elif perk_list[choice - 1] == "feathered shoe":
                        travel_speed += 0.4
                    elif perk_list[choice - 1] == 'chunk of gold':
                        dm.log_quest(5, 250, a_id)

                        dm.cur.execute(f"update playersinfo set coins = coins + 250 where userid = '{a_id}'")
                        dm.db.commit()
                    elif perk_list[choice - 1] == "book of knowledge":
                        dm.cur.execute(f"update playersinfo set exps = exps + 150 where userid = '{a_id}'")
                        dm.db.commit()
                    elif perk_list[choice - 1] == "hidden gem":
                        dm.cur.execute(f"update playersinfo set gems = gems + 1 where userid = '{a_id}'")
                        dm.db.commit()

                    section = "start"
                    await msg_reply.delete()
                    break

            if section == "end":
                pass
            elif perk_turn == 0:
                perk_turn = 5
            elif "choices" not in choices:
                event = choices['to'][1]
                section = choices['to'][0]
                trap_time = random.randint(choices["time"][0], choices["time"][1])
                trap_dmg = round(random.randint(choices["damage"][0], choices['damage'][1]) / 100 * round((100 * u.SCALE[1] ** math.floor(p_datas[3] / 2)) * u.SCALE[0]))
                if choices["trap"] == "reaction":
                    await ctx.send(
                        'Reply `a.react` as fast as you can when you see the message "Now!"!')
                    await asyncio.sleep(trap_time)
                    trap_msg = await ctx.send('Now!')
                    try:
                        msg_reply = await self.bot.wait_for("message", timeout=20.0,
                                                            check=checks.valid_reply(['react'], [ctx.message.author], [ctx.message.channel]))
                    except asyncio.TimeoutError:
                        pre_message.append(f"You went idle and received {trap_dmg * 2} damage!")
                        p_hp -= trap_dmg * 2
                    else:
                        offset = round((msg_reply.created_at - trap_msg.created_at).total_seconds() * 1000) / 1000
                        pre_message.append(f"You reacted in {offset} seconds")
                        if offset <= 0.7:
                            pre_message.append(f"You successfully dodged the trap!")
                        else:
                            pre_message.append(f"You received {trap_dmg} damage!")
                            p_hp -= trap_dmg
                elif choices['trap'] == "memorize":
                    sequence_em = [f':regional_indicator_{s}:' for s in string.ascii_lowercase]
                    sequence_le = list(string.ascii_lowercase)
                    rands = [random.randint(0, 25) for i in
                             range(random.randint(choices['length'][0], choices['length'][1]))]
                    seq_msg = await ctx.send(f'Memorize the sequence {"".join([sequence_em[i] for i in rands])}!')
                    await asyncio.sleep(trap_time)
                    await seq_msg.edit(content=f"Retype the sequence begin with `{u.PREF}`! \nEx: `{u.PREF}abcdefg`")
                    try:
                        msg_reply = await self.bot.wait_for("message", timeout=20.0,
                                                            check=checks.valid_reply([''], [ctx.message.author], [ctx.message.channel]))
                    except asyncio.TimeoutError:
                        pre_message.append(f"You went idle and received {trap_dmg * 2} damage!")
                        p_hp -= trap_dmg * 2
                    else:
                        seq = msg_reply.content[len(u.PREF):].lower()
                        correct_seq = "".join([sequence_le[i] for i in rands])
                        pre_message.append(f'The correct sequence is "{correct_seq}" \nYour sequence is "{seq}"')
                        if seq == correct_seq:
                            pre_message.append("You successfully avoided the trap!")
                        else:
                            pre_message.append(f"You received {trap_dmg} damage!")
                            p_hp -= trap_dmg

            elif not leave and not afk and p_hp > 0 and p_sta > 0:
                gained_coins = 0
                gained_exps = 0
                gained_gems = 0
                index = list(choices["choices"].values())[choice - 1]
                event = index[1]
                section = index[0]

                if index[2] == "item":
                    item_info = u.items_dict(list(choices['items'].keys())[0])
                    item_index = choices["items"][list(choices['items'].keys())[0]]["items"]
                    item_amount = random.randint(item_index[0], item_index[1])
                    items_to_take = 1
                    if u.get_bp_weight(p_inv) + u.items_dict(item_info["name"])["weight"] * item_amount <= 100:
                        items_to_take = item_amount
                        pre_message.append(f"You successfully obtained {item_info['name'].title()} x{item_amount}!")
                    elif u.get_bp_weight(p_inv) + u.items_dict(item_info["name"])["weight"] <= 100:
                        items_to_take = math.floor(
                            (100 - u.get_bp_weight(p_inv)) / u.items_dict(item_info["name"])["weight"])
                        pre_message.append(
                            f"You successfully obtained {item_info['name'].title()} x{math.floor((100 - u.get_bp_weight(p_inv)) / u.items_dict(item_info['name'])['weight'])}!")
                    else:
                        items_to_take = 0
                        pre_message.append(f"Your backpack is full, failed to obtain {item_info['name'].title()}!")
                    if not item_info['name'].lower() in p_inv and items_to_take != 0:
                        dm.log_quest(2, u.items_dict(item_info["name"])["weight"] * items_to_take,
                                            a_id)
                        p_inv[item_info['name'].lower()] = {"items": items_to_take}
                    elif items_to_take != 0:
                        dm.log_quest(2, u.items_dict(item_info['name'])["weight"] * items_to_take,
                                            a_id)
                        p_inv[item_info['name'].lower()]["items"] += items_to_take

                if index[2] == "fight":
                    def mob_generator(requirements):
                        mob = []
                        for x in requirements:
                            if requirements[x][0] > 0:
                                mob = mob + [x] * requirements[x][0]
                        for x in range(2, 4):
                            for y in requirements:
                                if len(mob) == 3:
                                    break
                                if requirements[y][1] >= x:
                                    if random.randint(1, 10000) <= requirements[y][2]:
                                        mob = mob + [y]
                        return mob

                    enemynames = mob_generator(choices["encounters"])
                    levels = math.floor((p_distance - 500) / 200) if p_distance > 500 else 1
                    if position[0] == "boss raid":
                        levels = raid_levels
                    ad_decks = [p_hand] + [random.sample(
                        [f"{levels + random.randint(0, 3)}.{x}" for x in u.mobs_dict(levels, i)["deck"]],
                        len(u.mobs_dict(levels, i)['deck'])) for i in enemynames]
                    ad_hps = [[p_hp, 0, p_max_hp, 0, 0]] + \
                             [[u.mobs_dict(levels, i)["health"], 0, u.mobs_dict(levels, i)['health'], 0, 0] for i in enemynames]
                    dd = BattleData({1: [1], 2: [i + 2 for i in range(len(enemynames))]},  # teams
                                    [ctx.message.author] + enemynames,  # names
                                    [a_id] + [123] * len(enemynames),  # ids
                                    ad_decks,  # decks
                                    [p_inv] + [{} for i in range(len(enemynames))],  # backpack
                                    ad_hps,  # hps
                                    [p_sta] + [u.mobs_dict(levels, i)["stamina"] for i in enemynames], #stamina
                                    len(enemynames)+1)
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
                        def use(msg):
                            return msg.content.lower().startswith(u.PREF)

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
                        correct_format = False

                        while not correct_format and dd.afk == 0 and not dd.freeze_skips.info[1] and \
                                dd.hps.info[1][0] > 0 and dd.staminas.info[1] > 0:
                            try:
                                replied_message = await self.bot.wait_for("message", timeout=120.0,
                                                                          check=checks.valid_reply([''], [ctx.message.author], [ctx.message.channel]))
                            except asyncio.TimeoutError:
                                dd.hps.info[1][0] = 0
                                dd.staminas.info[1] = 0
                                dd.descriptions.info[1].append("Went afk!")
                            else:
                                the_message = dd.interpret_message(replied_message.content[len(u.PREF):],
                                                                   str(dd.players.info[1]), 1)
                                if isinstance(the_message, str) and the_message not in ["skip", "flee", "refresh", "backpack"]:
                                    await ctx.send(the_message)

                                elif the_message == "refresh":
                                    stats_msg = await ctx.send(embed=stats_embed)
                                    hands_msg = await ctx.send(embed=hand_embed)

                                elif the_message == "skip":
                                    # dd.stamina[0] += 1
                                    for y in range(dd.hand_sizes.info[1]):
                                        if not dd.decks.info[1][y] in [".".join(x.split(".")[0:2]) for x in
                                                                       dd.used_cards.info[1]]:
                                            if "on_hand" in u.cards_dict(dd.decks.info[1][y].split(".")[0],
                                                                                 dd.decks.info[1][y].split(".")[1]):
                                                dd.execute_card_offense(int(dd.decks.info[1][y].split(".")[0]),
                                                                        dd.decks.info[1][y].split(".")[1], 1, 1,
                                                                        "on_hand")
                                    if not dd.hand_sizes.info[1] == 6:
                                        dd.hand_sizes.info[1] += 1
                                    dd.descriptions.info[1].append(f"{u.ICON['ski']}{u.ICON['kip']}\n")
                                    correct_format = True

                                elif the_message == "flee":
                                    for y in range(dd.hand_sizes.info[1]):
                                        if not dd.decks.info[1][y] in [".".join(x.split(".")[0:2]) for x in
                                                                       dd.used_cards.info[1]]:
                                            if "on_hand" in u.cards_dict(dd.decks.info[1][y].split(".")[0], dd.decks.info[1][y].split(".")[1]):
                                                dd.execute_card_offense(int(dd.decks.info[1][y].split(".")[0]), dd.decks.info[1][y].split(".")[1], 1, 1, "on_hand")
                                    if not dd.hand_sizes.info[1] == 6:
                                        dd.hand_sizes.info[1] += 1
                                    correct_format = True
                                    if random.randint(1, 100) > 40:
                                        dd.descriptions.info[1].append(
                                            f"{u.ICON['fle']}{u.ICON['lee']} {u.ICON['mi']}{u.ICON['ss']}\n")
                                    else:
                                        dd.descriptions.info[1].append(f"{u.ICON['fle']}{u.ICON['lee']}\n")
                                        dd.afk = 8

                                elif the_message == "backpack":
                                    embed = u.display_backpack(dd.backpacks.info[1], dd.players.info[1], "Backpack")
                                    embed.add_field(name="Stats:", value=f"Health - {p_hp}/{p_max_hp} \n" + \
                                                                         f"Stamina - {p_sta} \n" + \
                                                                         f"Traveled {p_distance} meters", inline=False)
                                    if perks != {}:
                                        embed.add_field(name="Perks:", value="".join([f"**{all_perks[i]['name']}** x{perks[i]}\n{u.ICON['alpha']}*{all_perks[i.lower()]['description']}*\n" for i in perks][:]))
                                    await ctx.send(embed=embed)

                                else:
                                    dd.staminas.info[1] -= len(the_message)
                                    dd.move_numbers.info[1] = the_message
                                    correct_format = True
                                    dd.used_cards.info[1] = [dd.decks.info[1][int(str(x)[0]) - 1] + "." + str(x)[1:]
                                                             for x in dd.move_numbers.info[1]]
                                    dd.stored_energies.info[1] -= sum([u.cards_dict(
                                        int(dd.decks.info[1][int(str(x)[0]) - 1].split(".")[0]),
                                        dd.decks.info[1][int(str(x)[0]) - 1].split(".")[1])["cost"] for x in
                                                                       dd.move_numbers.info[1]])
                                    dd.move_numbers.info[1].sort()
                                    z = 0
                                    for y in range(dd.hand_sizes.info[1]):
                                        if not dd.decks.info[1][y] in [".".join(x.split(".")[0:2]) for x in
                                                                       dd.used_cards.info[1]]:
                                            if "on_hand" in u.cards_dict(dd.decks.info[1][y].split(".")[0],
                                                                                 dd.decks.info[1][y].split(".")[1]):
                                                dd.execute_card_offense(int(dd.decks.info[1][y].split(".")[0]),
                                                                        dd.decks.info[1][y].split(".")[1], 1, 1, "on_hand")
                                    for y in range(len(dd.move_numbers.info[1])):
                                        translator = int(str(dd.move_numbers.info[1][y])[0]) - y + z
                                        card = dd.decks.info[1][translator - 1].split(".")
                                        card_info = u.cards_dict(card[0], card[1])
                                        if not card[1] in dd.temporary_cards:
                                            if "rewrite" in card_info:
                                                re_name = u.cards_dict(1, card[1])['rewrite']
                                                dd.descriptions.info[1].append(f"*{card[1]}* rewritten as *{re_name}*")
                                                dd.decks.info[1][translator - 1] = card[0] + "." + card_info["rewrite"]
                                            if "stay" in card_info:
                                                if random.randint(1, 100) <= card_info['stay']:
                                                    z += 1
                                                    dd.descriptions.info[1].append(
                                                        f"*[{u.rarity_cost(card[1])}] {card[1]} lv:{card[0]}* stayed in your hand!")
                                                # dd.new_line(1)
                                                else:
                                                    dd.decks.info[1].insert(len(dd.decks.info[1]),
                                                                            dd.decks.info[1].pop(translator - 1))
                                            else:
                                                dd.decks.info[1].insert(len(dd.decks.info[1]),
                                                                        dd.decks.info[1].pop(translator - 1))
                                        else:
                                            if "stay" in card_info:
                                                if random.randint(1, 100) <= card_info['stay']:
                                                    z += 1
                                                    dd.descriptions.info[1].append(
                                                        f"*[{u.rarity_cost(card[1])}] {card[1]} lv:{card[0]}* stayed in your hand!")
                                                # dd.new_line(1)
                                                else:
                                                    dd.decks.info[1].pop(translator - 1)
                                            else:
                                                dd.decks.info[1].pop(translator - 1)
                                    dd.hand_sizes.info[1] -= len(dd.move_numbers.info[1]) - z - 1
                                await replied_message.delete()

                        for e_index in range(2, len(enemynames) + 2):
                            if dd.afk == 0 and not dd.freeze_skips.info[e_index] and dd.hps.info[e_index][0] > 0 and dd.staminas.info[e_index] > 0:
                                rng_move = random.randint(1, dd.hand_sizes.info[e_index])
                                if dd.stored_energies.info[e_index] >= \
                                        u.cards_dict(int(dd.decks.info[e_index][rng_move - 1].split(".")[0]), dd.decks.info[e_index][rng_move - 1].split(".")[1])["cost"]:
                                    the_message = [rng_move]
                                    for translator in range(3):
                                        rng_move = random.randint(1, dd.hand_sizes.info[e_index])
                                        if dd.stored_energies.info[e_index] >= sum([u.cards_dict(
                                                int(dd.decks.info[e_index][x - 1].split(".")[0]),
                                                dd.decks.info[e_index][x - 1].split(".")[1])["cost"] for x in
                                                                                    the_message]) + \
                                                u.cards_dict(
                                                    int(dd.decks.info[e_index][rng_move - 1].split(".")[0]),
                                                    dd.decks.info[e_index][rng_move - 1].split(".")[1])["cost"]:
                                            the_message.append(rng_move)
                                else:
                                    the_message = "skip"
                                if the_message == "skip":
                                    # dd.stamina[1] += 1
                                    for y in range(dd.hand_sizes.info[e_index]):
                                        if not dd.decks.info[e_index][y] in dd.used_cards.info[e_index]:
                                            if "on_hand" in u.cards_dict(
                                                    dd.decks.info[e_index][y].split(".")[0],
                                                    dd.decks.info[e_index][y].split(".")[
                                                        1]):
                                                dd.execute_card_offense(int(dd.decks.info[e_index][y].split(".")[0]),
                                                                        dd.decks.info[e_index][y].split(".")[1],
                                                                        e_index, e_index, "on_hand")
                                    if not dd.hand_sizes.info[e_index] == 6:
                                        dd.hand_sizes.info[e_index] += 1
                                    dd.descriptions.info[e_index].insert(len(dd.descriptions.info[e_index]),
                                                                         f"{u.ICON['ski']}{u.ICON['kip']}\n")
                                    correct_format = True
                                elif the_message == "flee":
                                    dd.afk = len(dd.players.info) + e_index
                                    break
                                else:
                                    dd.staminas.info[e_index] -= 1
                                    dd.move_numbers.info[e_index] = list(dict.fromkeys(the_message))
                                    correct_format = True
                                    defense_cards = ["shield", "absorb", "heal", "aid", "aim", "relic", "meditate",
                                                     "heavy shield", "reckless assault", "seed", "sprout", "sapling",
                                                     "holy tree", "cache", "blessed clover", "dark resurrection",
                                                     "battle cry", "enrage", "devour", "reform",
                                                     "harden scales", "prideful flight", "rejuvenate", "regenerate"]
                                    dd.used_cards.info[e_index] = [dd.decks.info[e_index][x - 1] + f".{e_index}" if
                                                                   dd.decks.info[e_index][x - 1].lower().split(".")[
                                                                       1] in defense_cards else
                                                                   dd.decks.info[e_index][x - 1] + ".1" for x in
                                                                   dd.move_numbers.info[e_index]]
                                    dd.stored_energies.info[e_index] -= sum([u.cards_dict(int(dd.decks.info[e_index][x - 1].split(".")[0]),
                                                                                                  dd.decks.info[e_index][x - 1].split(".")[1])["cost"] for x in dd.move_numbers.info[e_index]])
                                    dd.move_numbers.info[e_index].sort()
                                    z = 0
                                    for y in range(dd.hand_sizes.info[e_index]):
                                        if not dd.decks.info[e_index][y] in dd.used_cards.info[e_index]:
                                            if "on_hand" in u.cards_dict(
                                                    dd.decks.info[e_index][y].split(".")[0],
                                                    dd.decks.info[e_index][y].split(".")[
                                                        1]):
                                                dd.execute_card_offense(int(dd.decks.info[e_index][y].split(".")[0]),
                                                                        dd.decks.info[e_index][y].split(".")[1],
                                                                        e_index, e_index, "on_hand")
                                    for y in range(len(dd.move_numbers.info[e_index])):
                                        translator = dd.move_numbers.info[e_index][y] - y + z
                                        card = dd.decks.info[e_index][translator - 1].split('.')
                                        card_info = u.cards_dict(card[0], card[1])

                                        if not card[1] in dd.temporary_cards:
                                            if "rewrite" in card_info:
                                                re_name = u.cards_dict(1, card[1])['rewrite']
                                                dd.descriptions.info[e_index].append(
                                                    f"*{card[1]}* rewritten as *{re_name}*")
                                                dd.decks.info[e_index][translator - 1] = card[0] + "." + card_info["rewrite"]
                                            if "stay" in card_info:
                                                if random.randint(1, 100) <= card_info['stay']:
                                                    z += 1
                                                    dd.descriptions.info[e_index].append(
                                                        f"*[{u.rarity_cost(card[1])}] {card[1]} lv:{card[0]}* stayed in your hand!")
                                                # dd.new_line(e_index)
                                                else:
                                                    dd.decks.info[e_index].insert(len(dd.decks.info[e_index]),
                                                                                  dd.decks.info[e_index].pop(translator - 1))
                                            else:
                                                dd.decks.info[e_index].insert(len(dd.decks.info[e_index]),
                                                                              dd.decks.info[e_index].pop(translator - 1))
                                        else:
                                            if "stay" in card_info:
                                                if random.randint(1, 100) <= card_info['stay']:
                                                    z += 1
                                                    dd.descriptions.info[e_index].append(
                                                        f"*[{u.rarity_cost(card[1])}] {card[1]} lv:{card[0]}* stayed in your hand!")
                                                # dd.new_line(e_index)
                                                else:
                                                    dd.decks.info[e_index].pop(translator - 1)
                                            else:
                                                dd.decks.info[e_index].pop(translator - 1)
                                    dd.hand_sizes.info[e_index] -= len(dd.move_numbers.info[e_index]) - z - 1
                            # dd.decke_index.insert(dd.move_numbere_index - 1, dd.decke_index.pop(dd.hand_size[1]-1))
                            elif dd.hps.info[e_index][0] <= 0 or dd.staminas.info[e_index] <= 0:
                                dd.descriptions.info[e_index].append(f"•{u.ICON['dead']}")
                                dd.effects.info[e_index] = {}
                        if dd.afk == 0:
                            cards_length = [len(i) for i in list(dd.used_cards.info.values())]
                            cards_length.sort()

                            if "mechanical heart" in perks:
                                perk_heal = math.ceil(dd.hps.info[1][2] / 100 * perks['mechanical heart'])
                                dd.hps.info[1][0] = min(dd.hps.info[1][0] + perk_heal, dd.hps.info[1][2])
                                dd.descriptions.info[1].append(f"**Mechanical Heart**» {perk_heal} {u.ICON['hp']}")

                            for translator in perks:
                                dd.multipliers.info[1] = [all_perks[translator.lower()]['multiplier'][i] * perks[translator] + dd.multipliers.info[1][i] for i in range(5)]
                            for translator in dd.item_used.info:
                                if dd.item_used.info[translator][0] != "None":
                                    dd.execute_card_defense(-1, dd.item_used.info[translator][0], translator, dd.item_used.info[translator][1])
                                    dd.execute_card_offense(-1, dd.item_used.info[translator][0], translator, dd.item_used.info[translator][1])
                                    dd.execute_card_special(-1, dd.item_used.info[translator][0], translator, dd.item_used.info[translator][1])
                            for translator in range(cards_length[-1]):
                                for y in range(1, len(dd.used_cards.info) + 1):
                                    if len(dd.used_cards.info[y]) > translator:
                                        if y == 1 and "soul of fire" in perks:
                                            dd.apply_effects('burn', {'burn': [perks['soul of fire'], 'target']}, 1, int(dd.used_cards.info[y][translator].split(".")[2]))
                                        if y == 1 and "devil's core" in perks:
                                            dd.apply_effects('curse', {'curse': [perks["devil's core"], 'target']}, 1, int(dd.used_cards.info[y][translator].split(".")[2]))
                                        if y == 1 and 'essence of venom' in perks:
                                            dd.apply_effects('poison', {'poison': [perks['essence of venom'], 'target']}, 1, int(dd.used_cards.info[y][translator].split(".")[2]))
                                        if y == 1 and 'unblemished prime crystal' in perks:
                                            dd.apply_effects('chill', {'chill': [perks['unblemished prime crystal'], 'target']}, 1, int(dd.used_cards.info[y][translator].split(".")[2]))
                                        dd.execute_card_defense(int(dd.used_cards.info[y][translator].split(".")[0]),
                                                                dd.used_cards.info[y][translator].split(".")[1], y,
                                                                int(dd.used_cards.info[y][translator].split(".")[2]))
                                for y in range(1, len(dd.used_cards.info) + 1):
                                    if len(dd.used_cards.info[y]) > translator:
                                        dd.execute_card_offense(int(dd.used_cards.info[y][translator].split(".")[0]),
                                                                dd.used_cards.info[y][translator].split(".")[1], y,
                                                                int(dd.used_cards.info[y][translator].split(".")[2]))
                                for y in range(1, len(dd.used_cards.info) + 1):
                                    if len(dd.used_cards.info[y]) > translator:
                                        dd.execute_card_special(int(dd.used_cards.info[y][translator].split(".")[0]),
                                                                dd.used_cards.info[y][translator].split(".")[1], y,
                                                                int(dd.used_cards.info[y][translator].split(".")[2]))

                            for i in range(1, len(dd.effects.info) + 1):
                                dd.execute_effects(i)
                            for i in range(1, len(dd.used_cards.info) + 1):
                                dd.used_cards.info[i] = []
                            for i in range(1, len(dd.players.info) + 1):
                                energy_lags = u.mobs_dict(1, dd.players.info[i])["energy_lag"] if i > 1 else 4
                                if dd.stored_energies.info[i] + math.ceil(dd.turns / energy_lags) > 12:
                                    dd.stored_energies.info[i] = 12
                                elif dd.hps.info[i][0] > 0 and dd.staminas.info[i] > 0:
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

                    p_hp = dd.hps.info[1][0]
                    p_sta = dd.staminas.info[1]
                    p_hand = dd.decks.info[1]
                    p_hand_size = dd.hand_sizes.info[1]
                    p_effect = dd.effects.info[1]
                    p_inv = dd.backpacks.info[1]

                    if dd.afk <= 6:
                        if dd.hps.info[1][0] > 1 and dd.staminas.info[1] > 1:
                            await stats_msg.edit(embed=dd.show_stats())
                            await hands_msg.edit(embed=dd.show_hand())

                            death_award = {
                                p: [
                                    random.randint(u.mobs_dict(levels, i)["death reward"][p][0][0],
                                                   u.mobs_dict(levels, i)["death reward"][p][0][1]),
                                    u.mobs_dict(levels, i)["death reward"][p][1]
                                ]
                                if p not in ["coins", "exps", "gems"] else 1
                                for i in enemynames for p in u.mobs_dict(levels, i)["death reward"]
                            }
                            pre_message.append("You successfully defeated " + ','.join(list(dict.fromkeys(enemynames))[:]) + "!")

                            if dd.hps.info[2][0] < 1:
                                dm.log_quest(1, len(dd.players.info), a_id)

                            loot_factor = 1
                            golden_greed = 1

                            if position[0] == "boss raid":
                                loot_factor = 1 + raid_levels // 5
                            if "golden greed" in perks:
                                golden_greed = perks['golden greed']

                            coin_loot = golden_greed * loot_factor * sum([random.randint(
                                u.mobs_dict(levels, i)["death reward"]['coins'][0],
                                u.mobs_dict(levels, i)["death reward"]['coins'][1]) for i in enemynames])
                            gained_coins += coin_loot
                            p_datas[5] += coin_loot
                            pre_message.append("Gained " + str(coin_loot) + " golden coins")
                            exp_loot = loot_factor * sum([random.randint(
                                u.mobs_dict(levels, i)["death reward"]['exps'][0],
                                u.mobs_dict(levels, i)["death reward"]['exps'][1]) for i in enemynames])
                            gained_exps += exp_loot
                            p_datas[4] += exp_loot
                            pre_message.append("Gained " + str(exp_loot) + " experience points")
                            try:
                                gem_loot = loot_factor * round(sum([random.randint(
                                    u.mobs_dict(levels, i)["death reward"]['gems'][0],
                                    u.mobs_dict(levels, i)["death reward"]['gems'][1]) for i in
                                    enemynames]) / 100)
                                gained_gems += gem_loot
                                p_datas[6] += gem_loot
                                pre_message.append("Gained " + str(gem_loot) + " shiny gems!")
                            except:
                                pass

                            for translator in death_award:
                                if not u.items_dict(translator)["name"] == "Glitching":
                                    if random.randint(1, 10000) <= death_award[translator][1]:
                                        item_info = u.items_dict(translator)
                                        items_to_take = 1
                                        if u.get_bp_weight(p_inv) + u.items_dict(item_info["name"])["weight"] * death_award[translator][0] <= 100:
                                            items_to_take = death_award[translator][0]
                                            pre_message.append(
                                                "Obtained " + translator.title() + " x" + str(death_award[translator][0]) + "!")
                                        elif u.get_bp_weight(p_inv) + u.items_dict(item_info["name"])["weight"] <= 100:
                                            items_to_take = math.floor((100 - u.get_bp_weight(p_inv)) /
                                                                       u.items_dict(item_info["name"])[
                                                                           "weight"])
                                            pre_message.append("Obtained " + translator.title() + " x" + str(math.floor(
                                                (100 - u.get_bp_weight(p_inv)) /
                                                u.items_dict(item_info["name"])["weight"])) + "!")
                                        else:
                                            items_to_take = 0
                                            pre_message.append("Your backpack is full, failed to obtain " + translator.title() + "!")
                                        if not translator.lower() in p_inv and items_to_take != 0:
                                            p_inv[translator.lower()] = {"items": items_to_take}
                                        elif items_to_take != 0:
                                            p_inv[translator.lower()]["items"] += items_to_take

                        else:
                            await stats_msg.edit(embed=dd.show_stats())
                            await hands_msg.edit(embed=dd.show_hand())
                            pre_message.append(f"You got defeated by {' '.join(enemynames[:])}!")
                    elif dd.afk == 7:
                        await stats_msg.edit(embed=dd.show_stats())
                        await hands_msg.edit(embed=dd.show_hand())
                        pre_message.append(f"The battle went on a tie!")
                    elif dd.afk == 8:
                        await stats_msg.edit(embed=dd.show_stats())
                        await hands_msg.edit(embed=dd.show_hand())
                        pre_message.append(f"You fled away successfully!")

                if index[2] == "end":
                    if index[0] == "coin loss":
                        coin_loss = random.randint(ADVENTURES["end"]["coin loss"][0], ADVENTURES["end"]["coin loss"][1])
                        if p_datas[5] < abs(coin_loss) and coin_loss < 0:
                            coin_loss = p_datas[5]
                            p_datas[5] = 0
                            pre_message.append("You lost all your " + str(
                                coin_loss) + " golden coins! You are as poor as a rat now! Even the thief felt sympathy for you.")
                        else:
                            p_datas[5] += coin_loss
                            pre_message.append(
                                "You lost " + str(abs(coin_loss)) + " golden coins, you still have " + str(
                                    p_datas[5]) + " more golden coins left!")
                        gained_coins = coin_loss

                if index[2] == "trade":
                    finished = False
                    offers = {}
                    trader = u.mobs_dict(math.floor(p_distance / 200), choices['name'])
                    trading_pre_message = ""
                    while len(offers) < 2:
                        for translator in range(len(trader["offers"])):
                            if random.randint(1, 10000) <= int(list(trader["offers"].keys())[translator]):
                                offers[list(trader["offers"].values())[translator]] = trader["recipe"][
                                    list(trader["offers"].values())[translator]]
                    offers["Finish trading"] = ["pass"]

                    def offer_choices(offers, msg):
                        logs = []
                        for x in range(len(offers) - 1):
                            cost = []
                            for y in list(offers.values())[x]:
                                cost.append(str(y[1]) + " " + y[0])
                            logs.append(
                                "**[" + str(x + 1) + "]** " + list(offers.keys())[x] + " - " + ", ".join(cost[:]))
                        logs.append("**[" + str(len(offers)) + "]** " + list(offers.keys())[len(offers) - 1])
                        if msg == "":
                            embed = discord.Embed(title=None, description="```" + choices["name"] + "'s offers:```", color=discord.Color.gold())
                        else:
                            embed = discord.Embed(title=None,
                                                  description="```" + msg + "\n\n" + choices['name'] + "'s offers:```", color=discord.Color.gold())
                        embed.add_field(name="Choices", value="\n".join(logs[:]))
                        embed.set_thumbnail(url=ctx.message.author.avatar.url)
                        embed.set_footer(text=f"{u.PREF}exit | {u.PREF}backpack")
                        return embed

                    while not leave and not afk and not finished:
                        option = 0
                        await adventure_msg.edit(embed=offer_choices(offers, trading_pre_message))
                        while not leave and not afk:
                            try:
                                msg_reply = await self.bot.wait_for("message", timeout=60.0,
                                                                    check=checks.valid_reply([''], [ctx.message.author], [ctx.message.channel]))
                            except asyncio.TimeoutError:
                                afk = True
                                await ctx.send(f"{mention}, you went idling and the adventure was ended.")
                                break

                            try:
                                option = abs(math.floor(int(msg_reply.content[len(u.PREF):])) + 1 - 1)
                            except:
                                msg_reply = msg_reply.content[len(u.PREF):].lower()
                                if msg_reply == "exit":
                                    leave = True
                                    await ctx.send(f"{mention}, you quit this adventure")
                                    break
                                elif msg_reply in ["bp", "backpack"]:
                                    embed = u.display_backpack(p_inv, ctx.message.author, "Backpack")
                                    embed.add_field(name="Stats:", value=f"Health - {p_hp}/{p_max_hp} \n"
                                                                         f"Stamina - {p_sta} \n"
                                                                         f"Traveled {p_distance} meters", inline=False)
                                    if perks != {}:
                                        embed.add_field(name="Perks:",
                                                        value="".join([f"**{all_perks[i]['name']}** x{perks[i]}\n{u.ICON['alpha']}*{all_perks[i.lower()]['description']}*\n" for i in perks][:]))
                                    await ctx.send(embed=embed)
                                elif msg_reply in ['r', 'ref', 'refresh']:
                                    adventure_msg = await ctx.send(embed=offer_choices(offers, trading_pre_message), file=None)
                                option = 0
                            if not 1 <= option <= len(offers):
                                if msg_reply not in ['exit', 'bp', 'backpack', 'r', 'ref', 'refresh']:
                                    await ctx.send(
                                        "You can only enter numbers `1-" + str(len(offers)) + "`!")
                            else:
                                break
                        if len(offers) == option:
                            finished = True
                        else:
                            trade_success = True
                            items_weight = 0
                            trade_items_to_take = {}
                            for translator in list(offers.values())[option - 1]:
                                if translator[0].lower() in p_inv:
                                    if translator[1] <= p_inv[translator[0].lower()]["items"] and trade_success:
                                        trade_items_to_take[translator[0].lower()] = translator[1]
                                        items_weight += u.items_dict(translator[0].lower())["weight"] * translator[1]
                                    else:
                                        trade_success = False
                                        break
                                else:
                                    trade_success = False
                                    break
                            if not trade_success:
                                trading_pre_message = "You don't have the items required to afford the " + \
                                                      list(offers.keys())[option - 1].title() + "!"
                            elif u.get_bp_weight(p_inv) - items_weight + u.items_dict(list(offers.keys())[option - 1])["weight"] > 100:
                                trading_pre_message = "You can't buy " + list(offers.keys())[option - 1].title() + " due to your rather full backpack!"
                            else:
                                cost = []
                                for translator in list(offers.values())[option - 1]:
                                    cost.append(str(translator[1]) + " " + translator[0].title())
                                trading_pre_message = "You successfully obtained " + list(offers.keys())[
                                    option - 1].title() + " with " + ", ".join(cost[:]) + "!"
                                if not list(offers.keys())[option - 1].lower() in p_inv:
                                    p_inv[list(offers.keys())[option - 1].lower()] = {"items": 1}
                                else:
                                    p_inv[list(offers.keys())[option - 1].lower()]["items"] += 1
                                for translator in trade_items_to_take:
                                    p_inv[translator]["items"] -= trade_items_to_take[translator]
                                p_inv = u.clear_bp(p_inv)

                sql = "update playersinfo set exps = exps + %s, coins = coins + %s, gems = gems + %s where userid = %s"
                val = (gained_exps, gained_coins, gained_gems, str(a_id))
                if gained_coins > 0:
                    dm.log_quest(5, gained_coins, a_id)
                dm.cur.execute(sql, val)
                dm.db.commit()

            if p_sta <= 0 or leave or afk or p_hp <= 0 or section == "end":
                if pre_message:
                    pre_message.append("\n")
                if p_sta <= 0:
                    p_sta = 0
                    embed = discord.Embed(title="You ran out of stamina!",
                                          description="```" + "\n".join(pre_message) + "You died from exhaustion!``` ```Loss: \n" + \
                                                      u.display_backpack(p_inv, ctx.message.author, "Backpack", [0, -2]) + "```",
                                          color=discord.Color.gold())
                    p_inv = {}
                if p_hp <= 0:
                    p_hp = 0
                    embed = discord.Embed(
                        title="You ran out of health!",
                        description="```" + "\n".join(pre_message) + "The world starts to go dark. You struggled to breath properly. You died!``` ```Loss: \n" + \
                                    u.display_backpack(p_inv, ctx.message.author, "Backpack", [0, -2]) + "```",
                        color=discord.Color.gold()
                    )
                    p_inv = {}
                if leave:
                    embed = discord.Embed(
                        title="You gave up keep adventuring!",
                        description="```" + "\n".join(pre_message) +
                                    "You got nervous and stopped yourself. It's probably better to rest up then visit the place again. "
                                    "You quickly backtracked and see your hometown again quickly.```",
                        color=discord.Color.gold()
                    )
                if afk:
                    embed = discord.Embed(
                        title="You went afk and left!",
                        description="```" + "\n".join(pre_message) + "You stood motionlessly and somehow forgot what you were going to do. "
                                                                     "Just like that, you traveled back to your hometown, wondering why you were here in the first place.```",
                        color=discord.Color.red()
                    )
                if section == "end":
                    p_hp = 0
                    embed = discord.Embed(
                        title="You finished this adventure!",
                        description="```" + "\n".join(pre_message) + "CONGRATULATIONS! You have endured and survived all the obstacles stood in your way. You achieved what many failed to acomplish!```",
                        color=discord.Color.green()
                    )
                    if location == "enchanted forest" and badges[5] == "0":
                        badges[5] = '1'
                        dm.cur.execute(f"update playersachivements set badges = '{badges}'")
                        dm.db.commit()

                embed.add_field(name="Result:", value="Total distance traveled - " + str(p_distance) + " meters")
                embed.set_thumbnail(url=ctx.message.author.avatar.url)
                embed.set_footer(text=f"Type {u.PREF}adventure to restart!")
                await adventure_msg.edit(embed=embed)

        sql = "update adventuredatas set inventory = %s where userid = %s"
        val = (str(p_inv), str(a_id))
        dm.cur.execute(sql, val)
        dm.db.commit()


async def setup(bot):
    await bot.add_cog(Adventure(bot))
