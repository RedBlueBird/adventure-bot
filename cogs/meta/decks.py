import math
import asyncio
import typing as t

import discord
from discord.ext import commands

from helpers import db_manager as dm
from helpers import checks
import util as u
from views import Confirm


class Decks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(description="Set the card display order.")
    @checks.is_registered()
    async def order(
            self, ctx: commands.Context,
            card_property: t.Literal["level", "ID", "name", "energy", "rarity"],
            order_by: t.Literal["ascending", "descending"]
    ):
        """Set the card display order."""
        order = None
        card_property = card_property.lower()
        if card_property == "level":
            order = 1
        elif card_property == "name":
            order = 3
        elif card_property == "ID":
            order = 5
        elif card_property == "energy":
            order = 7
        elif card_property == "rarity":
            order = 8
        assert order is not None

        if order_by == "descending":
            order += 1

        dm.set_user_order(ctx.author.id, order)
        await ctx.reply(f"The order had been set to {card_property} {order_by}.")

    @commands.command(aliases=["dis"], description="cards")
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

    @commands.hybrid_command(
        aliases=["selectdeck", "sel", "se"],
        description="Get a deck from your deck slots."
    )
    @checks.is_registered()
    async def select(self, ctx: commands.Context, slot: int = 0):
        """Get a deck from your deck slots."""

        a = ctx.author
        if not 1 <= slot <= 6:
            await ctx.reply("The deck slot number must between 1-6!")
            return

        if dm.get_user_level(a.id) < u.DECK_LVL_REQ[slot]:
            await ctx.reply(f"Deck #{slot} is unlocked at {u.DECK_LVL_REQ[slot]}!")
            return

        dm.set_user_deck_slot(a.id, slot)
        await ctx.reply(f"Deck #{slot} is now selected!")

    @commands.hybrid_command(description="Returns the card IDs of your current deck.")
    @checks.is_registered()
    async def deck_ids(self, ctx: commands.Context, slot: int = 0):
        """Returns the card IDs of your current deck."""

        a = ctx.author
        if not 0 <= slot <= 6:
            await ctx.reply("The deck slot number must be between 1-6!")
            return

        slot = slot if slot != 0 else dm.get_user_deck_slot(a.id)
        cards = dm.get_user_deck(a.id, slot)
        await ctx.reply(
            f"All the card IDs in Deck #{slot}:\n"
            f"```{' '.join([str(c[0]) for c in cards])}```"
        )

    @commands.hybrid_command(
        aliases=["replace", "switch", "change", "alter"],
        description="Swap a card from your deck with another."
    )
    @checks.not_preoccupied()
    @checks.is_registered()
    async def swap(self, ctx: commands.Context, new: int, old: int):
        """Swap a card from your deck with another."""

        a = ctx.author
        slot = dm.get_user_deck_slot(a.id)
        err = None
        swap = []

        for x in [new, old]:
            name = dm.get_card_name(a.id, x)
            lvl = dm.get_card_level(a.id, x)
            decks = dm.get_card_decks(x)

            if not name:
                err = f"You don't have a card #`{x}`!"
            elif decks[slot - 1] == 1 and x == new:
                err = f"Card #{new} is already in a deck of yours!"
            elif decks[slot - 1] == 0 and x == old:
                err = f"Card #{old} isn't in your deck!"
            else:
                swap.append(f"**[{u.rarity_cost(name)}] {name} lv: {lvl}** #`{x}`")

            if err is not None:
                await ctx.reply(err)
                return

        dm.set_user_card_deck(a.id, slot, 1, new)
        dm.set_user_card_deck(a.id, slot, 0, old)
        await ctx.reply(
            f"You swapped\n{swap[0]} with\n{swap[1]}\nin deck #{slot}!"
        )

    @commands.command(aliases=["use"], description="Add a card to your deck.")
    @checks.not_preoccupied()
    @checks.is_registered()
    async def add(self, ctx: commands.Context, cards: commands.Greedy[int]):
        """Add a card to your deck."""

        if not cards:
            await ctx.reply("You haven't provided any cards to add!")
            return
        
        a = ctx.author

        add_ids = []
        add_msg = []
        error_msg = []

        slot = dm.get_user_deck_slot(a.id)
        deck_size = dm.get_user_deck_count(a.id, slot)
        for c in cards:
            name = dm.get_card_name(a.id, c)
            lvl = dm.get_card_level(a.id, c)
            decks = dm.get_card_decks(c)

            if not name:
                error_msg.append(f"You don't have a card #`{c}`!")
            elif decks[slot - 1] or c in add_ids:
                error_msg.append(f"Card #`{c}` is already in your deck!")
            else:
                add_ids.append(c)
                add_msg.append(f"**[{u.rarity_cost(name)}] {name} lv: {lvl}** #`{c}`")

        if deck_size + len(add_ids) > 12:
            await ctx.reply("Your deck can't have that many cards!")
            return

        for i in add_ids:
            dm.set_user_card_deck(a.id, slot, 1, i)

        msg = f" \n".join(error_msg) + "\n"
        if len(add_ids) > 0:
            msg += f"These cards have been added to deck #{slot}:\n" + \
                   f"\n".join(add_msg)
        await ctx.reply(msg)

    @commands.command(aliases=["rem"], description="Remove a card from your deck.")
    @checks.not_preoccupied()
    @checks.is_registered()
    async def remove(self, ctx: commands.Context, cards: commands.Greedy[int]):
        """Remove a card from your deck."""

        if not cards:
            await ctx.reply("You haven't provided any cards to remove!")
            return

        a = ctx.author

        remove_ids = []
        remove_msg = []
        error_msg = []

        slot = dm.get_user_deck_slot(a.id)
        for c in cards:
            name = dm.get_card_name(a.id, c)
            lvl = dm.get_card_level(a.id, c)
            decks = dm.get_card_decks(c)

            if not name:
                error_msg.append(f"You don't have a card #`{c}`!")
            elif decks[slot - 1] == 0 or c in remove_ids:
                error_msg.append(f"Card #`{c}` isn't in your current deck!")
            elif c not in remove_ids:
                remove_ids.append(c)
                remove_msg.append(f"**[{u.rarity_cost(name)}] {name} lv: {lvl}** #`{c}`")

        for i in remove_ids:
            dm.set_user_card_deck(a.id, slot, 0, i)

        msg = f"\n".join(error_msg) + "\n"
        if len(remove_ids) > 0:
            msg += f"These cards have been removed from deck #{slot}:\n" + \
                   f"\n".join(remove_msg)
        await ctx.reply(msg)

    @commands.hybrid_command(aliases=["cleardeck"], description="Clear your current deck.")
    @checks.is_registered()
    @checks.not_preoccupied("clearing a deck slot")
    async def clear(self, ctx: commands.Context):
        """Clear your current deck."""

        a = ctx.author
        slot = dm.get_user_deck_slot(a.id)
        deck = dm.get_user_deck(a.id, slot)

        if len(deck) == 0:
            await ctx.reply(f"Your deck's already empty!")
            return

        view = Confirm()
        msg = await ctx.reply(f"Do you really want to clear deck #{slot}?", view=view)
        await view.wait()

        if view.value is None:
            await msg.edit(content="Clearing timed out", view=None)
            return
        if not view.value:
            await msg.edit(content="Clearing cancelled", view=None)
            return

        for i in deck:
            dm.set_user_card_deck(a.id, slot, 0, i[0])
        await msg.edit(
            content=f"Deck #{slot} has been cleared! \n"
                    f"Do `{u.PREF}add [cards]` to add new cards to your deck!"
        )

async def setup(bot):
    await bot.add_cog(Decks(bot))
