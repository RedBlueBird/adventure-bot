import random
import math
import string
import asyncio
import json
from copy import deepcopy
import io

from PIL import Image
import discord
from discord.ext import commands

from helpers import checks, BattleData
from helpers.checks import valid_reaction, valid_reply
from helpers import db_manager as dm
import util as u


def choices_list(choices) -> str:
    logs = []
    for c in choices:
        logs.append(f"**[{len(logs) + 1}]** {c}")
    return " \n".join(logs)


def mark_location(bg_pic: str, x: int | float, y: int | float) -> io.BytesIO:
    background = Image.open(f"resources/img/{bg_pic}.png")
    new_image = Image.open("resources/img/marker.png")
    background.paste(new_image, (10 + 32 * x, 32 * y), new_image)
    out = io.BytesIO()
    background.save(out, format="png")
    out.seek(0)
    return out


def setup_minigame(game_name: str, show_map: bool) -> tuple[discord.Embed, discord.File | None]:
    embed = discord.Embed(
        title=f"Mini Game - {game_name}!",
        color=discord.Color.gold()
    )

    logs = [f"• {r}" for r in u.MINIGAMES[game_name]["rules"]]
    embed.add_field(name="Rules", value=" \n".join(logs))

    embed.set_footer(text=f"{u.PREF}exit -quit mini game")
    if show_map:
        if u.MINIGAMES[game_name]["image"] is not None:
            return (
                embed,
                discord.File(u.MINIGAMES[game_name]["image"])
            )
        else:
            return embed, None
    else:
        return embed, None


class Adventure(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases=["ad", "adv"],
        description="Go on an adventure!"
    )
    @checks.not_preoccupied("on an adventure")
    @checks.is_registered()
    async def adventure(self, ctx: commands.Context):
        mention = ctx.author.mention
        a = ctx.author

        lvl = dm.get_user_level(a.id)
        hp = u.level_hp(lvl)
        max_hp = hp
        stamina = 100
        dist = 0
        badges = dm.get_user_badge(a.id)
        deck = dm.get_user_deck(a.id)
        hand = [f"{c[2]}.{c[1]}" for c in deck]
        random.shuffle(hand)

        coins = dm.get_user_coin(a.id)
        gems = dm.get_user_gem(a.id)
        xp = dm.get_user_exp(a.id)

        inv = dm.get_user_inventory(a.id)
        storage = dm.get_user_storage(a.id)
        pos = dm.get_user_position(a.id)
        show_map = dm.get_user_map(a.id)

        afk = False
        leave = False
        adventure = False

        # HOMETOWN EXPLORATION
        loading = discord.Embed(title="Loading...", description=u.ICON['load'])
        adventure_msg = await ctx.send(embed=loading)

        while not leave and not afk and not adventure:
            embed = discord.Embed(
                description=f"```{u.HTOWN[pos]['description']}```",
                color=discord.Color.gold()
            )
            embed.add_field(name="Choices", value=choices_list(u.HTOWN[pos]["choices"]))
            embed.set_thumbnail(url=ctx.author.avatar.url)

            always = ["exit", "map", "backpack", "home", "refresh"]
            embed.set_footer(text=" | ".join(f"{u.PREF}{c}" for c in always))

            if show_map:
                file = discord.File(
                    mark_location("hometown_map", *u.HTOWN[pos]["coordinate"]),
                    filename="hometown_map.png"
                )
                await adventure_msg.edit(embed=embed, attachments=[file])
            else:
                await adventure_msg.edit(embed=embed)

            decision = 0
            while True:
                try:
                    msg_reply = await self.bot.wait_for(
                        "message", timeout=60.0,
                        check=valid_reply("", ctx.author, ctx.message.channel)
                    )
                except asyncio.TimeoutError:
                    afk = True
                    await ctx.reply("You spaced out and the adventure was ended.")
                    break

                content = msg_reply.content[len(u.PREF):]
                if content.isdigit():
                    decision = int(content)
                    if 1 <= decision <= len(u.HTOWN[pos]["choices"]):
                        await msg_reply.delete()
                        break
                    else:
                        await ctx.send(f"You can only enter numbers `1-{len(u.HTOWN[pos]['choices'])}`!")
                else:
                    decision = 0
                    if content == "exit":
                        leave = True
                        await ctx.reply("You quit this adventure.")
                        break

                    elif "map".startswith(content):
                        show_map = not show_map
                        await ctx.reply(f"Map {'shown' if show_map else 'hidden'}")

                    elif content in ["bp", "backpack"]:
                        await ctx.send(embed=u.display_backpack(inv, ctx.author, "Backpack"))

                    elif "home".startswith(content):
                        pos = "south street"
                        decision = 6

                    elif "refresh".startswith(content):
                        if show_map:
                            img = mark_location("hometown_map", *u.HTOWN[pos]["coordinate"])
                            file = discord.File(img, filename="hometown_map.png")
                            adventure_msg = await ctx.send(embed=embed, file=file)
                        else:
                            adventure_msg = await ctx.send(embed=embed)

                    else:
                        await ctx.send("That's an invalid option!")
                        break

            pos = u.HTOWN[pos]["choices"][list(u.HTOWN[pos]["choices"])[decision - 1]]

            if pos[1] == "self" and not afk and not leave:
                if pos[0] in u.HTOWN:
                    pos = pos[0]
                else:
                    await ctx.reply("This route is still in development!")

            elif pos[1] == "selling" and not afk and not leave:
                exiting = False
                await adventure_msg.edit(
                    content=f"`{u.PREF}sell (item_name) (amount)` to sell items\n"
                            f"`{u.PREF}backpack` to check your backpack\n"
                            f"`{u.PREF}info item (item_name)` to check the item sell price\n"
                            f"`{u.PREF}exit` to exit the shops",
                    embed=u.display_backpack(inv, ctx.author, "Backpack")
                )
                while not exiting:
                    try:
                        msg_reply = await self.bot.wait_for(
                            "message", timeout=60.0,
                            check=valid_reply("", ctx.author, ctx.channel)
                        )
                    except asyncio.TimeoutError:
                        exiting = True
                        await ctx.reply("You went idle and decided to exit the shop.")
                        break

                    msg_reply = msg_reply.content[len(u.PREF):].lower().split(" ")
                    if len(msg_reply) < 1:
                        continue

                    elif msg_reply[0] == "exit":
                        break

                    elif msg_reply[0] in ["backpack", "bp"]:
                        await ctx.send(embed=u.display_backpack(inv, ctx.author, "Backpack"))
                        continue

                    elif msg_reply[0] in ['r', 'ref', 'refresh']:
                        adventure_msg = await ctx.send(
                            content=f"`{u.PREF}sell (item_name) (amount)` to sell items\n"
                                    f"`{u.PREF}backpack` to check your backpack\n"
                                    f"`{u.PREF}info item (item_name)` to check the item sell price\n"
                                    f"`{u.PREF}exit` to exit the shops",
                            embed=u.display_backpack(inv, ctx.author, "Backpack")
                        )
                        continue

                    elif len(msg_reply) < 3:
                        continue

                    elif msg_reply[0] == "sell":
                        try:
                            item = u.items_dict(" ".join(msg_reply[1].split("_")[:]))
                            counts = max(int(msg_reply[2]), 1)
                            if not item['name'].lower() in inv:
                                await ctx.send("The selected item(s) is not in your backpack!")
                                continue

                            elif inv[item['name'].lower()]["items"] < counts:
                                await ctx.send("You don't have these much items in your backpack!")
                                continue

                            else:
                                coins += item["sell"] * counts
                                if inv[item['name'].lower()]["items"] == counts:
                                    del inv[item['name'].lower()]
                                else:
                                    inv[item['name'].lower()]["items"] -= counts
                                await ctx.send(
                                    f"You just sold **[{item['rarity']}/{item['weight']}] {item['name']} x{counts}** "
                                    f"for {item['sell'] * counts} {u.ICON['coin']}!")
                                continue
                        except:
                            continue

            elif pos[1] == "buying" and not afk and not leave:
                exiting = False
                coins = dm.get_user_coin(a.id)
                items = [
                    "Forest Fruit", "Fruit Salad", "Raft", "Torch", "Herb",
                    "Health Potion", "Power Potion", "Large Health Potion",
                    "Large Power Potion", "Resurrection Amulet", "Teleportation Stone"
                ]

                offers = []
                for offer in items:
                    item = u.items_dict(offer)
                    offers.append(f"[{item['rarity']}/{item['weight']}] {item['name']} - {item['buy']} gc")

                embed = discord.Embed(
                    title="Jessie's Shop:",
                    description="I have everything adventurers need!\n"
                                "```" + "\n".join(offers) + "```",
                    color=discord.Color.gold()
                )
                await adventure_msg.edit(
                    content=f"`{u.PREF}purchase (item_name) (amount)` to purchase items\n"
                            f"`{u.PREF}backpack` to check your backpack\n"
                            f"`{u.PREF}refresh` to resend the items price list\n"
                            f"`{u.PREF}exit` to exit the shops",
                    embed=embed
                )
                while not exiting:
                    try:
                        msg_reply = await self.bot.wait_for(
                            "message", timeout=60.0,
                            check=valid_reply("", ctx.author, ctx.channel)
                        )
                    except asyncio.TimeoutError:
                        exiting = True
                        await ctx.reply("You decided to exit the shop.")
                        break

                    msg_reply = msg_reply.content[len(u.PREF):].split(" ")
                    if len(msg_reply) < 1:
                        continue
                    elif msg_reply[0].lower() == "exit":
                        break
                    elif msg_reply[0].lower() in ["backpack", "back", "bpack", "bp", "b"]:
                        await ctx.send(embed=u.display_backpack(inv, ctx.author, "Backpack"))
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
                            if not item['name'] in items:
                                await ctx.send("The selected item(s) is not in the offer!")
                                continue
                            elif item["weight"] * counts > 100 - u.get_bp_weight(inv):
                                await ctx.send("You don't have enough space in your backpack!")
                                continue
                            elif item["buy"] * counts > coins:
                                await ctx.send("You don't have enough coins to afford this stuff!")
                                continue
                            else:
                                coins -= item["buy"] * counts
                                if item["name"].lower() in inv:
                                    inv[item["name"].lower()]["items"] += counts
                                else:
                                    inv[item["name"].lower()] = {"items": counts}
                                await ctx.send(
                                    f"You just bought "
                                    f"**[{item['rarity']}/{item['weight']}] {item['name']} x{counts}** "
                                    f"for {item['buy'] * counts} {u.ICON['coin']}!"
                                )
                                continue
                        except:
                            continue

            elif pos[1] == "chest" and not afk and not leave:
                exiting = False
                await adventure_msg.edit(
                    content=f"`{u.PREF}backpack` to check your backpack\n`"
                            f"`{u.PREF}chest` to check your chest\n`"
                            f"`{u.PREF}close` to close your chest and exit\n`"
                            f"`{u.PREF}withdraw/deposit (item_name) (amount)` "
                            f"to take or put items from your backpack and chest",
                    embed=u.display_backpack(storage, ctx.author, "Chest", level=lvl)
                )
                if u.HTOWN[pos]["choices"][list(u.HTOWN[pos]["choices"])[decision - 1]][0] == "chest":
                    while not exiting:
                        try:
                            msg_reply = await self.bot.wait_for(
                                "message", timeout=60.0,
                                check=valid_reply("", ctx.author, ctx.channel)
                            )
                        except asyncio.TimeoutError:
                            exiting = True
                            await ctx.reply("You went idle and decided to close your treasure chest")
                        else:
                            if msg_reply.content[len(u.PREF):len(u.PREF) + 4].lower() == "exit" \
                                    or msg_reply.content[len(u.PREF):len(u.PREF) + 5].lower() == "close":
                                exiting = True
                                await ctx.reply("You closed your treasure chest")
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
                                    adventure_msg = await ctx.send(
                                        content=f"`{u.PREF}backpack` to check your backpack\n"
                                                f"`{u.PREF}chest` to check your chest\n"
                                                f"`{u.PREF}close` to close your chest and exit\n"
                                                f"`{u.PREF}withdraw/deposit (item_name) (amount) "
                                                f"to take or put items from your backpack and chest",
                                        embed=u.display_backpack(storage, ctx.author, "Chest", level=lvl)
                                    )

                                elif inputs[0] in ["backpack", "bp", "b"]:
                                    embed = u.display_backpack(inv, ctx.author, "Backpack")
                                    embed.add_field(
                                        name="Stats:",
                                        value=f"Health - {hp}/{max_hp}\n"
                                              f"Stamina - {stamina}\n"
                                              f"Traveled {dist} meters",
                                        inline=False
                                    )
                                    await ctx.send(embed=embed)

                                elif inputs[0] in ["chest", "ch", "c"]:
                                    await ctx.send(embed=u.display_backpack(storage, ctx.author, "Chest"))

                                elif len(inputs) < 3 or amount < 1:
                                    await ctx.reply(
                                        f"You can only do `" + u.PREF + "backpack`, `" + u.PREF + "chest`, `" + u.PREF + "close`, or `" + u.PREF + "withdraw/deposit (item_name) (amount)`!")

                                elif inputs[0] in ["withdraw", "deposit", "with", "wd", "w", "dep", "de"]:
                                    location = inv if inputs[0] in ["deposit", "dep", "de"] else storage
                                    target = "Backpack" if inputs[0] in ['deposit', 'dep', 'de'] else 'Chest'
                                    if item["name"].lower() in location:
                                        if location[item["name"].lower()]["items"] < amount:
                                            await ctx.reply(
                                                f"You don't have {amount} **[{item['rarity']}/{item['weight']}] {item['name']}** in your {target}!")

                                        elif (location == inv and u.get_bp_weight(
                                                storage) + total_weight > u.chest_storage(lvl)) \
                                                or (location == storage and u.get_bp_weight(
                                            inv) + total_weight > 100):
                                            await ctx.reply(
                                                f"Your {'Backpack' if location != inv else 'Chest'} doesn't have enough space for {amount} **[{item['rarity']}/{item['weight']}] {item['name']}**!")
                                        else:
                                            location[item['name'].lower()]['items'] -= amount
                                            if location == inv:
                                                if not item['name'].lower() in storage:
                                                    storage[item['name'].lower()] = {"items": amount}
                                                else:
                                                    storage[item['name'].lower()]['items'] += amount
                                                inv = u.clear_bp(inv)
                                                await ctx.send(
                                                    f"{mention} You put {amount} **[{item['rarity']}/{item['weight']}] {item['name']}** into your Chest from your backpack!")
                                            else:
                                                if not item['name'].lower() in inv:
                                                    inv[item['name'].lower()] = {"items": amount}
                                                else:
                                                    inv[item['name'].lower()]['items'] += amount
                                                storage = u.clear_bp(storage)
                                                await ctx.send(
                                                    f"{mention} You put {amount} **[{item['rarity']}/{item['weight']}] {item['name']}** into your backpack from your chest!")
                                    else:
                                        await ctx.reply(
                                            f"**[{item['rarity']}/{item['weight']}] {item['name']}** doesn't exist in your {target}!")
                                else:
                                    await ctx.reply(
                                        f"You can only do `{u.PREF}backpack`, `{u.PREF}chest`, `{u.PREF}close`, or `{u.PREF}withdraw/deposit (item_name) (amount)`!")

            elif pos[1] == "mini game" and not afk and not leave:
                dm.queues[a.id] = "playing a mini game"
                exit_game = False
                earned_loots = [0, 0, 0]
                random_number = random.randint(1, 1000)

                def reset(earned_loots):
                    nonlocal xp, coins, gems

                    xp += earned_loots[2]
                    coins += earned_loots[0]
                    gems += earned_loots[1]

                    dm.set_user_coin(a.id, coins)
                    dm.set_user_exp(a.id, xp)
                    dm.set_user_gem(a.id, gems)

                embed, img = setup_minigame(
                    u.HTOWN[pos]["choices"][list(u.HTOWN[pos]["choices"])[decision - 1]][0],
                    show_map
                )
                await adventure_msg.edit(embed=embed, attachments=[img])
                if pos[0] == "coin flip":
                    while not exit_game:
                        try:
                            msg_reply = await self.bot.wait_for(
                                "message", timeout=60.0,
                                check=valid_reply(["flip", "f", "exit"], ctx.author, ctx.channel)
                            )
                        except asyncio.TimeoutError:
                            exit_game = True
                            await ctx.reply("```You accidentally fell asleep and got left out of the game.```")
                        else:
                            if msg_reply.content[len(u.PREF):len(u.PREF) + 4].lower() == "exit":
                                exit_game = True
                                await ctx.reply("You quit this mini game")
                            elif not (msg_reply.content[len(u.PREF + "flip "):].lower() in ["head", "tail", "edge", "h",
                                                                                            "t", "e"] or
                                      msg_reply.content[len(u.PREF + "f "):].lower() in ["head", "tail", "edge", "h",
                                                                                         "t", "e"]):
                                await ctx.reply(
                                    f"```You can only input {u.PREF}exit or {u.PREF}flip (head/tail/edge)```")
                            else:
                                if coins < 100:
                                    await ctx.reply("```You need least 100 golden coins to place a bet!```")
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
                                        await ctx.reply(
                                            f"```You bet on {choice[0]}\n"
                                            f"The coin landed on {result}\n"
                                            f"You lost {abs(earned_loots[0])} golden coins!\n"
                                            f"You still gained {earned_loots[2]} exp though...\n"
                                            f"Better luck next time!```"
                                            f"```>flip (head/tail/edge) -try again \n"
                                            f">exit -quit the mini game```"
                                        )
                                    else:
                                        if result != "edge":
                                            earned_loots[0] += 100
                                            earned_loots[2] += 3
                                            await ctx.reply(
                                                f"```You bet on {choice[0]} \n"
                                                f"The coins landed on {result} \n"
                                                f"You won {earned_loots[0]} golden coins and {earned_loots[2]} XP!```"
                                                "```>flip (head/tail/edge) -try again \n"
                                                ">exit -quit the mini game```"
                                            )
                                        else:
                                            earned_loots[0] += 50000
                                            earned_loots[2] += 100
                                            await ctx.reply(
                                                f"```You bet on {choice[0]} \n"
                                                f"The coins landed on {result} \n"
                                                f"You won {earned_loots[0]} GOLDEN COINS and {earned_loots[2]} XP!"
                                                f"``````>flip (head/tail/edge) -try again \n"
                                                f">exit -quit the mini game```"
                                            )
                                    reset(earned_loots)
                                    earned_loots = [0, 0, 0]
                                    random_number = random.randint(1, 1000)

                if pos[0] == "fishing":
                    while not exit_game:
                        try:
                            msg_reply = await self.bot.wait_for(
                                "message", timeout=60.0,
                                check=valid_reply(["exit", "fish", "f"], ctx.author, ctx.channel)
                            )
                        except asyncio.TimeoutError:
                            exit_game = True
                            await ctx.send(f"{mention} ```You went idle and decided to quit this mini game```")
                        else:
                            if msg_reply.content[len(u.PREF):len(u.PREF) + 4].lower() == "exit":
                                exit_game = True
                                await ctx.reply(f"You quit this mini game")
                            elif coins < 50:
                                await ctx.reply("```You need least 50 golden coins to buy bait!```")
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
                                msg2 = await ctx.reply(
                                    f"```You saw a {rarity} fish!"
                                    f"Try to reply {u.PREF}bait in exactly {waits} seconds!```"
                                )

                                try:
                                    msg_reply2 = await self.bot.wait_for(
                                        "message", timeout=30.0,
                                        check=valid_reply(["bait", "b"], ctx.author, ctx.channel)
                                    )
                                except asyncio.TimeoutError:
                                    await ctx.reply("```The fish got away!```")
                                else:
                                    earned_loots[0] -= 50
                                    success_rate = 0
                                    reply_ms = (msg_reply2.created_at - msg2.created_at).total_seconds()
                                    reply_time = round(abs(waits - reply_ms), 4)
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
                                            dm.log_quest(8, 1, a.id)
                                            to_send = f"```You replied in EXACTLY {reply_ms} SECONDS!!! \n " \
                                                      f"0.000 SECONDS OFF FROM {waits} SECONDS!!! \n"
                                        else:
                                            earned_loots[0] += 100 * award_multiplier
                                            earned_loots[2] += 5
                                            dm.log_quest(8, 1, a.id)
                                            to_send = f"```You replied in {reply_ms} seconds \n" \
                                                      f"{reply_time} seconds off from {waits} seconds! \n"

                                        to_send += f"You caught a {random.choice(fish_dict[{1: 'c', 1.5: 'r', 2.5: 'e', 4.5: 'l'}[award_multiplier]])}, " \
                                                   f"gaining {int(earned_loots[0])} golden coins and {earned_loots[2]} experience points in total! \n" \
                                                   f"``````{u.PREF}fish -try again \n{u.PREF}exit -quit the mini game```"
                                        await ctx.reply(to_send)
                                    else:
                                        earned_loots[2] += 2
                                        await ctx.reply(
                                            f"```You replied in {reply_ms} seconds \n{reply_time} seconds off from {waits} seconds! \n" +
                                            f"The fish fled and you wasted {abs(earned_loots[0])} golden coins on the bait \n"
                                            f"You only gained {earned_loots[2]} experience points \n"
                                            f"Better luck next time! \n``````{u.PREF}fish -try again \n{u.PREF}exit -quit the mini game```"
                                        )
                                    reset(earned_loots)
                                    earned_loots = [0, 0, 0]
                                    random_number = random.randint(1, 1000)

                if pos[0] == "blackjack":
                    while not exit_game:
                        try:
                            msg_reply = await self.bot.wait_for(
                                "message", timeout=60.0,
                                check=valid_reply(["exit", "start", "s"], ctx.author, ctx.channel)
                            )
                        except asyncio.TimeoutError:
                            exit_game = True
                            await ctx.reply("```You dozed off and got kicked out of the blackjack table```")
                        else:
                            deck = deepcopy(u.DECK)
                            aces = deepcopy(u.ACES)
                            if msg_reply.content.lower().startswith(f"{u.PREF}exit"):
                                exit_game = True
                                await ctx.reply("You quit this mini game")
                            elif coins < 100:
                                await ctx.reply("```You need least 100 golden coins to play!```")
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
                                                                            check=valid_reply(
                                                                                ['hit', 'h', 'stand', 's'],
                                                                                [ctx.author],
                                                                                [ctx.message.channel]))
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
                                                while values[1] > 21 and any(
                                                        a in cards[1] and a not in included_aces[1] for a in aces):
                                                    for c in cards[1]:
                                                        if c in aces and c not in included_aces[1]:
                                                            values[1] -= 10
                                                            included_aces[1].append(c)
                                                            break

                                        elif action in ['h', 'hit']:
                                            add_card(random.choice(list(deck)), "self")
                                            while values[0] > 21 and any(
                                                    a in cards[0] and a not in included_aces[0] for a in aces):
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
                                        f"Your total: {values[0]} \n" + " ".join(
                                            cards[0]) + f" \n-------------------------------- \n"
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
                    dm.queues[a.id] = "exploring in the Hometown"
                dm.queues[a.id] = "exploring in the Hometown"

            elif pos[1] == "adventure" and not afk and not leave:
                dm.cur.execute(f"select deck_slot from playersinfo where userid = {a.id}")
                db_deck = f"deck{dm.cur.fetchall()[0][0]}"
                dm.cur.execute(
                    f"select {db_deck} from playersachievements where userid = {a.id}")
                deck = dm.cur.fetchall()[0][0].split(",")
                dm.cur.execute(
                    f"select card_name, card_level from cardsinfo where owned_user = {a.id} and id in ({str(deck)[1:-1]})")
                deck = dm.cur.fetchall()

                if len(deck) == 12:
                    if pos[0] == "boss raid":
                        if lvl < 9:
                            await ctx.send("You need to be at least level 9 to start a boss raid!")
                        elif dm.get_user_ticket(a.id) < 1:
                            await ctx.reply("You need a Raid Ticket to start a boss raid!")
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
                                                                         check=valid_reaction(
                                                                             ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"],
                                                                             [ctx.author], [diff_msg]))
                            except asyncio.TimeoutError:
                                await ctx.send(f"{ctx.author} the host, went afk... :man_facepalming: ")
                            else:
                                if reaction.emoji != "5️⃣":
                                    raid_levels = {"1️⃣": 1, "2️⃣": 5, "3️⃣": 10, "4️⃣": 15}[reaction.emoji]

                                    dm.cur.execute(
                                        f"update playersinfo set tickets = tickets - 1 where userid = {a.id}")
                                    dm.db.commit()
                                    adventure = True
                    else:
                        adventure = True
                else:
                    await ctx.send(f"{mention}, you need 12 cards in your deck in order to go on an adventure!")

        dm.set_user_map(a.id, show_map)
        dm.set_user_inventory(a.id, inv)
        dm.set_user_storage(a.id, storage)

        if adventure:
            location = u.HTOWN[pos]["choices"][list(u.HTOWN[pos]["choices"])[decision - 1]][0]
            event = "main"
            section = "start"
            distance = 0
            travel_speed = 1
            perk_turn = 5
            perks = {}
            boss_spawn = False
            pre_message = []

        u.PERKS = json.load(open('resources/text/perks.json'))
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
        perk_list = list(u.PERKS.keys())

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
                embed = discord.Embed(title=None, description="```" + path[option]["description"] + "```",
                                      color=discord.Color.gold())
            else:
                embed = discord.Embed(title=None, description="```" + "\n".join(msg[:]) + "\n\n" + path[option][
                    "description"] + "```",
                                      color=discord.Color.gold())
            if "choices" in path[option]:
                embed.add_field(name="Choices", value=choices_list(path[option]["choices"]))
            embed.set_thumbnail(url=ctx.author.avatar.url)
            embed.set_footer(text=f"{u.PREF}exit | {u.PREF}backpack | {u.PREF}refresh")
            return [embed, option]

        def perk_decider():
            random.shuffle(perk_list)
            embed = discord.Embed(title=None,
                                  description="```The tireless long journey has paid off! Choose 1 Perk:```",
                                  color=discord.Color.gold())
            embed.add_field(name="Choices", value=choices_list([i.title() for i in perk_list[:3]]))
            embed.set_footer(text=f"{u.PREF}exit | {u.PREF}backpack | {u.PREF}refresh")
            return [embed]

        while not leave and not afk and adventure and hp > 0 and stamina > 0:
            boss_spawn = False
            if section == "start":
                perk_turn -= 1
                stamina -= random.randint(3, 6)
                t_dis = round(travel_speed * random.randint(100, 200))
                if math.floor(dist / 1000) < math.floor((dist + t_dis) / 1000):
                    boss_spawn = True
                    perk_turn = 0
                dist += t_dis
            dm.log_quest(3, t_dis, a.id)

            if perk_turn != 0:
                options = option_decider(u.ADVENTURES[location][event][section], dist, boss_spawn, pre_message)
                pre_message = []
                option = options[1]
                choices = u.ADVENTURES[location][event][section][option]
                await adventure_msg.edit(embed=options[0])
            else:
                options = perk_decider()
                pre_message = []
                choices = {"choices": perk_list[:3]}
                await adventure_msg.edit(embed=options[0])

            choice = 0
            while not leave and not afk and hp > 0 and stamina > 0 and "choices" in choices:
                try:
                    msg_reply = await self.bot.wait_for("message", timeout=60.0,
                                                        check=valid_reply([''], [ctx.author],
                                                                          [ctx.message.channel]))
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
                        embed = u.display_backpack(inv, ctx.author, "Backpack")
                        embed.add_field(name="Stats:", value=f"Health - {hp}/{max_hp} \n" + \
                                                             f"Stamina - {stamina} \n" + \
                                                             f"Traveled {dist} meters", inline=False)
                        if perks != {}:
                            embed.add_field(name="Perks:", value="".join([
                                                                             f"**{u.PERKS[i]['name']}** x{perks[i]}\n{u.ICON['alpha']}*{u.PERKS[i.lower()]['description']}*\n"
                                                                             for i in perks][:]))
                        await ctx.send(embed=embed)
                    elif msg_reply in ['r', 'ref', 'refresh']:
                        adventure_msg = await ctx.send(embed=options[0], file=None)

                    choice = 0

                if not 1 <= choice <= len(choices["choices"]):
                    if not (msg_reply in ['exit', 'bp', 'backpack', 'r', 'refresh', 'ref']):
                        await ctx.send(f"You can only enter numbers `1-{len(choices['choices'])}`!")
                elif perk_turn != 0:
                    feed = u.fulfill_requirement(list(choices["choices"].values())[choice - 1], inv)

                    if feed[0]:
                        if not feed[2] is None:
                            pre_message.append(feed[2])
                        inv = feed[1]
                        await msg_reply.delete()
                        break
                    else:
                        if not feed[2] is None:
                            pre_message.append(feed[2])
                        options = option_decider(u.ADVENTURES[location][event][section], dist, boss_spawn,
                                                 pre_message, option)
                        pre_message = []
                        await adventure_msg.edit(embed=options[0])
                else:
                    if perk_list[choice - 1] in perks:
                        perks[perk_list[choice - 1]] += 1
                    else:
                        perks[perk_list[choice - 1]] = 1

                    if perk_list[choice - 1] == 'vigorous endurance':
                        max_hp = round(max_hp * 1.2)
                    elif perk_list[choice - 1] == 'hot spring':
                        stamina += 40
                    elif perk_list[choice - 1] == "feathered shoe":
                        travel_speed += 0.4
                    elif perk_list[choice - 1] == 'chunk of gold':
                        dm.log_quest(5, 250, a.id)

                        dm.cur.execute(f"update playersinfo set coins = coins + 250 where userid = {a.id}")
                        dm.db.commit()
                    elif perk_list[choice - 1] == "book of knowledge":
                        dm.cur.execute(f"update playersinfo set exps = exps + 150 where userid = {a.id}")
                        dm.db.commit()
                    elif perk_list[choice - 1] == "hidden gem":
                        dm.cur.execute(f"update playersinfo set gems = gems + 1 where userid = {a.id}")
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
                trap_dmg = round(random.randint(choices["damage"][0], choices['damage'][1]) / 100 * round(
                    (100 * u.SCALE[1] ** math.floor(lvl / 2)) * u.SCALE[0]))
                if choices["trap"] == "reaction":
                    await ctx.send(
                        f'Reply `{u.PREF}react` as fast as you can when you see the message "Now!"!')
                    await asyncio.sleep(trap_time)
                    trap_msg = await ctx.send('Now!')
                    try:
                        msg_reply = await self.bot.wait_for("message", timeout=20.0,
                                                            check=valid_reply(['react'], [ctx.author],
                                                                              [ctx.message.channel]))
                    except asyncio.TimeoutError:
                        pre_message.append(f"You went idle and received {trap_dmg * 2} damage!")
                        hp -= trap_dmg * 2
                    else:
                        offset = round((msg_reply.created_at - trap_msg.created_at).total_seconds() * 1000) / 1000
                        pre_message.append(f"You reacted in {offset} seconds")
                        if offset <= 0.7:
                            pre_message.append(f"You successfully dodged the trap!")
                        else:
                            pre_message.append(f"You received {trap_dmg} damage!")
                            hp -= trap_dmg
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
                                                            check=valid_reply([''], [ctx.author],
                                                                              [ctx.message.channel]))
                    except asyncio.TimeoutError:
                        pre_message.append(f"You went idle and received {trap_dmg * 2} damage!")
                        hp -= trap_dmg * 2
                    else:
                        seq = msg_reply.content[len(u.PREF):].lower()
                        correct_seq = "".join([sequence_le[i] for i in rands])
                        pre_message.append(f'The correct sequence is "{correct_seq}" \nYour sequence is "{seq}"')
                        if seq == correct_seq:
                            pre_message.append("You successfully avoided the trap!")
                        else:
                            pre_message.append(f"You received {trap_dmg} damage!")
                            hp -= trap_dmg

            elif not leave and not afk and hp > 0 and stamina > 0:
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
                    if u.get_bp_weight(inv) + u.items_dict(item_info["name"])["weight"] * item_amount <= 100:
                        items_to_take = item_amount
                        pre_message.append(f"You successfully obtained {item_info['name'].title()} x{item_amount}!")
                    elif u.get_bp_weight(inv) + u.items_dict(item_info["name"])["weight"] <= 100:
                        items_to_take = math.floor(
                            (100 - u.get_bp_weight(inv)) / u.items_dict(item_info["name"])["weight"])
                        pre_message.append(
                            f"You successfully obtained {item_info['name'].title()} x{math.floor((100 - u.get_bp_weight(inv)) / u.items_dict(item_info['name'])['weight'])}!")
                    else:
                        items_to_take = 0
                        pre_message.append(f"Your backpack is full, failed to obtain {item_info['name'].title()}!")
                    if not item_info['name'].lower() in inv and items_to_take != 0:
                        dm.log_quest(2, u.items_dict(item_info["name"])["weight"] * items_to_take,
                                     a.id)
                        inv[item_info['name'].lower()] = {"items": items_to_take}
                    elif items_to_take != 0:
                        dm.log_quest(2, u.items_dict(item_info['name'])["weight"] * items_to_take,
                                     a.id)
                        inv[item_info['name'].lower()]["items"] += items_to_take

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
                    levels = math.floor((dist - 500) / 200) if dist > 500 else 1
                    if pos[0] == "boss raid":
                        levels = raid_levels
                    ad_decks = [hand] + [random.sample(
                        [f"{levels + random.randint(0, 3)}.{x}" for x in u.mobs_dict(levels, i)["deck"]],
                        len(u.mobs_dict(levels, i)['deck'])) for i in enemynames]
                    ad_hps = [[hp, 0, max_hp, 0, 0]] + \
                             [[u.mobs_dict(levels, i)["health"], 0, u.mobs_dict(levels, i)['health'], 0, 0] for i in
                              enemynames]
                    dd = BattleData({1: [1], 2: [i + 2 for i in range(len(enemynames))]},  # teams
                                    [ctx.author] + enemynames,  # names
                                    [a.id] + [123] * len(enemynames),  # ids
                                    ad_decks,  # decks
                                    [inv] + [{} for i in range(len(enemynames))],  # backpack
                                    ad_hps,  # hps
                                    [stamina] + [u.mobs_dict(levels, i)["stamina"] for i in enemynames],  # stamina
                                    len(enemynames) + 1)
                    loading = discord.Embed(title="Loading...", description=u.ICON['load'])
                    stats_msg = await ctx.send(embed=loading)
                    hands_msg = await ctx.send(embed=loading)

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
                                                                          check=valid_reply([''], [ctx.author],
                                                                                            [ctx.message.channel]))
                            except asyncio.TimeoutError:
                                dd.hps.info[1][0] = 0
                                dd.staminas.info[1] = 0
                                dd.descriptions.info[1].append("Went afk!")
                            else:
                                the_message = dd.interpret_message(replied_message.content[len(u.PREF):],
                                                                   str(dd.players.info[1]), 1)
                                if isinstance(the_message, str) and the_message not in ["skip", "flee", "refresh",
                                                                                        "backpack"]:
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
                                            if "on_hand" in u.cards_dict(dd.decks.info[1][y].split(".")[0],
                                                                         dd.decks.info[1][y].split(".")[1]):
                                                dd.execute_card_offense(int(dd.decks.info[1][y].split(".")[0]),
                                                                        dd.decks.info[1][y].split(".")[1], 1, 1,
                                                                        "on_hand")
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
                                    embed.add_field(name="Stats:", value=f"Health - {hp}/{max_hp} \n" + \
                                                                         f"Stamina - {stamina} \n" + \
                                                                         f"Traveled {dist} meters", inline=False)
                                    if perks != {}:
                                        embed.add_field(name="Perks:", value="".join([
                                                                                         f"**{u.PERKS[i]['name']}** x{perks[i]}\n{u.ICON['alpha']}*{u.PERKS[i.lower()]['description']}*\n"
                                                                                         for i in perks][:]))
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
                                                                        dd.decks.info[1][y].split(".")[1], 1, 1,
                                                                        "on_hand")
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
                            if dd.afk == 0 and not dd.freeze_skips.info[e_index] and dd.hps.info[e_index][0] > 0 and \
                                    dd.staminas.info[e_index] > 0:
                                rng_move = random.randint(1, dd.hand_sizes.info[e_index])
                                if dd.stored_energies.info[e_index] >= \
                                        u.cards_dict(int(dd.decks.info[e_index][rng_move - 1].split(".")[0]),
                                                     dd.decks.info[e_index][rng_move - 1].split(".")[1])["cost"]:
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
                                    dd.stored_energies.info[e_index] -= sum(
                                        [u.cards_dict(int(dd.decks.info[e_index][x - 1].split(".")[0]),
                                                      dd.decks.info[e_index][x - 1].split(".")[1])["cost"] for x in
                                         dd.move_numbers.info[e_index]])
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
                                                dd.decks.info[e_index][translator - 1] = card[0] + "." + card_info[
                                                    "rewrite"]
                                            if "stay" in card_info:
                                                if random.randint(1, 100) <= card_info['stay']:
                                                    z += 1
                                                    dd.descriptions.info[e_index].append(
                                                        f"*[{u.rarity_cost(card[1])}] {card[1]} lv:{card[0]}* stayed in your hand!")
                                                # dd.new_line(e_index)
                                                else:
                                                    dd.decks.info[e_index].insert(len(dd.decks.info[e_index]),
                                                                                  dd.decks.info[e_index].pop(
                                                                                      translator - 1))
                                            else:
                                                dd.decks.info[e_index].insert(len(dd.decks.info[e_index]),
                                                                              dd.decks.info[e_index].pop(
                                                                                  translator - 1))
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
                                dd.multipliers.info[1] = [
                                    u.PERKS[translator.lower()]['multiplier'][i] * perks[translator] +
                                    dd.multipliers.info[1][i] for i in range(5)]
                            for translator in dd.item_used.info:
                                if dd.item_used.info[translator][0] != "None":
                                    dd.execute_card_defense(-1, dd.item_used.info[translator][0], translator,
                                                            dd.item_used.info[translator][1])
                                    dd.execute_card_offense(-1, dd.item_used.info[translator][0], translator,
                                                            dd.item_used.info[translator][1])
                                    dd.execute_card_special(-1, dd.item_used.info[translator][0], translator,
                                                            dd.item_used.info[translator][1])
                            for translator in range(cards_length[-1]):
                                for y in range(1, len(dd.used_cards.info) + 1):
                                    if len(dd.used_cards.info[y]) > translator:
                                        if y == 1 and "soul of fire" in perks:
                                            dd.apply_effects('burn', {'burn': [perks['soul of fire'], 'target']}, 1,
                                                             int(dd.used_cards.info[y][translator].split(".")[2]))
                                        if y == 1 and "devil's core" in perks:
                                            dd.apply_effects('curse', {'curse': [perks["devil's core"], 'target']}, 1,
                                                             int(dd.used_cards.info[y][translator].split(".")[2]))
                                        if y == 1 and 'essence of venom' in perks:
                                            dd.apply_effects('poison',
                                                             {'poison': [perks['essence of venom'], 'target']}, 1,
                                                             int(dd.used_cards.info[y][translator].split(".")[2]))
                                        if y == 1 and 'unblemished prime crystal' in perks:
                                            dd.apply_effects('chill',
                                                             {'chill': [perks['unblemished prime crystal'], 'target']},
                                                             1, int(dd.used_cards.info[y][translator].split(".")[2]))
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

                    hp = dd.hps.info[1][0]
                    stamina = dd.staminas.info[1]
                    hand = dd.decks.info[1]
                    p_hand_size = dd.hand_sizes.info[1]
                    p_effect = dd.effects.info[1]
                    inv = dd.backpacks.info[1]

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
                            pre_message.append(
                                "You successfully defeated " + ','.join(list(dict.fromkeys(enemynames))[:]) + "!")

                            if dd.hps.info[2][0] < 1:
                                dm.log_quest(1, len(dd.players.info), a.id)

                            loot_factor = 1
                            golden_greed = 1

                            if pos[0] == "boss raid":
                                loot_factor = 1 + raid_levels // 5
                            if "golden greed" in perks:
                                golden_greed = perks['golden greed']

                            coin_loot = golden_greed * loot_factor * sum([random.randint(
                                u.mobs_dict(levels, i)["death reward"]['coins'][0],
                                u.mobs_dict(levels, i)["death reward"]['coins'][1]) for i in enemynames])
                            gained_coins += coin_loot
                            coins += coin_loot
                            pre_message.append("Gained " + str(coin_loot) + " golden coins")
                            exp_loot = loot_factor * sum([random.randint(
                                u.mobs_dict(levels, i)["death reward"]['exps'][0],
                                u.mobs_dict(levels, i)["death reward"]['exps'][1]) for i in enemynames])
                            gained_exps += exp_loot
                            xp += exp_loot
                            pre_message.append("Gained " + str(exp_loot) + " experience points")
                            try:
                                gem_loot = loot_factor * round(sum([random.randint(
                                    u.mobs_dict(levels, i)["death reward"]['gems'][0],
                                    u.mobs_dict(levels, i)["death reward"]['gems'][1]) for i in
                                    enemynames]) / 100)
                                gained_gems += gem_loot
                                gems += gem_loot
                                pre_message.append("Gained " + str(gem_loot) + " shiny gems!")
                            except:
                                pass

                            for translator in death_award:
                                if not u.items_dict(translator)["name"] == "Glitching":
                                    if random.randint(1, 10000) <= death_award[translator][1]:
                                        item_info = u.items_dict(translator)
                                        items_to_take = 1
                                        if u.get_bp_weight(inv) + u.items_dict(item_info["name"])["weight"] * \
                                                death_award[translator][0] <= 100:
                                            items_to_take = death_award[translator][0]
                                            pre_message.append(
                                                "Obtained " + translator.title() + " x" + str(
                                                    death_award[translator][0]) + "!")
                                        elif u.get_bp_weight(inv) + u.items_dict(item_info["name"])["weight"] <= 100:
                                            items_to_take = math.floor((100 - u.get_bp_weight(inv)) /
                                                                       u.items_dict(item_info["name"])[
                                                                           "weight"])
                                            pre_message.append("Obtained " + translator.title() + " x" + str(math.floor(
                                                (100 - u.get_bp_weight(inv)) /
                                                u.items_dict(item_info["name"])["weight"])) + "!")
                                        else:
                                            items_to_take = 0
                                            pre_message.append(
                                                "Your backpack is full, failed to obtain " + translator.title() + "!")
                                        if not translator.lower() in inv and items_to_take != 0:
                                            inv[translator.lower()] = {"items": items_to_take}
                                        elif items_to_take != 0:
                                            inv[translator.lower()]["items"] += items_to_take

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
                        coin_loss = random.randint(u.ADVENTURES["end"]["coin loss"][0],
                                                   u.ADVENTURES["end"]["coin loss"][1])
                        if coins < abs(coin_loss) and coin_loss < 0:
                            coin_loss = coins
                            coins = 0
                            pre_message.append("You lost all your " + str(
                                coin_loss) + " golden coins! You are as poor as a rat now! Even the thief felt sympathy for you.")
                        else:
                            coins += coin_loss
                            pre_message.append(
                                "You lost " + str(abs(coin_loss)) + " golden coins, you still have " + str(
                                    coins) + " more golden coins left!")
                        gained_coins = coin_loss

                if index[2] == "trade":
                    finished = False
                    offers = {}
                    trader = u.mobs_dict(math.floor(dist / 200), choices['name'])
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
                            embed = discord.Embed(title=None, description="```" + choices["name"] + "'s offers:```",
                                                  color=discord.Color.gold())
                        else:
                            embed = discord.Embed(title=None,
                                                  description="```" + msg + "\n\n" + choices['name'] + "'s offers:```",
                                                  color=discord.Color.gold())
                        embed.add_field(name="Choices", value="\n".join(logs[:]))
                        embed.set_thumbnail(url=ctx.author.avatar.url)
                        embed.set_footer(text=f"{u.PREF}exit | {u.PREF}backpack")
                        return embed

                    while not leave and not afk and not finished:
                        option = 0
                        await adventure_msg.edit(embed=offer_choices(offers, trading_pre_message))
                        while not leave and not afk:
                            try:
                                msg_reply = await self.bot.wait_for("message", timeout=60.0,
                                                                    check=valid_reply([''], [ctx.author],
                                                                                      [ctx.message.channel]))
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
                                    embed = u.display_backpack(inv, ctx.author, "Backpack")
                                    embed.add_field(name="Stats:", value=f"Health - {hp}/{max_hp} \n"
                                                                         f"Stamina - {stamina} \n"
                                                                         f"Traveled {dist} meters", inline=False)
                                    if perks != {}:
                                        embed.add_field(name="Perks:",
                                                        value="".join([
                                                                          f"**{u.PERKS[i]['name']}** x{perks[i]}\n{u.ICON['alpha']}*{u.PERKS[i.lower()]['description']}*\n"
                                                                          for i in perks][:]))
                                    await ctx.send(embed=embed)
                                elif msg_reply in ['r', 'ref', 'refresh']:
                                    adventure_msg = await ctx.send(embed=offer_choices(offers, trading_pre_message),
                                                                   file=None)
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
                                if translator[0].lower() in inv:
                                    if translator[1] <= inv[translator[0].lower()]["items"] and trade_success:
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
                            elif u.get_bp_weight(inv) - items_weight + u.items_dict(list(offers.keys())[option - 1])[
                                "weight"] > 100:
                                trading_pre_message = "You can't buy " + list(offers.keys())[
                                    option - 1].title() + " due to your rather full backpack!"
                            else:
                                cost = []
                                for translator in list(offers.values())[option - 1]:
                                    cost.append(str(translator[1]) + " " + translator[0].title())
                                trading_pre_message = "You successfully obtained " + list(offers.keys())[
                                    option - 1].title() + " with " + ", ".join(cost[:]) + "!"
                                if not list(offers.keys())[option - 1].lower() in inv:
                                    inv[list(offers.keys())[option - 1].lower()] = {"items": 1}
                                else:
                                    inv[list(offers.keys())[option - 1].lower()]["items"] += 1
                                for translator in trade_items_to_take:
                                    inv[translator]["items"] -= trade_items_to_take[translator]
                                inv = u.clear_bp(inv)

                if gained_coins > 0:
                    dm.log_quest(5, gained_coins, a.id)

                sql = "update playersinfo set exps = exps + %s, coins = coins + %s, gems = gems + %s where userid = %s"
                val = (gained_exps, gained_coins, gained_gems, a.id)
                dm.cur.execute(sql, val)
                dm.db.commit()

            if stamina <= 0 or leave or afk or hp <= 0 or section == "end":
                if pre_message:
                    pre_message.append("\n")
                if stamina <= 0:
                    stamina = 0
                    embed = discord.Embed(title="You ran out of stamina!",
                                          description="```" + "\n".join(
                                              pre_message) + "You died from exhaustion!``` ```Loss: \n" + \
                                                      u.display_backpack(inv, ctx.author, "Backpack",
                                                                         [0, -2]) + "```",
                                          color=discord.Color.gold())
                    inv = {}
                if hp <= 0:
                    hp = 0
                    embed = discord.Embed(
                        title="You ran out of health!",
                        description="```" + "\n".join(
                            pre_message) + "The world starts to go dark. You struggled to breath properly. You died!``` ```Loss: \n" + \
                                    u.display_backpack(inv, ctx.author, "Backpack", [0, -2]) + "```",
                        color=discord.Color.gold()
                    )
                    inv = {}
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
                        description="```" +
                                    pre_message + "\n"
                                                  "You stood motionlessly and somehow forgot what you were going to do.\n"
                                                  "Just like that, you traveled back to your hometown, "
                                                  "wondering why you were here in the first place."
                                                  "```",
                        color=discord.Color.red()
                    )
                if section == "end":
                    hp = 0
                    embed = discord.Embed(
                        title="You finished this adventure!",
                        description="```" + "\n".join(
                            pre_message) + "CONGRATULATIONS! You have endured and survived all the obstacles stood in your way. You achieved what many failed to acomplish!```",
                        color=discord.Color.green()
                    )
                    if location == "enchanted forest" and (badges & (1 << 5)) == 0:
                        badges |= 1 << 5
                        dm.set_user_badge(a.id, badges)

                embed.add_field(name="Result:", value=f"Total distance traveled - {dist} meters")
                embed.set_thumbnail(url=ctx.author.avatar.url)
                embed.set_footer(text=f"Type {u.PREF}adventure to restart!")
                await adventure_msg.edit(embed=embed)

        dm.set_user_inventory(a.id, inv)


async def setup(bot):
    await bot.add_cog(Adventure(bot))
