import discord

import db
import resources as r
from helpers import util as u

PACKS = [
    {
        "name": "**Basic Pack**",
        "value": f"Cost: **3** {r.ICONS['gem']}\n• contains 3 (lv 4-10) cards\n`{r.PREF}buy basic`",
    },
    {
        "name": "**Fire Pack**",
        "value": (
            f"Cost: **5** {r.ICONS['gem']}\n"
            "• contains 4 (lv 4-10) cards with a\nhigher chance of fire cards\n"
            f"`{r.PREF}buy fire`"
        ),
    },
    {
        "name": "**Evil Pack**",
        "value": (
            f"Cost: **5** {r.ICONS['gem']}\n"
            "• contains 4 (lv 4-10) cards with a\nhigher chance of curse cards\n"
            f"`{r.PREF}buy evil`"
        ),
    },
    {
        "name": "**Electric Pack**",
        "value": (
            f"Cost: **5** {r.ICONS['gem']}\n"
            "• contains 4 (lv 4-10) cards with a\nhigher chance of electric cards\n"
            f"`{r.PREF}buy electric`"
        ),
    },
    {
        "name": "**Defensive Pack**",
        "value": (
            f"Cost: **5** {r.ICONS['gem']}\n"
            "• contains 4 (lv 4-10) cards with a\nhigher chance of defense cards\n"
            f"`{r.PREF}buy defensive`"
        ),
    },
    {
        "name": "**Pro Pack**",
        "value": f"Cost: **24** {r.ICONS['gem']}\n• contains 6 (lv 7-10) cards\n`{r.PREF}buy pro`",
    },
    # {
    #     "name": "**Anniversary Pack**",
    #     "value": f"Cost: **40** {r.ICONS['token']}\n"
    #              "• contains **[EX/7] Confetti Cannon**\n"
    #              f"`{r.PREFix}buy confetti`"
    # }
]

CURRENCY = [
    {
        "name": "**1000 Golden Coins**",
        "value": f"Cost: **3** {r.ICONS['gem']}\n`{r.PREF}buy coins gc1`",
    },
    {
        "name": "**2250 Golden Coins**",
        "value": f"Cost: **6** {r.ICONS['gem']}\n`{r.PREF}buy coins gc2`",
    },
    {
        "name": "**11000 Golden Coins**",
        "value": f"Cost: **24** {r.ICONS['gem']}\n`{r.PREF}buy coins gc3`",
    },
    {
        "name": "**1 Raid Ticket**",
        "value": f"Cost: **2** {r.ICONS['gem']}\n`{r.PREF}buy tickets rt1`",
    },
    {
        "name": "**2 Raid Tickets**",
        "value": f"Cost: **4** {r.ICONS['gem']}\n`{r.PREF}buy tickets rt2`",
    },
    {
        "name": "**3 Raid Tickets**",
        "value": f"Cost: **6** {r.ICONS['gem']}\n`{r.PREF}buy tickets rt3`",
    },
]


class Shop(discord.ui.View):
    def __init__(self, uid: int):
        super().__init__()
        self.id = uid
        self.player = db.Player.get_by_id(uid)

    @discord.ui.button(label="Daily Deals", style=discord.ButtonStyle.blurple)
    async def daily_deals(self, i: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Shop - Daily Deals:",
            description=(
                f"{r.ICONS['coin']} **{self.player.coins}** {r.ICONS['gem']} **{self.player.gems}**"
            ),
            color=discord.Color.gold(),
        )

        for v, d in enumerate(self.player.deals):
            card = r.card(d.c_name)
            if d.sold:
                embed.add_field(name=f"**{card} lv: {d.c_level}**", value="Sold out")
            else:
                cost = round(1.6**d.c_level * 50 * u.price_factor(card.id))
                embed.add_field(
                    name=f"**{card} lv: {d.c_level}**",
                    value=f"Cost: **{cost}** {r.ICONS['coin']}\n`{r.PREF}buy card {v + 1}`",
                )

        embed.set_footer(
            text=f"Wait {u.time_til_midnight()} or do `{r.PREF}buy r` to refresh the shop"
        )

        await i.response.edit_message(embed=embed)

    @discord.ui.button(label="Card Packs", style=discord.ButtonStyle.blurple)
    async def card_packs(self, i: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Shop - Card Packs:",
            description=(
                f"{r.ICONS['coin']} **{self.player.coins}** "
                f"{r.ICONS['gem']} **{self.player.gems}** "
                f"{r.ICONS['token']} **{self.player.event_tokens}**"
            ),
            color=discord.Color.green(),
        )

        for p in PACKS:
            embed.add_field(**p)
        embed.set_footer(text="Let the buyer beware")

        await i.response.edit_message(embed=embed)

    @discord.ui.button(label="Coins & Raid Tickets", style=discord.ButtonStyle.blurple)
    async def currency(self, i: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Shop - Currencies:",
            description=(
                f"{r.ICONS['coin']} **{self.player.coins}** {r.ICONS['gem']} **{self.player.gems}**"
            ),
            color=discord.Color.green(),
        )
        for field in CURRENCY:
            embed.add_field(**field)

        await i.response.edit_message(embed=embed)
