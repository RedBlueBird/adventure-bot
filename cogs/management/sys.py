import random
import math
import datetime as dt
import asyncio

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context

from helpers import db_manager as dm
import util as u

_today = str(dt.date.today() - dt.timedelta(days=1))


class Sys(commands.Cog, name="sys"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.background_task.start()

    @commands.hybrid_command(
        name="register",
        description="Registers the author of the message.",
    )
    async def register(self, ctx: Context):
        """Registers the author of the message."""
        a = ctx.message.author

        user_cooldown = dm.get_user_cooldown(a.id)
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
        owned_user = [a.id for _ in range(12)]
        card_levels = [4 for _ in range(12)]
        dm.add_user_cards(list(zip(owned_user, card_names, card_levels)))

        dm.add_user(a.id)
        dm.set_user_coin(250, a.id)
        dm.set_user_gem(5, a.id)
        dm.set_user_premium(dt.datetime.today() + dt.timedelta(days=7), a.id)
        dm.set_user_register_date(dt.datetime.today(), a.id)
        dm.set_user_position("home", a.id)
        dm.set_user_inventory("{}", a.id)
        dm.set_user_storage("{}", a.id)

        user_cards = dm.get_user_cards(1, a.id)
        for card in user_cards:
            dm.set_user_card_deck(1, 1, card[0], a.id)

        deals_cards = []
        for _ in range(9):
            deals_cards.append(u.add_a_card(1))
        dm.set_user_deals(','.join(deals_cards), a.id)

        await ctx.send(
            "**FREE PREMIUM MEMBERSHIP** for 2 weeks obtained!\n"
            f"Welcome to Adventure Bot! Do `{u.PREF}tutorial` to get started!"
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content = message.content.lower().strip()
        if (content.startswith(f"{u.PREF}pong")
                or content.startswith(f"<@{self.bot.application_id}>")
                or content.startswith(f"<@!{self.bot.application_id}>")):
            ms = int(self.bot.latency * 1000)
            await message.channel.send(f'Pong! {ms} ms. Bot command prefix is `{u.PREF}`!')

        # region Give the user XP through messages
        a = message.author
        user_level = dm.get_user_level(a.id)
        if not user_level:
            return
        user_exp = dm.get_user_exp(a.id)
        user_msg_exp = dm.get_user_msg_exp(a.id)
        user_premium_date = dm.get_user_premium(a.id)

        if user_exp < u.level_xp(user_level) and user_level < 30 or user_level == 30:
            if user_msg_exp > 0:
                if user_premium_date > dt.datetime.today():
                    dm.set_user_exp(user_exp + 2, a.id)
                else:
                    dm.set_user_exp(user_exp + 1, a.id)
                dm.set_user_msg_exp(user_msg_exp - 1, a.id)
        else:
            level_msg = []
            if (user_level + 1) % 2 == 0:
                add_hp = round(
                    (u.SCALE[1] ** math.floor((user_level + 1) / 2) -
                     u.SCALE[1] ** math.floor(user_level / 2)) * 100 * u.SCALE[0]
                )
                level_msg.append(f"Max health +{add_hp}!")

            # At levels 17 and 27, the user gets a week of free premium.
            if user_level + 1 in [17, 27]:
                dm.set_user_premium(user_premium_date + dt.timedelta(days=7), a.id)

            if u.LEVELS[user_level - 1]:
                level_msg.extend(u.LEVELS[user_level - 1].format(u.PREF).split("\n"))

            embed = discord.Embed(
                title=f"Congratulations {a.name}!",
                description=None,
                color=discord.Color.green()
            )
            embed.add_field(
                name=f"You're now level {user_level + 1}!",
                value=f"+{user_level * 50} {u.ICON['coin']} \n"
                      f"+{math.ceil((user_level + 1) / 5) + 1} {u.ICON['gem']} \n"
                      "```» " + "\n\n» ".join(level_msg) + "```"
            )
            embed.set_thumbnail(url=a.avatar.url)
            await message.channel.send(embed=embed)

            dm.set_user_exp(user_exp - u.level_xp(user_level), a.id)
            dm.set_user_level(user_level + 1, a.id)
            dm.set_user_coin(dm.get_user_coin(a.id) + user_level * 50, a.id)
            dm.set_user_coin(dm.get_user_gem(a.id) + math.ceil((user_level + 1) / 5) + 1, a.id)
        # endregion

        # region Quest Completion Check (scuffed)
        quests = dm.get_user_quest(a.id).split(",")
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
                    dm.set_user_coin(dm.get_user_coin(a.id) + gained[0], a.id)
                    dm.set_user_gem(dm.get_user_gem(a.id) + gained[1], a.id)
                    dm.set_user_gem(dm.get_user_exp(a.id) + gained[2], a.id)
                    dm.set_user_token(dm.get_user_token(a.id) + 1, a.id)
                    dm.set_user_quest(','.join(quests), a.id)
                    break
        # endregion

        # region Gold Spawn Logic
        by_jeff = message.content.lower() == "spawn" and str(a.id) == "344292024486330371"
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

                user_coin = dm.get_user_coin(a.id)
                if user_coin:
                    dm.set_user_coin(user_coin + amt, a.id)
                    if random.randint(1, 100) == 1:
                        dm.set_user_gem(dm.get_user_gem(a.id) + 1, a.id)
                        msg = f"{mention}, you collected {amt} {u.ICON['coin']} and 1 {u.ICON['gem']} as well!"
                    else:
                        msg = f"{mention}, you collected {amt} {u.ICON['coin']}!"
                else:
                    msg = f"{mention}, you have to register in this bot first! \n" \
                          f"Type `{u.PREF}register` to register!"

                await rep.channel.send(msg)
            except asyncio.TimeoutError:
                print("No one claimed the bag of coins.")
        # endregion

        # no need for bot.process bc the one in main already handled that

    @tasks.loop(seconds=10.0)
    async def background_task(self):
        global _today
        all_uids = [int(uid[0]) for uid in dm.get_all_userid()]
        refresh = _today != dt.date.today()

        for curr_id in all_uids:
            user_cooldown = dm.get_user_cooldown(curr_id)
            if user_cooldown - 1 >= 0:
                dm.set_user_cooldown(curr_id, user_cooldown - 1)

            if refresh:
                deals_cards = []
                user_level = dm.get_user_level(curr_id)
                user_premium_date = dm.get_user_premium(curr_id)
                if user_premium_date >= dt.datetime.today():
                    for x in range(9):
                        deals_cards.append(u.add_a_card(user_level, curr_id))
                else:
                    for x in range(6):
                        deals_cards.append(u.add_a_card(user_level, curr_id))
                dm.set_user_deals(",".join(deals_cards[:]), curr_id)
                dm.set_user_msg_exp(1000, curr_id)

        if refresh:
            _today = dt.date.today()


async def setup(bot: commands.Bot):
    await bot.add_cog(Sys(bot))
