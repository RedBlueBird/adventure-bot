import math
import datetime as dt
import os
import typing as t

import discord
from discord.ext import commands

from helpers import checks
import util as u
from helpers import db_manager as dm


class Admin(commands.Cog, name="admin"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(brief="Gives users the specified items in the arguments.")
    @checks.is_registered()
    @checks.is_owner()
    async def redeem(
            self, ctx: commands.Context,
            item_type: t.Literal["card", "item"],
            name: str, level: int, target: discord.Member
    ):
        """
        Gives users the specified items in the arguments.
        :param item_type: The type of item to give
        :param name: The specific name of the item to give
        :param level: The level/amount of the card/item to give.
        :param target: Who to give the item to
        """
        mention = ctx.message.author.mention

        with open("resources/text/bot_log.txt", "a") as log:
            log.write(f">>>{ctx.message.content}\n")
            log.write(f"{ctx.message.author} on {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        item_type = item_type.lower()
        if item_type == "card":
            card_name = " ".join(name.split("_")).title()

            dm.add_user_cards([(target.id, card_name, math.floor(int(level)))])
            await ctx.reply(
                f"{target.mention}, you received a **[{u.rarity_cost(card_name)}] "
                f"{card_name} lv: {math.floor(int(level))}** from {mention}"
            )

        elif item_type == "item":
            item_name = u.items_dict(" ".join(name.split("_")))["name"]
            inventory_data = eval(dm.get_user_inventory(target.id))

            if math.floor(int(level)) > 0 and not item_name.lower() in inventory_data:
                inventory_data[item_name.lower()] = {"items": math.floor(int(level))}
            else:
                inventory_data[item_name.lower()]["items"] += math.floor(int(level))

            inv_delete = []
            for x in inventory_data:
                if not inventory_data[x]["items"] == "x":
                    if inventory_data[x]["items"] <= 0:
                        inv_delete.append(x)
            for x in inv_delete:
                del inventory_data[x]

            inv_json = str(inventory_data).replace("'", "\"")
            dm.set_user_inventory(target.id, inv_json)
            await ctx.reply(
                f"{target.mention}, you received "
                f"**[{u.items_dict(item_name)['rarity']}/"
                f"{u.items_dict(item_name)['weight']}] "
                f"{item_name}** x{math.floor(int(level))} "
                f"from {mention}"
            )

        else:
            await ctx.reply(
                f"{mention}, the correct format for this command is "
                f"`{u.PREF}redeem (card/item) (name) (level/amount) (user)`!"
            )

    @commands.hybrid_command(
        aliases=["endseason"],
        brief="Resets the PVP season and gives each player their medals."
    )
    @commands.is_owner()
    async def end_season(self, ctx: commands.Context):
        """Resets the PVP season and gives each player their medals."""
        for d in dm.get_all_userid():
            user_medal = dm.get_user_medal(d)

            earned_coins = user_medal * 5
            earned_gems = math.floor(user_medal / 100)
            if dm.has_premium(d):
                earned_coins *= 2
                earned_gems *= 2

            medals = math.ceil((user_medal - 500) / 2) + 500 if user_medal > 500 else user_medal

            msg = f"```Season Ended!``` You now have {medals} {u.ICON['medal']} (from {user_medal}) "\
                  f"\n+{earned_coins} {u.ICON['coin']}!"
            if earned_gems > 0:
                msg += f"\n + {earned_gems} {u.ICON['gem']}"

            user = await self.bot.fetch_user(d)
            await user.send(msg)
            dm.set_user_coin(d, dm.get_user_coin(d) + earned_coins)
            dm.set_user_gem(d, dm.get_user_gem(d) + earned_gems)
            dm.set_user_medal(d, medals)

        await ctx.reply("Season Ended!")

    @commands.hybrid_command(aliases=["testing"], brief="Prints some debugging info for the devs.")
    @commands.is_owner()
    async def test(self, ctx: commands.Context):
        """Prints some debugging info for the devs."""
        loading = await ctx.message.channel.send(str(ctx.message.author) + u.ICON['load'])

        def print_all(tables_name):
            dm.cur.execute(f"SELECT * FROM {tables_name}")
            result = dm.cur.fetchall()
            for r in result:
                print(r)

        print_all("cardsinfo")
        print_all("playersinfo")
        print_all("playersachivements")
        print(u.ADMINS)
        print(dm.queues)
        guilds = list(self.bot.guilds)
        print("Connected on " + str(len(self.bot.guilds)) + " guilds:")
        for x in range(len(guilds)):
            print('  ' + guilds[x - 1].name)
        folders = os.listdir("..")
        print(folders)
        """
        for guild in self.bot.guilds:
            for emoji in guild.emojis:
                print(emoji)
            for channel in guild.channels:
                try:
                    invite = await channel.create_invite()
                    await ctx.message.channel.send(invite)
                    break
                except:
                    pass
        dm.cur.execute("select id, userid, position, inventory, show_map, storage from adventuredatas")
        adventure = dm.cur.fetchall()
        dm.cur.execute("select id, userid from playersinfo")
        ids =dm.cur.fetchall()
        for x in ids:
            found = False
            for y in adventure:
                if x[1] == y[1]:
                    found = True
                    sql = "INSERT INTO adventurecopy(userid, position, inventory, show_map, storage) VALUES (%s, %s, %s, %s, %s)"
                    val = (y[1], y[2], y[3], y[4], y[5])
                    dm.cur.execute(sql, val)
                    break
            if not found:
                sql = "INSERT INTO adventurecopy(userid, position, inventory, show_map, storage) VALUES (%s, %s, %s, %s, %s)"
                val = (x[1], "home", '{}', 'true', '{}')
                dm.cur.execute(sql, val)
        dm.db.commit()
        """
        await loading.edit(content="Database printed!")

        # dm.cur.execute("select deck1,deck2,deck3,deck4,deck5,deck6 from temp2")
        # result = dm.cur.fetchall()
        # for decks in result:
        #    for count, deck in enumerate(decks):
        #        cards = [int(i) for i in deck.split(",")]
        #        if len(cards) == 1:
        #            continue
        #        for card in cards:
        #            dm.cur.execute("update temp_cards set deck" + str(count+1) + " = 1 where id = " + str(card) + ";")
        # dm.db.commit()
                         

async def setup(bot):
    await bot.add_cog(Admin(bot))
