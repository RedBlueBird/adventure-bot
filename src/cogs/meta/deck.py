import typing as t

from discord.ext import commands

import db
from helpers import resources as r, checks
from views import Confirm


class Deck(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(description="Set the card display order.")
    @checks.is_registered()
    async def order(
        self,
        ctx: commands.Context,
        card_property: t.Literal["level", "id", "name", "energy", "rarity"],
        order: t.Literal["ascending", "descending"],
    ):
        """Set the card display order."""
        o_num = None
        for v, p in enumerate(["level", "name", "id", "energy", "rarity"]):
            if p == card_property:
                o_num = 2 * v + 1
        assert o_num is not None

        o_num += order == "descending"

        player = db.Player.get_by_id(ctx.author.id)
        player.card_order = o_num
        player.save()
        await ctx.reply(f"The order is now {card_property} {order}.")

    @commands.hybrid_command(
        aliases=["selectdeck", "sel", "se"],
        description="Get a deck from your deck slots.",
    )
    @checks.is_registered()
    async def select(self, ctx: commands.Context, slot: int):
        """Get a deck from your deck slots."""

        if not 1 <= slot <= 6:
            await ctx.reply("The deck slot number must between 1-6!")
            return

        player = db.Player.get_by_id(ctx.author.id)
        if player.level < r.DECK_LVL_REQ[slot]:
            await ctx.reply(f"Deck #{slot} is unlocked at level {r.DECK_LVL_REQ[slot]}!")
            return

        player.deck = slot
        player.save()
        await ctx.reply(f"Deck #{slot} is now selected!")

    @commands.hybrid_command(description="Returns the card IDs of your current deck.")
    @checks.is_registered()
    async def deck_ids(self, ctx: commands.Context, slot: int = 0):
        """Returns the card IDs of your current deck."""

        if not 0 <= slot <= 6:
            await ctx.reply("The deck slot number must be between 1-6!")
            return

        player = db.Player.get_by_id(ctx.author.id)
        slot = slot if slot != 0 else player.deck
        cards = db.get_deck(player.id, slot)
        if not cards:
            await ctx.reply(f"You don't have any cards in deck #{slot}!")
            return

        c_ids = [str(c.id) for c in cards]
        await ctx.reply(f"All the card IDs in deck #{slot}:\n```{' '.join(c_ids)}```")

    @commands.hybrid_command(
        aliases=["replace", "switch", "change", "alter"],
        description="Swap a card from your deck with another.",
    )
    @checks.not_preoccupied()
    @checks.is_registered()
    async def swap(self, ctx: commands.Context, new: int, old: int):
        """Swap a card from your deck with another."""

        player = db.Player.get_by_id(ctx.author.id)
        new_card = db.Card.get_or_none((db.Card.id == new) & (db.Card.owner == player))
        old_card = db.Card.get_or_none((db.Card.id == old) & (db.Card.owner == player))

        if new_card is None:
            await ctx.reply(f"You don't have a card #`{new}`!")
            return
        deck = db.Deck.get((db.Deck.owner == player.id) & (db.Deck.slot == player.deck))
        deck_cards = {c.card_id for c in deck.cards}
        if old not in deck_cards:
            await ctx.reply(f"Your current deck doesn't contain a card #`{old}`!")
            return

        db.DeckCard.delete().where(
            (db.DeckCard.deck == deck) & (db.DeckCard.card == old_card)
        ).execute()
        db.DeckCard.create(deck=deck, card=new_card)

        await ctx.reply(
            "You replaced\n"
            f"{r.card(old_card.name)} lv: {old_card.level} with\n"
            f"{r.card(new_card.name)} lv: {new_card.level}\n"
            f"in deck #{deck.slot}!"
        )

    @commands.hybrid_command(aliases=["use"], description="Add a card to your deck.")
    @checks.not_preoccupied()
    @checks.is_registered()
    async def add(self, ctx: commands.Context, cards: commands.Greedy[int]):
        """Add a card to your deck."""
        if not cards:
            await ctx.reply("You haven't provided any cards to add!")
            return

        player = db.Player.get_by_id(ctx.author.id)
        deck = db.Deck.get((db.Deck.owner == player.id) & (db.Deck.slot == player.deck))
        deck_cards = {c.card_id for c in deck.cards}

        to_add = []
        add_msg = []
        error_msg = []
        for c in cards:
            card = db.Card.get_or_none((db.Card.id == c) & (db.Card.owner == player))
            if card is None:
                error_msg.append(f"You don't have a card #`{c}`!")
                continue

            c_info = r.card(card.name)
            if card.id in to_add or card.id in deck_cards:
                error_msg.append(f"Card #`{c}` is already in your deck!")
            else:
                to_add.append(c)
                add_msg.append(f"{c_info} lv: {card.level} #`{c}`")

        if len(deck_cards) + len(to_add) > 12:
            await ctx.reply("Your deck can't have that many cards!")
            return

        to_create = [{"deck": deck, "card": i} for i in to_add]
        db.DeckCard.insert_many(to_create).execute()

        msg = "\n".join(error_msg)
        if to_add:
            msg += f"These cards have been added to deck #{player.deck}:\n" + f"\n".join(add_msg)
        await ctx.reply(msg)

    @commands.hybrid_command(aliases=["rem"], description="Remove a card from your deck.")
    @checks.not_preoccupied()
    @checks.is_registered()
    async def remove(self, ctx: commands.Context, cards: commands.Greedy[int]):
        """Remove a card from your deck."""
        if not cards:
            await ctx.reply("You haven't provided any cards to remove!")
            return

        player = db.Player.get_by_id(ctx.author.id)
        deck = db.Deck.get((db.Deck.owner == player.id) & (db.Deck.slot == player.deck))
        deck_cards = {c.card_id for c in deck.cards}

        to_remove = []
        remove_msg = []
        error_msg = []
        for c in cards:
            card = db.Card.get_or_none((db.Card.id == c) & (db.Card.owner == player))
            if card is None:
                error_msg.append(f"You don't have a card #`{c}`!")
                continue

            c_info = r.card(card.name)
            if c in to_remove or c not in deck_cards:
                error_msg.append(f"Card #`{c}` isn't in your current deck!")
            elif c not in to_remove:
                to_remove.append(c)
                remove_msg.append(f"{c_info} lv: {card.level} #`{c}`")

        db.DeckCard.delete().where(
            (db.DeckCard.deck == deck) & (db.DeckCard.card.in_(to_remove))
        ).execute()

        msg = "\n".join(error_msg)
        if to_remove:
            msg += f"These cards have been removed from deck #{deck.slot}:\n" + f"\n".join(
                remove_msg
            )
        await ctx.reply(msg)

    @commands.hybrid_command(aliases=["cleardeck"], description="Clear your current deck.")
    @checks.is_registered()
    @checks.not_preoccupied("clearing a deck slot")
    async def clear(self, ctx: commands.Context):
        """Clear your current deck."""

        a = ctx.author
        player = db.Player.get_by_id(a.id)
        cards = db.get_deck(player.id, player.deck)
        if not cards:
            await ctx.reply(f"Your deck's already empty!")
            return

        view = Confirm()
        msg = await ctx.reply(f"Do you really want to clear deck #{player.deck}?", view=view)
        await view.wait()

        if view.value is None:
            await msg.edit(content="Clearing timed out.", view=None)
            return
        if not view.value:
            await msg.edit(content="Clearing canceled.", view=None)
            return

        sel_deck = db.Deck.get((db.Deck.owner == player.id) & (db.Deck.slot == player.deck))
        db.DeckCard.delete().where(db.DeckCard.deck == sel_deck).execute()
        await msg.edit(
            content=(
                f"Deck #{player.deck} has been cleared! \n"
                f"Do `{r.PREF}add [cards]` to add new cards to your deck!"
            ),
            view=None,
        )


async def setup(bot):
    await bot.add_cog(Deck(bot))
