import discord
import discord.ui as ui

from helpers import db_manager as dm, util as u, resources as r
from views.adventure.template import AdventureTemplate
from ...confirm import Confirm


class TradeSelect(ui.Select["Trade"]):
    def __init__(self, trades: dict[str, list[tuple[str, int]]]):
        self.trades = {
            c.lower(): [(r_[0].lower(), r_[1]) for r_ in req]
            for c, req in trades.items()
        }
        
        choices = []
        for c in self.trades:
            choices.append(discord.SelectOption(label=c.title(), value=c))
        super().__init__(
            options=choices,
            placeholder="What do you want to trade for?"
        )

    async def callback(self, i: discord.Interaction):
        assert self.view is not None
        embed = discord.Embed(title="Are you sure you want to buy this item?")

        product = self.values[0]
        reqs = self.trades[product]
        description = ["You'll need:"]
        for item, amt in reqs:
            description.append(f"• {amt} {item}")
        embed.description = "\n".join(description)

        view = Confirm()
        await i.response.send_message(embed=embed, view=view)
        msg = await i.original_response()
        await view.wait()

        if not view.value:
            await msg.delete()
            return

        inv = dm.get_user_inventory(i.user.id)
        if u.bp_weight(inv) + r.item(product).weight > r.BP_CAP:
            await msg.edit(
                content="Hey, your pack's too full, I won't be able to fit it in!",
                view=None
            )
        print(inv)
        for item, amt in reqs:
            if inv.get(item, 0) < amt:
                await msg.edit(
                    content="Sorry pal, I can't give credits. "
                            "Come back when you're a little, mmmmmm, RICHER.",
                    embed=None, view=None
                )
                break
        else:
            for item, amt in reqs:
                inv[item] -= amt
            inv[product] = inv.get(product, 0) + 1

            dm.set_user_inventory(i.user.id, inv)

            await msg.edit(
                content=f"Alright! You traded for a {product.title()}.",
                embed=None, view=None
            )
        
        await msg.delete(delay=5)


class Trade(AdventureTemplate):
    def __init__(
            self, user: discord.Member,
            trades: dict[str, list[tuple[str, int]]]
    ):
        super().__init__(user)
        self.trades = trades
        self.add_item(TradeSelect(trades))

    @ui.button(label="Backpack", style=discord.ButtonStyle.blurple)
    async def backpack(self, i: discord.Interaction, button: ui.Button):
        inv = dm.get_user_inventory(self.user.id)
        await i.response.send_message(
            embed=u.container_embed(inv, "Backpack"),
            ephemeral=True
        )
