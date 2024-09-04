import discord
import discord.ui as ui

import db
import resources as r
from helpers import util as u
from views.adventure.template import Backpack, Exit, InteractionCheckMixin

from ...confirm import Confirm


class TradeSelect(ui.Select["Trade"]):
    def __init__(self, user: discord.Member, trades: dict[str, list[tuple[str, int]]]):
        self.user = user
        self.trades = {
            c.lower(): [(r_[0].lower(), r_[1]) for r_ in req] for c, req in trades.items()
        }

        choices = []
        for c in self.trades:
            choices.append(discord.SelectOption(label=c.title(), value=c))
        super().__init__(options=choices, placeholder="What do you want to trade for?")

    async def callback(self, i: discord.Interaction):
        assert self.view is not None
        embed = discord.Embed(title="Are you sure you want to buy this item?")

        product = self.values[0]
        reqs = self.trades[product]
        description = ["You'll need:"]
        for item, amt in reqs:
            description.append(f"• {amt} {item}")
        embed.description = "\n".join(description)

        view = Confirm(self.user)
        await i.response.send_message(embed=embed, view=view)
        msg = await i.original_response()
        await view.wait()

        if not view.value:
            await msg.delete()
            return

        player = db.Player.get_by_id(i.user.id)
        inv = player.inventory
        if u.bp_weight(inv) + r.item(product).weight > r.BP_CAP:
            await msg.edit(
                content="Hey, your pack's too full. I couldn't fit it in if I tried.",
                view=None,
            )
            await msg.delete(delay=5)
            return

        for item, amt in reqs:
            if inv.get(item, 0) < amt:
                await msg.edit(
                    content=(
                        "Sorry pal, I can't give credits. "
                        "Come back when you're a little, mmmmmm, RICHER."
                    ),
                    embed=None,
                    view=None,
                )
                break
        else:
            for item, amt in reqs:
                inv[item] -= amt
            inv[product] = inv.get(product, 0) + 1

            player.save()

            await msg.edit(
                content=f"Alright man. Here's your {product.title()}.",
                embed=None,
                view=None,
            )
        await msg.delete(delay=5)


class Trade(InteractionCheckMixin, ui.View):
    def __init__(self, user: discord.Member, trades: dict[str, list[tuple[str, int]]]):
        super().__init__(user)
        self.trades = trades
        self.add_item(TradeSelect(user, trades))
        self.add_item(Backpack())
        self.add_item(Exit())
