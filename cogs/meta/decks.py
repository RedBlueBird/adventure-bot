import math
import asyncio
import typing as t

import discord
from discord.ext import commands

from helpers import db_manager as dm
from helpers import checks
import util as u


class Decks(commands.Cog, name="decks"):
    @commands.hybrid_command(brief="Set the card display order.")
    @checks.is_registered()
    async def order(
            self, ctx: commands.Context,
            card_property: t.Literal["level", "id", "name", "energy", "rarity"],
            order_by: t.Literal["ascending", "descending"]
    ):
        """Set the card display order."""
        order = None
        card_property = card_property.lower()
        if card_property == "level":
            order = 1
        elif card_property == "name":
            order = 3
        elif card_property == "id":
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

    @commands.command(aliases=["dis"], brief="cards")
    @checks.is_registered()
    @checks.not_preoccupied("discarding cards")
    async def discard(self, ctx: commands.Context, cards: commands.Greedy[int]):
        """Deletes unwanted cards."""

        a = ctx.author

        to_discard = []
        discard_msg = []
        error_msg = []
        for c in cards:
            card_name = dm.get_card_name(a.id, c)
            card_level = dm.get_card_level(a.id, c)
            card_decks = dm.get_card_decks(c)

            if not card_name or c in to_discard:
                error_msg.append(f"You don't have a Card #{c}`!")
            elif sum(card_decks):
                error_msg.append(f"Card #`{c}` is in one of your decks!")
            else:
                to_discard.append((c, a.id))
                discard_msg.append(
                    f"**[{u.rarity_cost(card_name)}] {card_name} lv: {card_level}** #`{c}`"
                )

        msg = f" \n".join(error_msg) + "\n"
        if len(to_discard) == 0:
            return
        else:
            msg += f"You sure you want to discard: \n" + \
                   f" \n".join(discard_msg) + \
                   f"\n{u.ICON['bers']} *(Discarded cards can't be retrieved!)*"
        msg = await ctx.reply(msg)
        await msg.add_reaction("✅")
        await msg.add_reaction("❎")

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add", timeout=30.0,
                check=checks.valid_reaction(["❎", "✅"], ctx.author, msg)
            )
        except asyncio.TimeoutError:
            await msg.edit(content=f"Discarding cancelled")
            await msg.clear_reactions()
            return
        
        await msg.clear_reactions()
        if reaction.emoji == "❎":
            await msg.edit(content=f"Discarding cancelled")
            return

        dm.delete_user_cards(to_discard)
        await msg.edit(content=f"{len(to_discard)} card(s) discarded successfully!")

    @commands.hybrid_command(aliases=["mer"], brief="Upgrade a card with two others.")
    @checks.is_registered()
    @checks.not_preoccupied("trying to merge cards")
    async def merge(self, ctx: commands.Context, card1: int, card2: int):
        """Upgrade a card to next level with two other cards."""

        a_id = ctx.author.id
        mention = ctx.author.mention

        dm.cur.execute(
            f"SELECT deck1,deck2,deck3,deck4,deck5,deck6 FROM playersachivements WHERE userid = '{a_id}'")
        decks = [int(k) for i in dm.cur.fetchall()[0] for k in i.split(",")]

        dm.cur.execute(f"SELECT card_name, card_level, owned_user FROM cardsinfo WHERE id = {card1}")
        card1 = dm.cur.fetchall()[0]
        if not card1:
            await ctx.send(f"{mention}, you don't have the first card!")
            return

        dm.cur.execute(f"SELECT card_name, card_level, owned_user FROM cardsinfo WHERE id = {card2}")
        card2 = dm.cur.fetchall()[0]
        if not card2:
            await ctx.send(f"{mention}, you don't have the second card!")
            return

        if card1[2] != str(a_id) or card2[2] != str(a_id):
            await ctx.send(f"{mention}, you have to own both cards!")
            return

        if card1[1] != card2[1] or \
                u.cards_dict(1, card1[0])["rarity"] != u.cards_dict(1, card2[0])["rarity"]:
            await ctx.send(f"{mention}, both cards need to be the same level and rarity!")
            return

        if card1[1] >= 15:
            await ctx.send(f"{mention}, the card to merge is maxed out!")
            return

        if card2 in decks:
            await ctx.send(
                f"{mention}, the sacrificial card you chose "
                "is currently in one of your deck slots- \n"
                f"`{u.PREF}remove (* card_ids)` first before you merge it away!"
            )
            return

        dm.cur.execute("SELECT * FROM playersinfo WHERE userid = " + str(a_id))
        player_info = dm.cur.fetchall()

        merge_cost = math.floor(((card1[1] + 1) ** 2) * 10)
        if player_info[0][5] < merge_cost:
            await ctx.send(f"{mention} You don't have enough coins ({merge_cost} coins) to complete this merge!")
            return

        msg = await ctx.send(
            f"{mention}, \n"
            f"**[{u.rarity_cost(card1[0])}] {card1[0]} lv: {card1[1]}**\n"
            f"**[{u.rarity_cost(card2[0])}] {card2[0]} lv: {card2[1]}**\n"
            f"merging cost {merge_cost} {u.ICON['coin']}."
        )
        await msg.add_reaction("✅")
        await msg.add_reaction("❎")
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=30.0,
                check=checks.valid_reaction(["❎", "✅"], ctx.author, msg)
            )
        except asyncio.TimeoutError:
            await msg.edit(content=f"{mention}, merging timed out")
            await msg.clear_reactions()
        else:
            if reaction.emoji == "❎":
                await msg.edit(content=f"{mention}, merging timed out")
                await msg.clear_reactions()
            else:
                await msg.delete()
                dm.log_quest(7, 1, a_id)
                sql = "UPDATE playersinfo SET coins = coins - %s, exps = exps + %s WHERE userid = %s"
                value = (math.floor(((card1[1] + 1) ** 2) * 10), (card1[1] + 1) * 10, a_id)
                dm.cur.execute(sql, value)
                dm.cur.execute(f"DELETE FROM cardsinfo WHERE id = {card2}")
                dm.cur.execute(f"UPDATE cardsinfo SET card_level = card_level + 1 WHERE id = {card1}")
                dm.db.commit()

                embed = discord.Embed(
                    title="Cards merged successfully!",
                    description=f"-{math.floor(((card1[1] + 1) ** 2) * 10)} {u.ICON['coin']} "
                                f"+{(card1[1] + 1) * 10} {u.ICON['exp']}",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name=f"You got a [{u.rarity_cost(card1[0])}] {card1[0]} lv: {card1[1] + 1} from:",
                    value=f"[{u.rarity_cost(card1[0])}] {card1[0]} lv: {card1[1]} \n"
                          f"[{u.rarity_cost(card2[0])}] {card2[0]} lv: {card2[1]}"
                )
                embed.set_thumbnail(url=ctx.author.avatar.url)
                await ctx.send(embed=embed)

    @commands.hybrid_command(
        aliases=["selectdeck", "sel", "se"],
        brief="Get a deck from your deck slots."
    )
    @checks.is_registered()
    async def select(self, ctx: commands.Context, slot: int = 0):
        """Get a deck from your deck slots."""

        a = ctx.author
        if not 1 <= slot <= 6:
            await ctx.send("{member.mention} The deck slot number must between 1-6!")
            return

        user_level = dm.get_user_level(a.id)
        if user_level < u.DECK_LVL_REQ[slot]:
            await ctx.send(f"{a.mention} Deck #{slot} is unlocked at {u.DECK_LVL_REQ[slot]}!")
            return

        dm.set_user_deck_slot(a.id, slot)
        await ctx.send(f"{a.mention} Deck #{slot} is now selected!")

    @commands.hybrid_command(brief="Returns the card IDs of your current deck.")
    @checks.is_registered()
    async def deck_ids(self, ctx: commands.Context, slot: int = 0):
        """Returns the card IDs of your current deck."""

        a = ctx.author
        if not 0 <= slot <= 6:
            await ctx.send(f"{a.mention} The deck slot number must be between 1-6!")
            return

        slot = slot if slot != 0 else dm.get_user_deck_slot(a.id)
        cards = dm.get_user_deck(a.id, slot)
        await ctx.send(
            f"All the card IDs in Deck #{slot}: "
            f"\n`{' '.join([str(c[0]) for c in cards])}`"
        )

    @commands.hybrid_command(
        aliases=["replace", "switch", "change", "alter"],
        brief="Swap a card from your deck with another."
    )
    @checks.is_registered()
    @checks.not_preoccupied()
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
                err.append(f"You don't have a card #`{x}`!")
            elif decks[slot - 1] == 1 and x == new:
                err = f"Card #{new} is already in a deck of yours!"
                break
            elif decks[slot - 1] == 0 and x == old:
                err = f"Card #{old} isn't in your deck!"
                break
            else:
                swap.append(f"**[{u.rarity_cost(name)}] {name} lv: {lvl}** #`{x}`")

        if err is not None:
            await ctx.reply(err)
            return

        dm.set_user_card_deck(a.id, slot, 1, new)
        dm.set_user_card_deck(a.id, slot, 0, old)
        await ctx.send(
            f"You swapped\n{swap[0]} with\n{swap[1]}\nin deck #{slot}!"
        )

    @commands.command(aliases=["use"], brief="Add a card to your deck.")
    @checks.is_registered()
    @checks.not_preoccupied()
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
            elif deck_size + len(add_ids) >= 12:
                await ctx.reply("Your deck can't have that many cards!")
                return
            else:
                add_ids.append(c)
                add_msg.append(f"**[{u.rarity_cost(name)}] {name} lv: {lvl}** #`{c}`")

        for i in add_ids:
            dm.set_user_card_deck(a.id, slot, 1, i)

        msg = f" \n".join(error_msg) + "\n"
        if len(add_ids) > 0:
            msg += f"These cards have been added to deck #{slot}:\n" + \
                   f"\n".join(add_msg)
        await ctx.reply(msg)

    @commands.command(aliases=["rem"], brief="Remove a card from your deck.")
    @checks.is_registered()
    @checks.not_preoccupied()
    async def remove(self, ctx: commands.Context, cards: commands.Greedy[int]):
        """Remove a card from your deck."""

        if not cards:
            await ctx.reply(f"You haven't provided any cards to remove!")
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

    @commands.hybrid_command(aliases=["cleardeck"], brief="Clear your current deck.")
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

        msg = await ctx.reply(f"Do you really want to clear deck #{slot}?")
        await msg.add_reaction("✅")
        await msg.add_reaction("❎")
        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add", timeout=30.0,
                check=checks.valid_reaction(["❎", "✅"], ctx.author, msg)
            )
        except asyncio.TimeoutError:
            await msg.edit(content=f"Clearing deck cancelled")
            return
        finally:
            await msg.clear_reactions()

        if reaction.emoji == "❎":
            await msg.edit(content=f"Clearing deck cancelled")
            return

        for i in deck:
            dm.set_user_card_deck(a.id, slot, 0, i[0])
        await msg.edit(
            content=f"Deck #{slot} has been cleared! \n"
                    f"Do `{u.PREF}add [cards]` to add new cards to your deck!"
        )

async def setup(bot):
    await bot.add_cog(Decks(bot))
