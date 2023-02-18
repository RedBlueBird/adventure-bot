import random
import math
import datetime as dt
import asyncio

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db_manager as dm
import util as u


class Sys(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="register",
        description="Registers the author of the message.",
    )
    async def register(self, ctx: Context):
        """Registers the author of the message."""
        a = ctx.author

        await ctx.send(f"*registering {ctx.author.mention}...*")

        card_names = [
            "Stab", "Stab", "Shield", "Shield", "Strike", "Strike",
            "Punch", "Punch", "Heal", "Slash", "Explode", "Aim"
        ]
        owned_user = [a.id for _ in range(len(card_names))]
        card_levels = [4 for _ in range(len(card_names))]
        dm.add_user_cards(list(zip(owned_user, card_names, card_levels)))

        dm.add_user(a.id)
        dm.set_user_coin(a.id, 250)
        dm.set_user_gem(a.id, 5)
        dm.set_user_premium(a.id, dt.datetime.today() + dt.timedelta(days=7))
        dm.set_user_register_date(a.id, dt.datetime.today())
        dm.set_user_position(a.id, "home")
        dm.set_user_inventory(a.id, "{}")
        dm.set_user_storage(a.id, "{}")

        user_cards = dm.get_user_cards(a.id, 1)
        for card in user_cards:
            dm.set_user_card_deck(a.id, 1, 1, card[0])

        deals_cards = []
        for _ in range(9):
            deals_cards.append(u.add_a_card(1))
        dm.set_user_deals(a.id, ','.join(deals_cards))

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

        if not dm.is_registered(message.author.id):
            return

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
                inc_amt = 2 if user_premium_date > dt.datetime.today() else 1
                dm.set_user_exp(a.id, user_exp + inc_amt)
                dm.set_user_msg_exp(a.id, user_msg_exp - 1)
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
                dm.set_user_premium(a.id, user_premium_date + dt.timedelta(days=7))

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

            dm.set_user_exp(a.id, user_exp - u.level_xp(user_level))
            dm.set_user_level(a.id, user_level + 1)
            dm.set_user_coin(a.id, dm.get_user_coin(a.id) + user_level * 50)
            dm.set_user_coin(a.id, dm.get_user_gem(a.id) + math.ceil((user_level + 1) / 5) + 1)
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
                    dm.set_user_coin(a.id, dm.get_user_coin(a.id) + gained[0])
                    dm.set_user_gem(a.id, dm.get_user_gem(a.id) + gained[1])
                    dm.set_user_gem(a.id, dm.get_user_exp(a.id) + gained[2])
                    dm.set_user_token(a.id, dm.get_user_token(a.id) + 1)
                    dm.set_user_quest(a.id, ','.join(quests))
                    break
        # endregion

        # region Gold Spawn Logic
        by_jeff = message.content.lower() == "spawn" and a.id == 344292024486330371
        if random.randint(1, 250) == 0 or by_jeff:
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
                    check=lambda m:
                    m.content.lower().startswith(f"{u.PREF}collect {amt} coins") and
                    m.channel == spawn_msg.channel
                )
                mention = rep.author.mention

                user_coin = dm.get_user_coin(a.id)
                if user_coin:
                    dm.set_user_coin(a.id, user_coin + amt)
                    if random.randint(1, 100) == 1:
                        dm.set_user_gem(a.id, dm.get_user_gem(a.id) + 1)
                        msg = f"{mention}, you got {amt} {u.ICON['coin']} and 1 {u.ICON['gem']} as well!"
                    else:
                        msg = f"{mention}, you got {amt} {u.ICON['coin']}!"
                else:
                    msg = f"{mention}, you have to register in this bot first with `{u.PREF}register`! \n"

                await rep.channel.send(msg)
            except asyncio.TimeoutError:
                print("No one claimed the bag of coins.")
        # endregion

        # no need for bot.process bc the one in main already handled that


async def setup(bot: commands.Bot):
    await bot.add_cog(Sys(bot))
