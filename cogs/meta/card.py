import math

import discord
from discord.ext import commands

from helpers import db_manager as dm, util as u, checks
from views import Confirm


class Card(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["dis"], description="Deletes unwanted cards.")
    @checks.not_preoccupied("discarding cards")
    @checks.is_registered()
    async def discard(self, ctx: commands.Context, cards: commands.Greedy[int]):
        """Deletes unwanted cards."""

        if not cards:
            await ctx.reply("You haven't provided any cards to discard!")
            return
        
        a = ctx.author
        to_discard = []
        discard_msg = []
        error_msg = []
        for c in cards:
            name = dm.get_card_name(a.id, c)
            lvl = dm.get_card_level(a.id, c)
            decks = dm.get_card_decks(c)

            if not name:
                error_msg.append(f"You don't have a Card `#{c}`!")
            elif (c, a.id) in to_discard:
                error_msg.append(f"You have already chosen Card `#{c}` for disposal!")
            elif any(decks):
                error_msg.append(f"Card #`{c}` is in one of your decks!")
            else:
                to_discard.append((c, a.id))
                discard_msg.append(
                    f"**[{u.rarity_cost(name)}] {name} lv: {lvl}** #`{c}`"
                )

        msg = "\n".join(error_msg) + "\n"
        if not to_discard:
            await ctx.reply(msg)
            return
        msg += "You sure you want to discard:\n" + \
                "\n".join(discard_msg) + \
                f"\n{u.ICON['bers']} *(Discarded cards can't be retrieved!)*"

        view = Confirm()
        msg = await ctx.reply(msg, view=view)
        await view.wait()

        if view.value is None:
            await msg.edit(content="Discarding timed out.", view=None)
            return
        if not view.value:
            await msg.edit(content="Discarding canceled.", view=None)
            return

        dm.delete_user_cards(to_discard)
        s = 's' if len(to_discard) > 1 else ''
        await msg.edit(content=f"{len(to_discard)} card{s} discarded.", view=None)

    @commands.hybrid_command(
        aliases=["upg"],
        description="Upgrade a card by merging it with another."
    )
    @checks.not_preoccupied("upgrading card")
    @checks.is_registered()
    async def upgrade(self, ctx: commands.Context, card_id: int, other_card_id: int):
        """Upgrade a card by merging it with another."""

        if card_id == other_card_id:
            await ctx.reply(f"You cannot upgrade a card using itself!")
            return

        a = ctx.author
        card = dm.get_card_name(a.id, card_id), dm.get_card_level(a.id, card_id)
        other_card = dm.get_card_name(a.id, other_card_id), dm.get_card_level(a.id, other_card_id)

        if card[0] is None and other_card[0] is None:
            await ctx.reply(f"You have neither card `#{card_id}` nor `#{other_card_id}`!")
            return
        
        if card[0] is None or other_card[0] is None:
            missing = card_id if card[0] is None else other_card_id
            await ctx.reply(f"You don't have card `#{missing}`!")
            return

        if card[1] != other_card[1]:
            await ctx.reply("Both cards need to be the same level!")
            return

        if u.cards_dict(1, card[0])["rarity"] != u.cards_dict(1, other_card[0])["rarity"]:
            await ctx.reply("Both cards need to be the same rarity!")
            return

        if card[1] >= 15:
            await ctx.reply("The card to upgrade is maxed out!")
            return

        if any(dm.get_card_decks(other_card_id)):
            await ctx.reply(
                "The sacrificial card you chose "
                "is currently in one of your deck slots-\n"
                f"Do `{u.PREF}remove {other_card_id}` first before you sacrifice it!"
            )
            return

        upgrade_cost = math.floor(((card[1] + 1) ** 2) * 10)
        coins = dm.get_user_coin(a.id)
        if coins < upgrade_cost:
            await ctx.reply(f"You don't have enough coins to upgrade! ({upgrade_cost} coins)")
            return

        view = Confirm()
        msg = await ctx.reply(
            f"**[{u.rarity_cost(card[0])}] {card[0]} lv: {card[1]}**\n"
            f"**[{u.rarity_cost(other_card[0])}] {other_card[0]} lv: {other_card[1]}**\n"
            f"Upgrading cost {upgrade_cost} {u.ICON['coin']}.",
            view=view
        )
        await view.wait()

        if view.value is None:
            await msg.edit(content="Upgrading timed out.", view=None)
            return
        if not view.value:
            await msg.edit(content="Upgrading canceled.", view=None)
            return

        dm.log_quest(7, 1, a.id)
        dm.set_user_coin(a.id, coins - upgrade_cost)
        dm.delete_user_cards([(other_card_id, a.id)])
        dm.set_card_level(a.id, card_id, card[1] + 1)

        embed = discord.Embed(
            title="Card upgraded successfully!",
            description=f"-{upgrade_cost} {u.ICON['coin']} "
                        f"+{(card[1] + 1) * 10} {u.ICON['exp']}",
            color=discord.Color.green()
        )
        embed.add_field(
            name=f"You got a [{u.rarity_cost(card[0])}] {card[0]} lv: {card[1] + 1} from:",
            value=f"[{u.rarity_cost(card[0])}] {card[0]} lv: {card[1]}\n"
                  f"[{u.rarity_cost(other_card[0])}] {other_card[0]} lv: {other_card[1]}"
        )
        embed.set_thumbnail(url=ctx.author.avatar.url)
        await msg.edit(content=None, embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(Card(bot))