import random
import json
import datetime as dt

import discord
import discord.ui as ui

from helpers import db_manager as dm
from ..adventure_template import AdventureTemplate

BAIT_COST = 50

with open("resources/text/fish.json") as read:
    FISH = json.load(read)
RARITIES = list(FISH.keys())
RARITY_PROBS = [FISH[f]["chance"] for f in FISH]


class BaitButton(ui.Button["Fishing"]):
    def __init__(self, user: discord.Member):
        super().__init__(label="Reel it in!", style=discord.ButtonStyle.green)
        self.user = user

    async def callback(self, i: discord.Interaction):
        assert self.view is not None


class Bait(ui.View):
    def __init__(self, user: discord.Member, rarity: str, wait: int):
        super().__init__()
        self.user = user
        self.rarity = rarity
        self.wait_time = wait

    @ui.button(label="Reel it in!", style=discord.ButtonStyle.green)
    async def reel(self, i: discord.Interaction, button: ui.Button):
        time = abs(dt.datetime.now().timestamp() - i.message.created_at.timestamp())
        diff = abs(time - self.wait_time)

        success_rate = 0
        if diff < 0.05:
            success_rate = 100
        elif diff < 0.125:
            success_rate = 80
        elif diff < 0.25:
            success_rate = 60
        elif diff < 0.5:
            success_rate = 40
        elif diff < 0.75:
            success_rate = 20
        elif diff < 1:
            success_rate = 10

        descr = f"You reeled the rod in in {round(time, 2)} seconds," \
                f"which is {round(diff, 2)} seconds off from {self.wait_time} seconds.\n"
        if random.randint(1, 100) <= success_rate:
            coin_rwd = 100 * FISH[self.rarity]["rwd_bonus"] - BAIT_COST
            xp_rwd = 5
            title = "Hooray!"
            descr += f"You caught a {random.choice(FISH[self.rarity]['fish'])}, " \
                     f"getting {coin_rwd} coins and {xp_rwd} XP!"
            color = discord.Color.green()
        else:
            coin_rwd = -BAIT_COST
            xp_rwd = 2
            title = "Aww..."
            descr += f"The fish got away and you wasted {BAIT_COST} coins on the bait...\n" \
                     f"Well, at least you gained {xp_rwd} XP!"
            color = discord.Color.red()

        uid = self.user.id
        dm.set_user_coin(uid, dm.get_user_coin(uid) + coin_rwd)
        dm.set_user_exp(uid, dm.get_user_exp(uid) + xp_rwd)

        delay = 10
        embed = discord.Embed(title=title, description=descr, color=color)
        embed.set_footer(text=f"This message will be deleted in {delay} seconds.")
        await i.response.edit_message(embed=embed, view=None)
        await i.message.delete(delay=delay)
        self.stop()


class Fishing(AdventureTemplate):
    @ui.button(label="Start fishing!", style=discord.ButtonStyle.blurple)
    async def bait(self, i: discord.Interaction, button: ui.Button):
        coins = dm.get_user_coin(self.user.id)
        if coins < BAIT_COST:
            await i.response.send_message(
                f"You need at least {BAIT_COST} to buy bait!",
                ephemeral=True
            )
            return

        rarity = random.choices(RARITIES, RARITY_PROBS)[0]
        wait = FISH[rarity]["base_wait"] + random.randint(1, 8)

        embed = discord.Embed(
            title=f"You saw a {rarity} fish!",
            description=f"Try to click the button in exactly {wait} seconds!",
            color=discord.Color.blurple()
        )

        view = Bait(self.user, rarity, wait)
        await i.response.send_message(
            embed=embed,
            view=view
        )

        button.disabled = True
        await i.message.edit(view=self)

        await view.wait()
        button.disabled = False
        await i.message.edit(view=self)
