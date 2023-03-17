import typing as t

from discord.ext import commands

from helpers import db_manager as dm, util as u, checks
from views import Confirm


class Deck(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(description="Set the card display order.")
    @checks.is_registered()
    async def order(
            self, ctx: commands.Context,
            card_property: t.Literal["level", "ID", "name", "energy", "rarity"],
            order: t.Literal["ascending", "descending"]
    ):
        """Set the card display order."""
        o_num = None
        if card_property == "level":
            o_num = 1
        elif card_property == "name":
            o_num = 3
        elif card_property == "ID":
            o_num = 5
        elif card_property == "energy":
            o_num = 7
        elif card_property == "rarity":
            o_num = 9
        assert o_num is not None

        o_num += order == "descending"

        dm.set_user_order(ctx.author.id, o_num)
        await ctx.reply(f"The order had been set to {card_property} {order}.")

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

    @commands.hybrid_command(aliases=["use"], description="Add a card to your deck.")
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

        msg = "\n".join(error_msg) + "\n"
        if add_ids:
            msg += f"These cards have been added to deck #{slot}:\n" + \
                   f"\n".join(add_msg)
        await ctx.reply(msg)

    @commands.hybrid_command(aliases=["rem"], description="Remove a card from your deck.")
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

        msg = "\n".join(error_msg) + "\n"
        if remove_ids:
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

        if not deck:
            await ctx.reply(f"Your deck's already empty!")
            return

        view = Confirm()
        msg = await ctx.reply(f"Do you really want to clear deck #{slot}?", view=view)
        await view.wait()

        if view.value is None:
            await msg.edit(content="Clearing timed out.", view=None)
            return
        if not view.value:
            await msg.edit(content="Clearing canceled.", view=None)
            return

        for i in deck:
            dm.set_user_card_deck(a.id, slot, 0, i[0])
        await msg.edit(
            content=f"Deck #{slot} has been cleared! \n"
                    f"Do `{u.PREF}add [cards]` to add new cards to your deck!"
        )

async def setup(bot):
    await bot.add_cog(Deck(bot))
