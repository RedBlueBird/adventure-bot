
""""
Copyright © Krypton 2019-2022 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.4.1
"""
import random
import math
import time as times
import datetime as dt

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks
from helpers import db_manager as dm
from helpers import asset_manager as am


class StatsCmd(commands.Cog, name="informational"):
    def __init__(self, bot):
        self.bot = bot


    @commands.hybrid_command(
        name="profile",
        description="Check player's general information."
    )
    @checks.not_blacklisted()
    async def profile(self, context: Context, user: discord.User = None) -> None:
        """
        Check player's general information

        :param context: The hybrid command context.
        :param user: The user the information is obtained from
        """
        if user == None:
            user = context.message.author
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(user.id)
        
        dm.mycursor.execute(f"select * from playersinfo where userid = '{member.id}'")
        profile_info = dm.mycursor.fetchall()

        if not profile_info:
            await ctx.send(f"{ctx.message.author.mention}, that's an invalid user id!")
            return
        else:
            profile_info = profile_info[0]
            dm.mycursor.execute(f"select * from playersachivements where userid = '{member.id}'")
            achivement_info = dm.mycursor.fetchall()[0]

        if profile_info[14].split(",")[0] == "1":
            description_msg = f"14 \n{am.icon['timer']}**ᴘʀᴇᴍɪᴜᴍ**: {am.time_converter(int(profile_info[14].split(',')[1]) - int(times.time()))} \n"
            tickets = "10"
        else:
            description_msg = "7 \n"
            tickets = "5"

        tick_msg = ""
        if profile_info[3] >= 4:
            tick_msg = f"{am.icon['tick']}**Raid Tickets: **{profile_info[9]}/{tickets}"

        if str(member.id) not in am.queues:
            embed = discord.Embed(title=member.display_name + "'s profile:", description=None,
                                  color=discord.Color.gold())
        else:
            embed = discord.Embed(title=member.display_name + "'s profile:",
                                  description=f"```{am.queues[str(member.id)]}``` \n",
                                  color=discord.Color.gold())
        embed.set_thumbnail(url=member.avatar.url)

        if int(profile_info[3]) < 30:
            embed.add_field(name=f"Current Level: {profile_info[3]}",
                            value=f"{am.icon['exp']} {profile_info[4]}/{math.floor(int((profile_info[3] ** 2) * 40 + 60))} \n"
                                  f"{am.icon['hp']} {round((100 * am.scale[1] ** math.floor(profile_info[3] / 2)) * am.scale[0])}",
                            inline=False)
        else:
            embed.add_field(name=f"Max Level: {profile_info[3]}",
                            value=f"{am.icon['exp']} {profile_info[4]} \n{am.icon['hp']} {round((100 * am.scale[1] ** math.floor(profile_info[3] / 2)) * am.scale[0])}",
                            inline=False)

        if profile_info[10] != str(dt.date.today()):
            dts = "Right Now!"
        else:
            dts = cmd_tools.remain_time()
        embed.add_field(name="Currency: ", value=f"{am.icon['coin']}**Golden Coins: **{profile_info[5]} \n"
                                                 f"{am.icon['gem']}**Shiny Gems: **{profile_info[6]} \n"
                                                 f"{am.icon['token']}**Confetti: **{profile_info[7]} \n"
                                                 f"{am.icon['medal']}**Medals: **{profile_info[8]} \n"
                                                 f"{tick_msg}", inline=False)
        embed.add_field(name="Times: ",
                        value=f"{am.icon['streak']}**Current daily streak: **{int(profile_info[13])}/" +
                              description_msg + f"{am.icon['timer']}**Next daily: **{dts} \n"
                                                f"{am.icon['timer']}**Next quest: "
                                                f"**{am.time_converter(int(profile_info[15].split(',')[-1]) - int(times.time()))}",
                        inline=False)

        if achivement_info[3] != "0000000000000000000000000000000000000000":
            badges = ["beta b", "pro b", "art b", "egg b", "fbi b", "for b"]
            owned_badges = []
            for i, value in enumerate(achivement_info[3]):
                if value == "1":
                    owned_badges.append(am.icon[badges[i]])
            embed.add_field(name="Badges: ", value=" ".join(owned_badges))
        # embed.add_field(name="Personal Best: ", value="Traveled " + str(profile_info[10]) + " Meters in one Adventure.", inline=False)
        embed.set_footer(text="PlayerID: " + str(profile_info[0]) + ", RegisterDate: " + str(achivement_info[2]))
        await context.send(embed=embed)


async def setup(bot):
    await bot.add_cog(StatsCmd(bot))
