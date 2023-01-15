import math
import datetime as dt
import os

import discord
from discord.ext import commands

from helpers import checks
from helpers import asset_manager as am
from helpers import db_manager as dm


class Admin(commands.Cog, name="admin"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        aliases=["red", "deem"],
        brief="Gives users the specified items in the arguments."
    )
    @checks.is_registered()
    @checks.is_owner()
    async def redeem(self, ctx: commands.Context, item_type: str, name: str, level: int, target: discord.User):
        """
        Gives users the specified items in the arguments.
        :param item_type: The type of item to give
        :param name: The specific name of the item to give
        :param level: The level/amount of the card/item to give.
        :param target: Who to give the item to
        """
        mention = ctx.message.author.mention

        with open("txts/bot_log.txt", "a") as log:
            log.write(f">>>{ctx.message.content}\n")
            log.write(f"Sender: {ctx.message.author}, Date: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        item_type = item_type.lower()
        if "cards".startswith(item_type):
            card_name = " ".join(name.split("_")).title()
            try:
                mysql = "INSERT INTO cardsinfo (owned_user, card_name, card_level) VALUES (%s, %s, %s)"
                value = (target, card_name, math.floor(int(level)))
                dm.cur.execute(mysql, value)
                dm.db.commit()

                await ctx.message.channel.send(
                    f"{target.mention}, you received a **[{am.rarity_cost(card_name)}] "
                    f"{card_name} lv: {math.floor(int(level))}** from {mention}"
                )
            except BaseException as error:
                await ctx.message.channel.send(mention + ", " + str(error) + ".")

        elif "items".startswith(item_type):
            item_name = am.items_dict(" ".join(name.split("_")))["name"]
            dm.cur.execute(f"SELECT inventory FROM adventuredatas WHERE userid = {target.id}")
            inventory_data = eval(dm.cur.fetchall()[0][0])
            try:
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
                dm.cur.execute(
                    f"UPDATE adventuredatas SET inventory = '{inv_json}' WHERE userid = {target.id}"
                )
                dm.db.commit()
                await ctx.message.channel.send(
                    f"{target.mention}, you received "
                    f"**[{am.items_dict(item_name)['rarity']}/"
                    f"{am.items_dict(item_name)['weight']}] "
                    f"{item_name}** x{math.floor(int(level))} "
                    f"from {mention}"
                )
            except BaseException as error:
                await ctx.message.channel.send(mention + f", {error}!")

        else:
            await ctx.message.channel.send(
                f"{mention}, the correct format for this command is "
                f"`{am.PREF}redeem (card/item) (name) (level/amount) (user)`!"
            )

    @commands.hybrid_command(
        aliases=["endseason"],
        brief="Resets the PVP season and gives each player their medals."
    )
    @commands.is_owner()
    async def end_season(self, ctx: commands.Context):
        """Resets the PVP season and gives each player their medals."""
        dm.cur.execute("select userid, medals, user_identity from playersinfo")
        all_datas = dm.cur.fetchall()
        for d in all_datas:
            try:
                user = await self.bot.fetch_user(d[0])

                if int(d[2].split(",")[0]) == 0:
                    earned_coins = d[1] * 5
                    earned_gems = math.floor(d[1] / 100)
                elif int(d[2].split(",")[0]) == 1:
                    earned_coins = d[1] * 10
                    earned_gems = math.floor(d[1] / 100) * 2
                if d[1] > 500:
                    medals = math.ceil((d[1] - 500) / 2) + 500
                else:
                    medals = d[1]

                if earned_gems == 0:
                    await user.send(
                        f"```Season Ended!``` You now have {medals} {am.ICONS['medal']} (from {d[1]}) "
                        f"\n+{earned_coins} {am.ICONS['coin']}!"
                    )
                else:
                    await user.send(
                        f"```Season Ended!``` You now have {medals} medals (from {d[1]}) "
                        f"\n+{earned_coins} {am.ICONS['coin']} \n+{earned_gems} {am.ICONS['gem']}!"
                    )
                sql = "UPDATE playersinfo SET coins = coins + %s, gems = gems + %s, medals = %s WHERE userid = %s"
                data = (earned_coins, earned_gems, medals, d[0])
                dm.cur.execute(sql, data)
                dm.db.commit()
            except:
                print(all_datas.index(d))

        await ctx.message.channel.send("Season Ended!")

    @commands.hybrid_command(aliases=["testing"], brief="Prints some debugging info for the devs.")
    @commands.is_owner()
    async def test(self, ctx: commands.Context):
        """Prints some debugging info for the devs."""
        loading = await ctx.message.channel.send(str(ctx.message.author) + am.ICONS['load'])

        def print_all(tables_name):
            dm.cur.execute("select * from " + tables_name)
            result = dm.cur.fetchall()
            for r in result:
                print(r)

        print_all("cardsinfo")
        print_all("playersinfo")
        print_all("playersachivements")
        print(am.ADMINS)
        print(dm.queues)
        guilds = list(self.bot.guilds)
        print("Connected on " + str(len(self.bot.guilds)) + " guilds:")
        for x in range(len(guilds)):
            print('  ' + guilds[x - 1].name)
        folders = os.listdir(".")
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


async def setup(bot):
    await bot.add_cog(Admin(bot))
