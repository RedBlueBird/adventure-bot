import logging
import math

import discord
from discord.ext import commands
from discord.ext.commands import Context

import db
import resources as r
from helpers import checks


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
        if not db.Player.select().where(db.Player.id == recipient.id).exists():
            await ctx.reply(f"{recipient.mention} isn't registered in the bot yet!")

        if level <= 0:
            await ctx.reply("You can't redeem a card with a nonpositive level!")
            return

        card = r.card(card)
        if card is None:
            await ctx.reply("That card doesn't exist!")
            return

        db.Card.create(owner=recipient.id, name=card.id, level=level)
        logging.info(f"{ctx.author} gave a {card} lv: {level} to {recipient}")
        await ctx.send(
            f"{recipient.mention}, you received a {card} lv: {level} from {ctx.author.mention}!"
        )

    @redeem.command()
    @checks.is_admin()
    @checks.is_registered()
    async def item(self, ctx: Context, item: str, amt: int, recipient: discord.Member):
        if not db.Player.select().where(db.Player.id == recipient.id).exists():
            await ctx.reply(f"{recipient.mention} isn't registered in the bot yet!")

        if amt <= 0:
            await ctx.reply("You can't redeem a nonpositive amount of items!")
            return

        item = r.item(item)
        if item is None:
            await ctx.reply("That item doesn't exist!")
            return

        player = db.Player.get_by_id(recipient.id)
        inv = player.inventory
        if item.id not in inv:
            inv[item.id] = 0
        inv[item.id] += amt
        player.save()

        logging.info(f"{ctx.author} gave {item} x{amt} to {recipient}")
        await ctx.reply(
            f"{recipient.mention}, you received **{item}** x{amt} from {ctx.author.mention}!"
        )

    @commands.hybrid_command(
        aliases=["endseason"],
        description="Resets the PVP season and gives each player their medals. (Admin only)",
    )
    @commands.is_owner()
    async def end_season(self, ctx: Context):
        """Resets the PVP season and gives each player their medals."""
        for p in db.Player.select():
            earned_coins = p.medals * 5
            earned_gems = math.floor(p.medals / 100)
            if p.has_premium():
                earned_coins *= 2
                earned_gems *= 2

            cap = 500  # "tax" medals above this limit at 50%
            new_medals = (p.medals - cap) // 2 + cap if p.medals > cap else p.medals

            msg = (
                "The season ended!You now have"
                f" {new_medals} {r.ICONS['medal']} (initially {p.medals})"
                f" \n+{earned_coins} {r.ICONS['coin']}!"
            )
            if earned_gems > 0:
                msg += f"\n+{earned_gems} {r.ICONS['gem']}"

            user = await self.bot.fetch_user(p.id)
            await user.send(msg)

            p.coins += earned_coins
            p.gems += earned_gems
            p.medals = new_medals
            p.save()

        logging.info(f"{ctx.author} ended the season")
        await ctx.reply("Season Ended!")


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
