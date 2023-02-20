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


async def setup(bot: commands.Bot):
    await bot.add_cog(Sys(bot))
