import random
import math
import datetime as dt
import asyncio
import io
from copy import deepcopy
import typing as t

from PIL import Image, ImageFont, ImageDraw
import discord
from discord.ext import commands

from helpers import db_manager as dm
import util as u
from helpers import checks


class Fun(commands.Cog, name="fun"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["black", "bj"], brief="Practice your blackjack skills!")
    @checks.not_preoccupied("practicing blackjack")
    async def blackjack(self, ctx):
        """Practice your blackjack skills!"""

        a_id = ctx.author.id
        mention = ctx.author.mention

        deck = deepcopy(u.DECK)
        aces = deepcopy(u.ACES)
        values = [0, 0]
        cards = [[], []]
        included_aces = [[], []]
        end = False

        def add_card(card, target):
            if target == "self":
                values[0] += deck[card]
                cards[0].append(card)
            else:
                values[1] += deck[card]
                cards[1].append(card)
            del deck[card]

        add_card(random.choice(list(deck)), "self")
        add_card(random.choice(list(deck)), "self")
        add_card(random.choice(list(deck)), "opponent")

        hit = ["hit", "h"]
        stand = ["stand", "s"]
        while not end and values[0] < 21:
            await ctx.send(
                f"{mention} \nYour total: {values[0]} \n{' '.join(cards[0])}"
                f" \n------------------------------ \nDealer's total: {values[1]} + ? \n"
                f"{' '.join(cards[1])} [? ? ?] ```\n{u.PREF}hit -draw a card \n"
                f"{u.PREF}stand -end your turn```"
            )
            try:
                msg_reply = await self.bot.wait_for(
                    "message", timeout=30.0,
                    check=checks.valid_reply(hit + stand, ctx.author, ctx.message.channel)
                )
            except asyncio.TimeoutError:
                values = [1000, 1000]
                await ctx.send(f"{mention}, you blanked out and lost the game!")
                return
            else:
                action = msg_reply.content[len(u.PREF):].lower()
                if action in stand:
                    end = True
                    add_card(random.choice(list(deck)), "opponent")
                    while values[1] < 17:
                        add_card(random.choice(list(deck)), "opponent")
                        while values[1] > 21 and any(a in cards[1] and a not in included_aces[1] for a in aces):
                            for x in cards[1]:
                                if x in aces and x not in included_aces[1]:
                                    values[1] -= 10
                                    included_aces[1].append(x)
                                    break

                elif action in hit:
                    add_card(random.choice(list(deck)), "self")
                    while values[0] > 21 and any(a in cards[0] and a not in included_aces[0] for a in aces):
                        for x in cards[0]:
                            if x in aces and x not in included_aces[0]:
                                values[0] -= 10
                                included_aces[0].append(x)
                                break

        if len(cards[1]) == 1 and not values == [1000, 1000]:
            add_card(random.choice(list(deck)), "opponent")

        if values[0] == values[1] and values != [1000, 1000]:
            game_state = "tied"
        elif (values[0] > 21 and values[0] > values[1]) or (values[0] < values[1] < 22):
            game_state = "lost"
        elif (22 > values[0] > values[1]) or (values[1] > 21 and values[0] < values[1]):
            game_state = "won"

        await ctx.send(
            f"{mention}, **You {game_state}!** \nYour total: {values[0]} \n{''.join(cards[0])}"
            f" \n------------------------------ \nDealer's total: {values[1]} \n{''.join(cards[1])}"
        )

    @commands.hybrid_command(brief="Test your reflexes and counting ability!")
    @checks.not_preoccupied("testing timing accuracy")
    async def reaction(self, ctx: commands.Context, wait_time: float = -1.0):
        """Test your reflexes AND counting ability!"""
        mention = ctx.author.mention

        if wait_time <= 0:
            wait_time = random.randint(6, 30)

        t = await ctx.send(f"{mention}, reply `{u.PREF}` as close as you can to {wait_time} seconds!")
        try:
            message = await self.bot.wait_for(
                "message", timeout=70,
                check=checks.valid_reply("", ctx.author, ctx.message.channel)
            )
        except asyncio.TimeoutError:
            await ctx.send(f"{mention}, time's up!")
        else:
            recorded = (message.created_at - t.created_at).total_seconds()
            off = round(abs(wait_time - recorded) * 1000) / 1000
            await ctx.send(
                f"{mention}, you replied in {recorded} seconds, which "
                f"is {off} seconds off from {wait_time} seconds"
            )

    @commands.hybrid_command(brief="Have Crispy agree with anything!")
    async def agree(self, ctx: commands.Context, statement: str = "but u said u are stupid"):
        """Have Crispy agree with anything!"""
        img = Image.open("resources/img/crispy_reply.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("resources/fonts/whitneysemibold.ttf", 24)
        draw.text((323, 82), statement, (170, 172, 171), font=font)
        with io.BytesIO() as out:
            img.save(out, format="png")
            out.seek(0)
            await ctx.send(file=discord.File(fp=out, filename="crispy_reply.png"))

    @commands.hybrid_command(brief="Mock the bot's creator.")
    async def birb(self, ctx: commands.Context, stuff: str = "1 + 1 = 3"):
        """Mock the bot's creator."""
        img = Image.open("resources/img/birb_logic.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("resources/fonts/whitneysemibold.ttf", 12)
        draw.text((64, 28), stuff, (200, 200, 200), font=font)
        with io.BytesIO() as out:
            img.save(out, format="png")
            out.seek(0)
            await ctx.send(file=discord.File(fp=out, filename="birb_logic.png"))

    @commands.hybrid_command(brief="This is fine.")
    async def dead(self, ctx: commands.Context, msg: str = "Should I be scared?"):
        """Kind of like the 'this is fine' meme, except you can make the dog say whatever you want."""
        img = Image.open("resources/img/pandemic.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("resources/fonts/whitneysemibold.ttf", 14)
        draw.text((62, 290), msg, (200, 200, 200), font=font)
        with io.BytesIO() as out:
            img.save(out, format="png")
            out.seek(0)
            await ctx.send(file=discord.File(fp=out, filename="pandemic.png"))

    @commands.hybrid_command(brief="An Adventure Bot themed meme template.")
    async def kick_meme(
            self, ctx: commands.Context,
            kickee: str = "Me duelling someone", kicker: str = "RNG"
    ):
        """A adventurers themed meme generator."""
        img = Image.open("resources/img/meme_template.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("resources/fonts/whitneysemibold.ttf", 17)
        draw.text((80, 25), kickee, (256, 256, 256), font=font)
        draw.text((330, 25), kicker, (256, 256, 256), font=font)
        with io.BytesIO() as out:
            img.save(out, format="png")
            out.seek(0)
            await ctx.send(file=discord.File(fp=out, filename="kick.png"))

    @commands.hybrid_command(aliases=["find_words", "findwords", "fw"], brief="Finds words with given letters.")
    async def find_word(self, ctx: commands.Context, letters: str, limit: int = 5):
        """Finds words with given letters."""
        with open("resources/text/search.txt") as file:
            valid_words = []
            for line in file:
                if limit == 0:
                    break
                if letters in line:
                    valid_words.append(line)
                    limit -= 1

        if valid_words:
            await ctx.send(f"Words found: \n{''.join(valid_words)}")
        else:
            await ctx.send("No words found! :frown:")


async def setup(bot):
    await bot.add_cog(Fun(bot))
