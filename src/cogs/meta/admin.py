import json
import math
import datetime

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import resources as r, checks, db_manager as dm
import db


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.log_to = open("bot_log.txt", "a")
        print(f"Cog started on {datetime.datetime.now()}", file=self.log_to, flush=True)
        self.bot = bot

    async def cog_before_invoke(self, ctx: Context):
        msg = ctx.message.content
        insert = f"\n{msg}\n" if msg else ""
        to_print = f"{ctx.author}:{insert}{ctx.command}"
        print(to_print, file=self.log_to, flush=True)

    @commands.hybrid_group(description="Redeem something! (Admin only)")
    @checks.is_admin()
    @checks.is_registered()
    async def redeem(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            embed = (
                discord.Embed(title="Here's what you can redeem:")
                .add_field(
                    name="Cards",
                    value=f"`{r.PREF}redeem card (card name) (card level) (recipient)`",
                )
                .add_field(
                    name="Items",
                    value=f"`{r.PREF}redeem item (item name) (item amt) (recipient)`",
                )
            )
            await ctx.reply(embed=embed)

    @redeem.command()
    @checks.is_admin()
    @checks.is_registered()
    async def card(self, ctx: Context, card: str, level: int, recipient: discord.Member):
        if level <= 0:
            await ctx.reply("You can't redeem a card with a nonpositive level!")
            return

        card = r.card(card)
        db.Card.create(owner=recipient.id, name=card.name, level=level)
        await ctx.send(
            f"{recipient.mention}, you received a **[{card.rarity}/{card.cost}] "
            f"{card.name} lv: {level}** from {ctx.author.mention}!"
        )

    @redeem.command()
    @checks.is_admin()
    @checks.is_registered()
    async def item(self, ctx: Context, item: str, amt: int, recipient: discord.Member):
        if amt <= 0:
            await ctx.reply("You can't redeem a nonpositive amount of items!")
            return

        item = r.item(item.replace("_", " "))
        name = item.name
        inv = dm.get_user_inventory(recipient.id)

        if amt > 0 and name not in inv:
            inv[name] = amt
        else:
            inv[name] += amt

        inv_delete = []
        for i in inv:
            if inv[i] != "x" and inv[i] <= 0:
                inv_delete.append(i)
        for i in inv_delete:
            del inv[i]

        dm.set_user_inventory(recipient.id, json.dumps(inv))
        await ctx.reply(
            f"{recipient.mention}, you received "
            f"**[{item.rarity}/{item.weight}] "
            f"{name.title()}** x{math.floor(int(amt))} "
            f"from {ctx.author.mention}"
        )

    @commands.hybrid_command(
        aliases=["endseason"],
        description="Resets the PVP season and gives each player their medals.",
    )
    @commands.is_owner()
    async def end_season(self, ctx: Context):
        """Resets the PVP season and gives each player their medals."""
        for d in dm.get_all_uid():
            medals = dm.get_user_medal(d)

            earned_coins = medals * 5
            earned_gems = math.floor(medals / 100)
            if dm.has_premium(d):
                earned_coins *= 2
                earned_gems *= 2

            cap = 500  # "tax" medals above this limit at 50%
            new_medals = (medals - cap) // 2 + cap if medals > cap else medals

            msg = (
                "The season ended!"
                f"You now have {new_medals} {r.ICONS['medal']} (from {medals}) "
                f"\n+{earned_coins} {r.ICONS['coin']}!"
            )
            if earned_gems > 0:
                msg += f"\n + {earned_gems} {r.ICONS['gem']}"

            user = await self.bot.fetch_user(d)
            await user.send(msg)
            dm.set_user_coin(d, dm.get_user_coin(d) + earned_coins)
            dm.set_user_gem(d, dm.get_user_gem(d) + earned_gems)
            dm.set_user_medal(d, new_medals)

        await ctx.reply("Season Ended!")

    @commands.hybrid_command(description="Prints some debugging info for the devs.")
    @commands.is_owner()
    async def test(self, ctx: Context):
        """Prints some debugging info for the devs."""
        loading = await ctx.reply(r.ICONS["load"])

        def print_all(table: str) -> None:
            dm.cur.execute(f"SELECT * FROM {table}")
            result = dm.cur.fetchall()
            for i in result:
                print(i)

        print_all("temp")
        print_all("temp_cards")
        print(r.ADMINS)
        print(dm.queues)

        guilds = list(self.bot.guilds)
        print(f"Connected on {len(guilds)} guilds:")
        for g in guilds:
            print(f"\t{g.name}")

        await loading.edit(content="Database printed!")


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
