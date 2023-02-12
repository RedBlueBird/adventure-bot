import discord

from helpers import db_manager as dm
import util as u

PACKS = [
    {
        "name": "**Basic Pack**",
        "value": f"Cost: **3** {u.ICON['gem']}\n"
                    "• contains 3 (lv 4-10) cards\n"
                    f"`{u.PREF}buy basic`"
    },
    {
        "name": "**Fire Pack**",
        "value": f"Cost: **5** {u.ICON['gem']}\n"
                    "• contains 4 (lv 4-10) cards with a\nhigher chance of fire cards\n"
                    f"`{u.PREF}buy fire`"
    },
    {
        "name": "**Evil Pack**",
        "value": f"Cost: **5** {u.ICON['gem']}\n"
                    "• contains 4 (lv 4-10) cards with a\nhigher chance of curse cards\n"
                    f"`{u.PREF}buy evil`"
    },
    {
        "name": "**Electric Pack**",
        "value": f"Cost: **5** {u.ICON['gem']}\n"
                    "• contains 4 (lv 4-10) cards with a\nhigher chance of electric cards\n"
                    f"`{u.PREF}buy electric`"
    },
    {
        "name": "**Defensive Pack**",
        "value": f"Cost: **5** {u.ICON['gem']}\n"
                    "• contains 4 (lv 4-10) cards with a\nhigher chance of defense cards\n"
                    f"`{u.PREF}buy defensive`"
    },
    {
        "name": "**Pro Pack**",
        "value": f"Cost: **24** {u.ICON['gem']}\n"
                    "• contains 6 (lv 7-10) cards\n"
                    f"`{u.PREF}buy pro`"
    },
    # {
    #     "name": "**Anniversary Pack**",
    #     "value": f"Cost: **40** {u.icon['token']}\n"
    #              "• contains **[EX/7] Confetti Cannon**\n"
    #              f"`{u.prefix}buy confetti`"
    # }
]


CURRENCY = [
    {
        "name": "**1000 Golden Coins**",
        "value": f"Cost: **3** {u.ICON['gem']}\n`{u.PREF}buy gc1`"
    },
    {
        "name": "**2250 Golden Coins**",
        "value": f"Cost: **6** {u.ICON['gem']}\n`{u.PREF}buy gc2`"
    },
    {
        "name": "**11000 Golden Coins**",
        "value": f"Cost: **24** {u.ICON['gem']}\n`{u.PREF}buy gc3`"
    },
    {
        "name": "**1 Raid Ticket**",
        "value": f"Cost: **2** {u.ICON['gem']}\n`{u.PREF}buy rt1`"
    },
    {
        "name": "**2 Raid Ticket**",
        "value": f"Cost: **4** {u.ICON['gem']}\n`{u.PREF}buy rt2`"
    },
    {
        "name": "**3 Raid Ticket**",
        "value": f"Cost: **6** {u.ICON['gem']}\n`{u.PREF}buy rt3`"
    }
]


class Shop(discord.ui.View):
    def __init__(self, uid: int):
        super().__init__()
        self.uid = uid
        self.coins = dm.get_user_coin(uid)
        self.gems = dm.get_user_gem(uid)
        self.tokens = dm.get_user_token(uid)

    @discord.ui.button(label="Daily Deals", style=discord.ButtonStyle.blurple)
    async def daily_deals(self, i: discord.Interaction, button: discord.ui.Button):
        user_deals = dm.get_user_deals(self.uid).split(",")
        embed = discord.Embed(
            title="Shop - Daily Deals:",
            description=f"{u.ICON['coin']} **{self.coins}** "
                        f"{u.ICON['gem']} **{self.gems}**",
            color=discord.Color.gold()
        )

        for v, d in enumerate(user_deals):
            card = d.split('.')
            rarity = u.rarity_cost(card[1])
            if d[0] != "-":
                cost = round(1.6 ** int(card[0]) * 50 * u.price_factor(card[1]))
                embed.add_field(
                    name=f"**[{rarity}] {card[1]} lv: {card[0]}**",
                    value=f"Cost: **{cost}** {u.ICON['coin']}\n`{u.PREF}buy {v + 1}`"
                )
            else:
                embed.add_field(
                    name=f"**[{rarity}] {card[1]} lv: {card[0][1:]}**",
                    value="Sold out"
                )
        
        embed.set_footer(
            text=f"Wait {u.time_til_midnight()} or use `{u.PREF}buy r` to refresh the shop"
        )

        await i.response.edit_message(embed=embed)

    @discord.ui.button(label="Card Packs", style=discord.ButtonStyle.blurple)
    async def card_packs(self, i: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Shop - Card Packs:",
            description=f"{u.ICON['coin']} **{self.coins}** {u.ICON['gem']} "
                        f"**{self.gems}** {u.ICON['token']} **{self.tokens}**",
            color=discord.Color.green()
        )

        for p in PACKS:
            embed.add_field(**p)
        embed.set_footer(text="Let the buyer beware")

        await i.response.edit_message(embed=embed)

    @discord.ui.button(label="Coins & Raid Tickets", style=discord.ButtonStyle.blurple)
    async def currency(self, i: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Shop - Currencies:",
            description=f"{u.ICON['coin']} **{self.coins}** {u.ICON['gem']} **{self.gems}**",
            color=discord.Color.green()
        )
        for field in CURRENCY:
            embed.add_field(**field)

        await i.response.edit_message(embed=embed)
