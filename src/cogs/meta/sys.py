import random
import math
import datetime as dt
import asyncio

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context

import db
from helpers import util as u
import resources as r


def fill_quests(player: db.Player):
    max_quests = 4 + player.has_premium()
    for _ in range(max_quests - len(player.quests)):
        q_type = random.choice(list(db.QuestType))
        rwd_type = db.RewardType.COINS
        if random.randint(1, 4) == 1:
            rwd_type = db.RewardType.GEMS
        rarity = db.QuestRarity(u.randint_log(0, 3))
        db.Quest.create(player=player, quest_type=q_type, reward_type=rwd_type, rarity=rarity)


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

        if db.Player.select().where(db.Player.id == a.id).exists():
            await ctx.send("You are already registered!")
            return

        await ctx.send("*Registering...*")

        player = db.Player.create(id=a.id, premium_acc=dt.date.today() + dt.timedelta(days=14))
        deals = [u.deal_card(player.level) for _ in range(9)]
        db.Deal.insert_many(
            [{"player": player, "c_name": d["card"], "c_level": d["level"]} for d in deals]
        ).execute()
        fill_quests(player)

        deck = db.Deck.create(owner=player.id, slot=1)

        card_names = [
            "stab",
            "stab",
            "shield",
            "shield",
            "strike",
            "strike",
            "punch",
            "punch",
            "heal",
            "slash",
            "explode",
            "aim",
        ]
        for c in card_names:
            card = db.Card.create(owner=player.id, name=c, level=4)
            db.DeckCard.create(card=card.id, deck=deck.id)

        await ctx.send(
            "**FREE PREMIUM MEMBERSHIP** for 2 weeks obtained!\n"
            f"Welcome to Adventure Bot! Do `{r.PREF}tutorial` to get started!"
        )

    @tasks.loop(time=dt.time.min)
    async def fill_quests(self):
        map(fill_quests, db.Player.select())

    @commands.Cog.listener()
    async def on_command(self, ctx: Context):
        if ctx.author.bot:
            return

        if random.randint(1, 25) == 1:
            await self.spawn_coin(ctx)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: Context):
        if ctx.author.bot:
            return
        await self.check_levels(ctx)

    async def check_levels(self, ctx: Context):
        a = ctx.author
        player = db.Player.get_or_none(db.Player.id == a.id)
        if player is None:
            return

        lvl = player.level
        needed_xp = u.level_xp(lvl)
        if player.xp < needed_xp or player.level >= 30:
            return

        level_msg = []
        if (lvl + 1) % 2 == 0:
            add_hp = round(
                (r.SCALE[1] ** math.floor((lvl + 1) / 2) - r.SCALE[1] ** math.floor(lvl / 2))
                * 100
                * r.SCALE[0]
            )
            level_msg.append(f"Max health +{add_hp}!")

        # At levels 17 and 27, the user gets a week of free premium.
        if lvl + 1 in [17, 27]:
            player.premium_acc = dt.date.today() + dt.timedelta(days=7)

        if r.LEVELS[lvl - 1]:
            level_msg.extend(r.LEVELS[lvl - 1].format(r.PREF).split("\n"))

        embed = discord.Embed(
            title=f"Congratulations {a.name}!",
            description=None,
            color=discord.Color.green(),
        )

        coin_gain = lvl * 50
        gem_gain = math.ceil((lvl + 1) / 5) + 1
        embed.add_field(
            name=f"You're now level {lvl + 1}!",
            value=f"+{coin_gain} {r.ICONS['coin']} \n+{gem_gain} {r.ICONS['gem']} \n```» "
            + "\n\n» ".join(level_msg)
            + "```",
        )
        embed.set_thumbnail(url=a.avatar.url)
        await ctx.reply(embed=embed)

        player.xp -= needed_xp
        player.level += 1
        player.coins += coin_gain
        player.gems += gem_gain
        player.save()

    async def spawn_coin(self, ctx: Context):
        if random.randint(1, 30) == 1:
            lo, hi = 250, 500
        else:
            lo, hi = 50, 100
        amt = random.randint(lo, hi)

        msg = await ctx.channel.send(
            embed=discord.Embed(
                title=f"A bag of gold showed up out of nowhere!",
                description=(
                    f"Quick! Type `{r.PREF}collect {amt} coins` to collect them!\n"
                    "They'll be gone in 10 minutes!"
                ),
                color=discord.Color.green(),
            )
        )
        try:
            rep: discord.Message = await self.bot.wait_for(
                "message",
                timeout=600.0,
                check=lambda m: m.content.lower() == f"{r.PREF}collect {amt} coins",
            )
        except asyncio.TimeoutError:
            await msg.edit(content="No one claimed the bag of coins.")
            return

        give_to = rep.author.id
        claimer = db.Player.get_or_none(db.Player.id == give_to)
        if claimer is None:
            await rep.reply(f"You have to register in this bot first with `{r.PREF}register`!")
            return

        claimer.coins += amt
        if random.randint(1, 100) == 1:
            claimer.gems += 1
            msg = f"You got {amt} {r.ICONS['coin']} and a bonus {r.ICONS['gem']}!"
        else:
            msg = f"You got {amt} {r.ICONS['coin']}!"

        claimer.save()
        await rep.reply(msg)


async def setup(bot: commands.Bot):
    await bot.add_cog(Sys(bot))
