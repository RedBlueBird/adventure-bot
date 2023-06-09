import random
import math
import datetime as dt
import asyncio

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db_manager as dm, util as u, resources as r


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

        if dm.is_registered(a.id):
            await ctx.send("You are already registered!")
            return

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
        now = dt.datetime.now(dt.datetime.utc)
        dm.set_user_premium(a.id, now + dt.timedelta(days=7))
        dm.set_user_register_date(a.id, now)
        dm.set_user_position(a.id, "home")
        dm.set_user_inventory(a.id, "{}")
        dm.set_user_storage(a.id, "{}")

        user_cards = dm.get_user_cards(a.id, 1)
        for card in user_cards:
            dm.set_user_card_deck(a.id, 1, 1, card[0])

        deals_cards = []
        for _ in range(9):
            deals_cards.append(u.deal_card(1))
        dm.set_user_deals(a.id, ",".join(deals_cards))

        await ctx.send(
            "**FREE PREMIUM MEMBERSHIP** for 2 weeks obtained!\n"
            f"Welcome to Adventure Bot! Do `{r.PREF}tutorial` to get started!"
        )

    @commands.Cog.listener()
    async def on_command(self, ctx: Context):
        if ctx.bot:
            return

        # region Check user level up
        a = ctx.author
        lvl = dm.get_user_level(a.id)
        if not lvl:
            return
        xp = dm.get_user_exp(a.id)

        if xp >= u.level_xp(lvl) and lvl < 30:
            level_msg = []
            if (lvl + 1) % 2 == 0:
                add_hp = round(
                    (r.SCALE[1] ** math.floor((lvl + 1) / 2) -
                     r.SCALE[1] ** math.floor(lvl / 2)) * 100 * r.SCALE[0]
                )
                level_msg.append(f"Max health +{add_hp}!")

            # At levels 17 and 27, the user gets a week of free premium.
            if lvl + 1 in [17, 27]:
                dm.set_user_premium(a.id, dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=7))

            if r.LEVELS[lvl - 1]:
                level_msg.extend(r.LEVELS[lvl - 1].format(r.PREF).split("\n"))

            embed = discord.Embed(
                title=f"Congratulations {a.name}!",
                description=None,
                color=discord.Color.green()
            )

            coin_gain = lvl * 50
            gem_gain = math.ceil((lvl + 1) / 5) + 1
            embed.add_field(
                name=f"You're now level {lvl + 1}!",
                value=f"+{coin_gain} {r.ICON['coin']} \n"
                      f"+{gem_gain} {r.ICON['gem']} \n"
                      "```» " + "\n\n» ".join(level_msg) + "```"
            )
            embed.set_thumbnail(url=a.avatar.url)
            await ctx.reply(embed=embed)

            dm.set_user_exp(a.id, xp - u.level_xp(lvl))
            dm.set_user_level(a.id, lvl + 1)
            dm.set_user_coin(a.id, dm.get_user_coin(a.id) + coin_gain)
            dm.set_user_coin(a.id, dm.get_user_gem(a.id) + gem_gain)
        # endregion

        # region Quest Completion Check (temporary)
        quests = dm.get_user_quests(a.id)
        for quest in quests:
            await u.update_quest(ctx, a.id, quest[1], 0)
        # endregion

        # region Gold Spawn Logic
        if random.randint(1, 25) == 1:
            if random.randint(1, 30) == 1:
                amt = random.randint(250, 500)
            else:
                amt = random.randint(50, 100)

            await ctx.channel.send(embed=discord.Embed(
                title=f"A bag of gold showed up out of nowhere!",
                description=f"Quick! Type `{r.PREF}collect {amt} coins` to collect them!\n"
                            f"They'll be gone in 10 minutes!",
                color=discord.Color.green()
            ))
            try:
                rep: discord.Message = await self.bot.wait_for(
                    "message", timeout=600.0,
                    check=lambda m: m.content.lower() == f"{r.PREF}collect {amt} coins"
                )
                user_coin = dm.get_user_coin(a.id)
                if user_coin:
                    dm.set_user_coin(a.id, user_coin + amt)
                    if random.randint(1, 100) == 1:
                        dm.set_user_gem(a.id, dm.get_user_gem(a.id) + 1)
                        msg = f"You got {amt} {r.ICON['coin']} and a bonus {r.ICON['gem']}!"
                    else:
                        msg = f"You got {amt} {r.ICON['coin']}!"
                else:
                    msg = f"You have to register in this bot first with `{r.PREF}register`!"

                await rep.reply(msg)
            except asyncio.TimeoutError:
                print("No one claimed the bag of coins.")
        # endregion


async def setup(bot: commands.Bot):
    await bot.add_cog(Sys(bot))
