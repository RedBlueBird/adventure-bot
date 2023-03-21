import random
import asyncio
import io

from PIL import Image, ImageFont, ImageDraw
import discord
from discord.ext import commands

from helpers import resources as r, checks


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(description="Test your reflexes and counting ability!")
    @checks.not_preoccupied("testing timing accuracy")
    async def reaction(self, ctx: commands.Context, wait_time: float = -1.0):
        """Test your reflexes and counting ability!"""
        if wait_time <= 0:
            wait_time = random.randint(6, 30)

        t = await ctx.reply(f"Reply `{r.PREF}` as close as you can to {wait_time} seconds!")
        try:
            message = await self.bot.wait_for(
                "message", timeout=70,
                check=checks.valid_reply("", ctx.author, ctx.message.channel)
            )
        except asyncio.TimeoutError:
            await ctx.reply(f"Time's up!")
        else:
            recorded = (message.created_at - t.created_at).total_seconds()
            off = round(abs(wait_time - recorded) * 1000) / 1000
            await ctx.reply(
                f"You replied in {recorded} seconds, which "
                f"is {off} seconds off from {wait_time} seconds"
            )

    @commands.hybrid_command(description="Have Crispy agree with anything!")
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

    @commands.hybrid_command(description="Mock the bot's creator.")
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

    @commands.hybrid_command(description="This is fine.")
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

    @commands.hybrid_command(description="An Adventure Bot themed meme template.")
    async def kick_meme(
            self, ctx: commands.Context,
            kickee: str = "Me dueling someone", kicker: str = "RNG"
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


async def setup(bot):
    await bot.add_cog(Fun(bot))
