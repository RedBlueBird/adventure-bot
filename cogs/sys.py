import random
import math
import datetime as dt
import time as times

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context

from helpers import checks
from helpers import db_manager as dm
from helpers import asset_manager as am


class Sys(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

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

        sql = "INSERT INTO adventuredatas(userid, position, inventory, show_map, storage) VALUES (%s, %s, %s, %s, %s)"
        val = (author_id, "home", '{}', 'true', '{}')
        dm.cur.execute(sql, val)

        dm.db.commit()

        dm.cur.execute(f"SELECT id FROM cardsinfo WHERE owned_user = '{ctx.message.author.id}'")
        result = dm.cur.fetchall()
        ids = [str(i[0]) for i in result]
        dm.cur.execute(f"UPDATE playersachivements SET deck1 = '{','.join(ids[:])}' WHERE userid = '{ctx.message.author.id}'")

        deals_cards = []
        for _ in range(9):
            deals_cards.append(am.add_a_card(1))
        dm.cur.execute = f"UPDATE playersinfo SET deals = '{','.join(deals_cards[:])}' WHERE userid = '{ctx.message.author.id}'"

        dm.db.commit()

        await ctx.send(
            "__FREE PREMIUM MEMBERSHIP__ for 2 weeks obtained!\n"
            f"*Registered {ctx.message.author.mention} into this bot!* " +
            f"Do `{am.prefix}help` and `{am.prefix}tutorial` to get started!"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Sys(bot))
