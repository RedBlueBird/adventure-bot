import random
import math
import datetime as dt
import time as times
import asyncio

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context

from helpers import db_manager as dm
import util as u

_today = str(dt.date.today() - dt.timedelta(days=1))


class Sys(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.background_task.start()

    @commands.hybrid_command(
        name="register",
        description="Registers the author of the bot.",
    )
    async def register(self, ctx: Context):
        """Registers the author of the bot."""
        member = ctx.message.author

        user_cooldown = dm.get_user_cooldown(member.id)
        if user_cooldown:
            if user_cooldown == 0:
                await ctx.send(f"{ctx.message.author.mention}, you're already registered in this bot!")
            else:
                await ctx.send(
                    "You have to wait " +
                    u.time_converter(user_cooldown) +
                    " before you can send another command!"
                )
            return

        await ctx.send(f"*registering {ctx.message.author.mention}...*")

        card_names = [
            "Stab", "Stab", "Shield", "Shield", "Strike", "Strike",
            "Punch", "Punch", "Heal", "Slash", "Explode", "Aim"
        ]
        owned_user = [member.id for i in range(12)]
        card_levels = [4 for i in range(12)]
        dm.add_user_cards(list(zip(owned_user,card_names,card_levels)))

        dm.add_user(member.id)
        dm.set_user_coin(250, member.id)
        dm.set_user_gems(5, member.id)
        dm.set_user_premium(dt.datetime.today() + dt.timedelta(days=7), member.id)
        dm.set_user_register_date(dt.datetime.today(), member.id)
        dm.set_user_position("home", member.id)
        dm.set_user_inventory("{}", member.id)
        dm.set_user_storage("{}", member.id)

        user_cards = dm.get_user_cards(0,500,1,member.id)
        for card in user_cards:
            dm.set_user_card_deck(1,1,card[0],member.id)

        deals_cards = []
        for _ in range(9):
            deals_cards.append(u.add_a_card(1))
        dm.set_user_deals(','.join(deals_cards), member.id)

        await ctx.send(
            "**FREE PREMIUM MEMBERSHIP** for 2 weeks obtained!\n"
            f"Registered {ctx.message.author.mention} into this bot! "
            f"Do `{u.PREF}tutorial` to get started!"
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content = message.content.lower()
        if (content.startswith(f"{u.PREF}pong")
                or content.startswith("<@521056196380065802>")
                or content.startswith("<@!521056196380065802>")):
            ms = int(self.bot.latency * 1000)
            await message.channel.send(f'Pong! {ms} ms. Bot command prefix is `{u.PREF}`!')

        member = message.author  # shorthand
        user_level = dm.get_user_level(member.id)

        if not user_level:
            return

        user_exp = dm.get_user_exp(member.id)
        user_premium_date = dm.get_user_premium(member.id)

        if (user_exp < math.floor(int((user_level ** 2) * 40 + 60)) and
                int(user_level[3]) < 30 or int(user_level[3]) == 30):
            if profile[16] > 0:
                print("hi")
                #user_premium_date > dt.datetime.today()
        else:
            level_msg = []
            if (profile[3] + 1) % 2 == 0:
                add_hp = round(
                    (u.SCALE[1] ** math.floor((profile[3] + 1) / 2) -
                     u.SCALE[1] ** math.floor(profile[3] / 2)) * 100 * u.SCALE[0]
                )
                level_msg.append(f"Max health +{add_hp}!")

            """
            Each element of this list corresponds to what will be unlocked when a player levels up.
            The first element is when level 2 is reached, and then it increments by 1 so on.
            Empty strings signify that no particular special thing is unlocked.
            """
            level_chart = [
                f"{u.PREF}Quest is unlocked!",
                f"{u.PREF}Shop is unlocked!",
                f"{u.PREF}Coop is unlocked! \n"
                f"Daily shop max card level +1!",
                f"{u.PREF}Battle for PvP is unlocked!",
                f"Deck slot +1!",
                f"{u.PREF}Trade is unlocked! \n"
                f"Adventure Chest Storage +50!",
                f"Daily shop max card level +1!",
                f"Adventure Boss Raids is unlocked! \n"
                f"Raid Tickets is unlocked!",
                f"Daily shop min card level +1!",
                f"Adventure Cemetery Map unlocked!",
                f"Daily shop max card level +1!",
                f"Adventure Hometown chest storage +25!",
                f"",
                f"Deck slot +1!",
                f"Daily shop max card level +1!",
                f"Received 1 week of Premium!",
                f"",
                f"Adventure Hometown chest storage +25!",
                f"Daily shop min card level +1!\n"
                f"Daily shop max card level +1!",
                f"Deck slot +1!",
                f"",
                f"New Adventure Map unlocked!",
                f"",
                f"Adventure Hometown chest storage +25!",
                f"",
                f"Received 1 week of Premium!",
                f"",
                f"Deck slot +1!",
                f"Daily shop min card level +1!\n"
                f"Adventure Hometown chest storage +25!"
            ]

            # At levels 17 and 27, the user gets a week of free premium.
            if profile[3] + 1 in [17, 27]:
                dm.cur.execute(f"SELECT user_identity FROM playersinfo WHERE userid = '{a.id}'")
                u_id = int(dm.cur.fetchall()[0][0].split(',')[1])
                if u_id == 0:
                    u_id = int(times.time())
                dm.cur.execute(
                    f"UPDATE playersinfo SET user_identity = '{'1,' + str(u_id + 604800)}' WHERE userid = '{a.id}'"
                )
                dm.db.commit()

            if level_chart[profile[3] - 1]:
                level_msg.extend(level_chart[profile[3] - 1].split("\n"))

            embed = discord.Embed(
                title=f"Congratulations {a.name}!",
                description=None,
                color=discord.Color.green()
            )
            embed.add_field(
                name="You're now level " + str(profile[3] + 1) + "!",
                value=f"+{profile[3] * 50} {u.ICON['coin']} \n"
                      f"+{math.ceil((profile[3] + 1) / 5) + 1} {u.ICON['gem']} \n"
                      "```» " + "\n\n» ".join(level_msg[:]) + "```"
            )
            embed.set_thumbnail(url=a.avatar.url)
            await message.channel.send(embed=embed)

            sql = "UPDATE playersinfo " \
                  "SET exps = %s, level = level + %s, coins = coins + %s, gems = gems + %s " \
                  "WHERE userid = %s"
            value = (
                current_exp - int((profile[3] ** 2) * 40 + 60), 1, profile[3] * 50,
                math.ceil((profile[3] + 1) / 5) + 1, str(a.id)
            )
            dm.cur.execute(sql, value)
            dm.db.commit()

        quests = profile[15].split(",")
        if len(quests) > 1:
            quest_com = [
                math.floor(int(quests[x].split(".")[2]) / u.quest_index(quests[x])[0] * 100)
                for x in range(len(quests) - 1)
            ]
            for x in range(len(quests) - 1):
                if quest_com[x] >= 100:
                    quest = u.quest_index(quests[x])
                    embed = discord.Embed(
                        title=f"QUEST COMPLETE {a.name}!",
                        description=None,
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name=f"**{quest[2]} {u.quest_str_rep(quests[x].split('.')[1], quest[0])}**",
                        value=f"**+{' '.join(quest[1::2])} +{quest[4]} {u.ICON['exp']}**",
                        # " +1{u.icon['token']}**",
                        inline=False
                    )
                    embed.set_thumbnail(url=a.avatar.url)
                    await message.channel.send(embed=embed)

                    gained = [0, 0, quest[4]]  # coin, gem, exp
                    if quest[3] == u.ICON["coin"]:
                        gained[0] += int(quest[1])
                    elif quest[3] == u.ICON["gem"]:
                        gained[1] += int(quest[1])

                    quests.remove(quests[x])
                    dm.cur.execute(
                        f"UPDATE playersinfo "
                        f"SET coins = coins + {gained[0]}, gems = gems + {gained[1]}, exps = exps + {gained[2]}, "
                        f"event_token = event_token + 1, quests = '{','.join(quests)}' "
                        f"WHERE userid = {a.id}"
                    )
                    dm.db.commit()
                    break

        by_jeff = message.content == "Spawn" and str(a.id) == "344292024486330371"
        if random.randint(1, 250) == 1 or by_jeff:
            if random.randint(1, 30) == 1:
                amt = random.randint(250, 500)
            else:
                amt = random.randint(50, 100)

            spawn_msg = await message.channel.send(embed=discord.Embed(
                title=f"A bag of gold showed up out of nowhere!",
                description=f"Quick! Type `{u.PREF}collect {amt} coins` to collect them! \n"
                            f"They'll be gone in 10 minutes!",
                color=discord.Color.green()
            ))

            if by_jeff:
                await message.delete()

            try:
                rep = await self.bot.wait_for(
                    "message", timeout=600.0,
                    check=lambda m: m.content.lower().startswith(f"{u.PREF}collect {amt} coins") and
                                    m.channel == spawn_msg.channel
                )
                mention = rep.author.mention
                ra_id = rep.author.id

                dm.cur.execute("SELECT * FROM playersinfo WHERE userid = " + str(ra_id))
                profile = dm.cur.fetchall()
                if profile:
                    if random.randint(1, 100) == 1:
                        dm.cur.execute(
                            f"UPDATE playersinfo SET coins = coins + {amt}, gems = gems + 1 WHERE userid = {ra_id}"
                        )
                        msg = f"{mention}, you collected {amt} {u.ICON['coin']} **and** __1 {u.ICON['gem']}__!"
                    else:
                        dm.cur.execute(f"UPDATE playersinfo SET coins = coins + {amt} WHERE userid = {ra_id}")
                        msg = f"{mention}, you collected {amt} {u.ICON['coin']}!"
                    dm.db.commit()
                else:
                    msg = f"{mention}, you have to register in this bot first! \n" \
                          f"Type `{u.PREF}register` to register!"

                await rep.channel.send(msg)
            except asyncio.TimeoutError:
                print("No one claimed")

        # no need for bot.process bc the one in main already handled that

    @tasks.loop(seconds=10.0)
    async def background_task(self):
        global _today
        dm.cur.execute("SELECT cooldown, daily, userid, streak, user_identity, quests FROM playersinfo")
        all_cooldowns = dm.cur.fetchall()
        limit = len(all_cooldowns)
        repeats = 1
        refresh = _today != dt.date.today()

        while repeats != limit + 1:
            if all_cooldowns[repeats - 1][0] - 1 >= 0:
                dm.cur.execute(
                    "UPDATE playersinfo SET cooldown = cooldown - 1 WHERE userid = %s",
                    all_cooldowns[repeats - 1][2]
                )

            if int(all_cooldowns[repeats - 1][4].split(",")[1]) - 1 >= 0:
                if int(all_cooldowns[repeats - 1][4].split(",")[1]) - 1 - int(times.time()) == 172800:
                    try:
                        user = await self.bot.fetch_user(all_cooldowns[repeats - 1][2])
                        await user.send(
                            "Your Premium Membership is going to expire in *__2 days__*! "
                            "Contact a bot admin in the bot server to recharge your godly powers again!"
                        )
                    except:
                        print(f"UNABLE TO DM USER: {all_cooldowns[repeats - 1][2]}")

                if int(all_cooldowns[repeats - 1][4].split(",")[1]) - 1 - int(times.time()) <= 1:
                    try:
                        user = await self.bot.fetch_user(all_cooldowns[repeats - 1][2])
                        await user.send(
                            "**R.I.P.** \n"
                            "Your Premium Membership just *__EXPIRED__*!"
                            "Contact a bot admin in the bot server to reclaim your godly powers again!")
                    except:
                        print(f"UNABLE TO DM USER: {all_cooldowns[repeats - 1][2]}")

                    dm.cur.execute(
                        f"UPDATE playersinfo SET user_identity = '0,0'"
                        f"WHERE userid = {all_cooldowns[repeats - 1][2]}"
                    )

            if refresh:
                deals_cards = []
                dm.cur.execute(
                    f"select level, user_identity from playersinfo where userid = {all_cooldowns[repeats - 1][2]}")
                result = list(dm.cur.fetchall())[0]
                player_lvl = result[0]
                user_identity = result[1]
                if int(user_identity.split(",")[0]) == 0:
                    for x in range(6):
                        deals_cards.append(u.add_a_card(player_lvl, all_cooldowns[repeats - 1][2]))
                elif int(user_identity.split(",")[0]) == 1:
                    for x in range(9):
                        deals_cards.append(u.add_a_card(player_lvl, all_cooldowns[repeats - 1][2]))
                sql = "update playersinfo set deals = %s, msg_exp = 1000 where userid = %s"
                value = (",".join(deals_cards[:]), all_cooldowns[repeats - 1][2])
                dm.cur.execute(sql, value)

            repeats += 1

        dm.db.commit()
        if refresh:
            _today = dt.date.today()


async def setup(bot: commands.Bot):
    await bot.add_cog(Sys(bot))
