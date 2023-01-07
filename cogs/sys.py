import random
import math
import datetime as dt
import time as times

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
        val = (author_id, "home", '{}', 'true', '{}')
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
            f"*Registered {ctx.message.author.mention} into this bot!* " +
            f"Do `{am.prefix}help` and `{am.prefix}tutorial` to get started!"
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
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
