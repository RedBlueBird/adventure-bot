import random
import math
import datetime as dt
import time as times
import asyncio

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context

from helpers import checks
from helpers import db_manager as dm
from helpers import asset_manager as am

_today = str(dt.date.today() - dt.timedelta(days=1))


class Sys(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.background_task.start()

    @commands.hybrid_command(
        name="register",
        description="Registers the author of the bot.",
    )
    @checks.not_blacklisted()
    async def register(self, ctx: Context):
        """Registers the author of the bot."""
        author_id = str(ctx.message.author.id)

        dm.cur.execute(f"SELECT cooldown FROM playersinfo WHERE userid = {author_id}")
        result = dm.cur.fetchall()
        if result:
            if result[0][0] == 0:
                await ctx.send(f"{ctx.message.author.mention}, you're already registered in this bot!")
            else:
                await ctx.send(
                    "You have to wait " +
                    am.time_converter(result[0][0]) +
                    " before you can send another command!"
                )
            return

        await ctx.send(f"*registering {ctx.message.author.mention}...*")
        sql = "INSERT INTO cardsinfo (owned_user, card_name, card_level) VALUES (%s, %s, %s)"

        starter_cards = [
            "Stab", "Stab", "Shield", "Shield", "Strike", "Strike",
            "Punch", "Punch", "Heal", "Slash", "Explode", "Aim"
        ]
        val = [(author_id, c, 4) for c in starter_cards]
        dm.cur.executemany(sql, val)

        sql = "INSERT INTO playersinfo (userid, coins, gems, user_identity) VALUES (%s, %s, %s, %s)"
        val = (author_id, 250, 5, f"1,{1209600 + int(times.time())}")
        dm.cur.execute(sql, val)

        sql = "INSERT INTO playersachivements (userid, register_date, badges) VALUES (%s, %s, %s)"
        val = (author_id, str(dt.date.today()), "1000000000000000000000000000000000000000")
        dm.cur.execute(sql, val)

        sql = "INSERT INTO adventuredatas (userid, position, inventory, show_map, storage) VALUES (%s, %s, %s, %s, %s)"
        val = (author_id, "home", "{}", "true", "{}")
        dm.cur.execute(sql, val)

        dm.db.commit()

        dm.cur.execute(f"SELECT id FROM cardsinfo WHERE owned_user = '{author_id}'")
        result = dm.cur.fetchall()
        ids = [str(i[0]) for i in result]
        dm.cur.execute(f"UPDATE playersachivements SET deck1 = '{','.join(ids)}' WHERE userid = '{author_id}'")

        deals_cards = []
        for _ in range(9):
            deals_cards.append(am.add_a_card(1))
        dm.cur.execute(f"UPDATE playersinfo SET deals = '{','.join(deals_cards)}' WHERE userid = '{author_id}'")

        dm.db.commit()

        await ctx.send(
            "__FREE PREMIUM MEMBERSHIP__ for 2 weeks obtained!\n"
            f"*Registered {ctx.message.author.mention} into this bot!* "
            f"Do `{am.prefix}help` and `{am.prefix}tutorial` to get started!"
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content = message.content.lower()
        if (content.startswith(f"{am.prefix}ping")
                or content.startswith(f"{am.prefix}pong")
                or content.startswith("<@521056196380065802>")
                or content.startswith("<@!521056196380065802>")):
            ms = int(self.bot.latency * 1000)
            await message.channel.send(f'Pong! {ms} ms. Bot command prefix is `{am.prefix}`!')

        a = message.author  # shorthand
        dm.cur.execute("select * from playersinfo where userid = " + str(a.id))
        profile = dm.cur.fetchall()

        if not profile:
            return

        profile = profile[0]
        current_exp = profile[4]

        if (current_exp < math.floor(int((profile[3] ** 2) * 40 + 60)) and
                int(profile[3]) < 30 or int(profile[3]) == 30):
            if profile[16] > 0:
                sql = "update playersinfo set exps = %s, msg_exp = msg_exp - 1 where userid = %s"
                value = (current_exp + 1 + int(profile[14].split(",")[0]), str(a.id))
                dm.cur.execute(sql, value)
                dm.db.commit()
        else:
            level_msg = []
            if (profile[3] + 1) % 2 == 0:
                add_hp = round(
                    (am.scale[1] ** math.floor((profile[3] + 1) / 2) -
                     am.scale[1] ** math.floor(profile[3] / 2)) * 100 * am.scale[0]
                )
                level_msg.append(f"Max health +{add_hp}!")

            """
            Each element of this list corresponds to what will be unlocked when a player levels up.
            The first element is when level 2 is reached, and then it increments by 1 so on.
            Empty strings signify that no particular special thing is unlocked.
            """
            level_chart = [
                f"{am.prefix}Quest is unlocked!",
                f"{am.prefix}Shop is unlocked!",
                f"{am.prefix}Coop is unlocked! \n"
                f"Daily shop max card level +1!",
                f"{am.prefix}Battle for PvP is unlocked!",
                f"Deck slot +1!",
                f"{am.prefix}Trade is unlocked! \n"
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
                value=f"+{profile[3] * 50} {am.icon['coin']} \n"
                      f"+{math.ceil((profile[3] + 1) / 5) + 1} {am.icon['gem']} \n"
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
                math.floor(int(quests[x].split(".")[2]) / am.quest_index(quests[x])[0] * 100)
                for x in range(len(quests) - 1)
            ]
            for x in range(len(quests) - 1):
                if quest_com[x] >= 100:
                    quest = am.quest_index(quests[x])
                    embed = discord.Embed(
                        title=f"QUEST COMPLETE {a.name}!",
                        description=None,
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name=f"**{quest[2]} {am.quest_str_rep(quests[x].split('.')[1], quest[0])}**",
                        value=f"**+{' '.join(quest[1::2])} +{quest[4]} {am.icon['exp']}**",
                        # " +1{am.icon['token']}**",
                        inline=False
                    )
                    embed.set_thumbnail(url=a.avatar.url)
                    await message.channel.send(embed=embed)

                    gained = [0, 0, quest[4]]  # coin, gem, exp
                    if quest[3] == am.icon["coin"]:
                        gained[0] += int(quest[1])
                    elif quest[3] == am.icon["gem"]:
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
                description=f"Quick! Type `{am.prefix}collect {amt} coins` to collect them! \n"
                            f"They'll be gone in 10 minutes!",
                color=discord.Color.green()
            ))

            if by_jeff:
                await message.delete()

            try:
                rep = await self.bot.wait_for(
                    "message", timeout=600.0,
                    check=lambda m: m.content.lower().startswith(f"{am.prefix}collect {amt} coins") and
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
                        msg = f"{mention}, you collected {amt} {am.icon['coin']} **and** __1 {am.icon['gem']}__!"
                    else:
                        dm.cur.execute(f"UPDATE playersinfo SET coins = coins + {amt} WHERE userid = {ra_id}")
                        msg = f"{mention}, you collected {amt} {am.icon['coin']}!"
                    dm.db.commit()
                else:
                    msg = f"{mention}, you have to register in this bot first! \n" \
                          f"Type `{am.prefix}register` to register!"

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
                        deals_cards.append(am.add_a_card(player_lvl, all_cooldowns[repeats - 1][2]))
                elif int(user_identity.split(",")[0]) == 1:
                    for x in range(9):
                        deals_cards.append(am.add_a_card(player_lvl, all_cooldowns[repeats - 1][2]))
                sql = "update playersinfo set deals = %s, msg_exp = 1000 where userid = %s"
                value = (",".join(deals_cards[:]), all_cooldowns[repeats - 1][2])
                dm.cur.execute(sql, value)

            repeats += 1

        dm.db.commit()
        if refresh:
            _today = dt.date.today()


async def setup(bot: commands.Bot):
    await bot.add_cog(Sys(bot))
