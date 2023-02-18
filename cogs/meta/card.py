import math

import discord
from discord.ext import commands

from helpers import db_manager as dm
from helpers import checks
import util as u
from views import Confirm

class Card(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["dis"], description="Deletes unwanted cards.")
    @checks.not_preoccupied("discarding cards")
    @checks.is_registered()
    async def discard(self, ctx: commands.Context, cards: commands.Greedy[int]):
        """Deletes unwanted cards."""

        a = ctx.author
        to_discard = []
        discard_msg = []
        error_msg = []
        for c in cards:
            name = dm.get_card_name(a.id, c)
            lvl = dm.get_card_level(a.id, c)
            decks = dm.get_card_decks(c)

            if not name or c in to_discard:
                error_msg.append(f"You don't have a Card #{c}`!")
            elif any(decks):
                error_msg.append(f"Card #`{c}` is in one of your decks!")
            else:
                to_discard.append((c, a.id))
                discard_msg.append(
                    f"**[{u.rarity_cost(name)}] {name} lv: {lvl}** #`{c}`"
                )

        msg = "\n".join(error_msg) + "\n"
        if len(to_discard) == 0:
            return
        else:
            msg += "You sure you want to discard:\n" + \
                   "\n".join(discard_msg) + \
                   f"\n{u.ICON['bers']} *(Discarded cards can't be retrieved!)*"

        view = Confirm()
        msg = await ctx.reply(msg, view=view)
        await view.wait()

        if view.value is None:
            await msg.edit(content="Discarding timed out", view=None)
            return
        if not view.value:
            await msg.edit(content="Discarding cancelled", view=None)
            return

        dm.delete_user_cards(to_discard)
        s = 's' if len(to_discard) > 1 else ''
        await msg.edit(content=f"{len(to_discard)} card{s} discarded.")

    @commands.hybrid_command(
        aliases=["mer"],
        description="Upgrade a card with two others."
    )
    @checks.not_preoccupied("trying to merge cards")
    @checks.is_registered()
    async def merge(self, ctx: commands.Context, card1: int, card2: int):
        """Upgrade a card with two others."""

        a = ctx.author

        c1_id = card1
        card1 = dm.get_card_name(a.id, c1_id), dm.get_card_level(a.id, c1_id)
        if card1[0] is None:
            await ctx.reply("You don't have the first card!")
            return

        c2_id = card2
        card2 = dm.get_card_name(a.id, c2_id), dm.get_card_level(a.id, c2_id)
        if card1[0] is None or card2[0] is None:
            missing = 'first' if card1[0] is None else 'second'
            await ctx.reply(f"You don't have the {missing} card!")
            return

        if card1[1] != card2[1]:
            await ctx.reply("Both cards need to be the same level!")
            return

        if u.cards_dict(1, card1[0])["rarity"] != u.cards_dict(1, card2[0])["rarity"]:
            await ctx.reply("Both cards need to be the same rarity!")
            return

        if card1[1] >= 15:
            await ctx.reply("The card to merge is maxed out!")
            return

        if any(dm.get_card_decks(c2_id)):
            await ctx.reply(
                "The sacrificial card you chose "
                "is currently in one of your deck slots- \n"
                f"Use `{u.PREF}remove (* card_ids)` first before you merge it!"
            )
            return

        merge_cost = math.floor(((card1[1] + 1) ** 2) * 10)
        coins = dm.get_user_coin(a.id)
        if coins < merge_cost:
            await ctx.reply(f"You don't have enough coins ({merge_cost} coins) to complete this merge!")
            return

        view = Confirm()
        msg = await ctx.reply(
            f"**[{u.rarity_cost(card1[0])}] {card1[0]} lv: {card1[1]}**\n"
            f"**[{u.rarity_cost(card2[0])}] {card2[0]} lv: {card2[1]}**\n"
            f"merging cost {merge_cost} {u.ICON['coin']}.",
            view=view
        )
        await view.wait()

        if view.value is None:
            await msg.edit(content="Merging timed out", view=None)
            return
        if not view.value:
            await msg.edit(content="Merging cancelled", view=None)
            return

        dm.log_quest(7, 1, a.id)
        dm.set_user_coin(a.id, coins - merge_cost)
        dm.delete_user_cards([(c2_id, a.id)])
        dm.set_card_level(a.id, c1_id, card1[1] + 1)

        embed = discord.Embed(
            title="Cards merged successfully!",
            description=f"-{merge_cost} {u.ICON['coin']} "
                        f"+{(card1[1] + 1) * 10} {u.ICON['exp']}",
            color=discord.Color.green()
        )
        embed.add_field(
            name=f"You got a [{u.rarity_cost(card1[0])}] {card1[0]} lv: {card1[1] + 1} from:",
            value=f"[{u.rarity_cost(card1[0])}] {card1[0]} lv: {card1[1]}\n"
                  f"[{u.rarity_cost(card2[0])}] {card2[0]} lv: {card2[1]}"
        )
        embed.set_thumbnail(url=ctx.author.avatar.url)
        await msg.edit(content=None, embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(Card(bot))