import math

import discord
from discord.ext import commands

import db
from helpers import resources as r, util as u, checks
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

        cards = set(cards)
        a = ctx.author
        db_cards = list(db.Card.select().where(db.Card.id.in_(cards)).where(db.Card.owner == a.id))
        if not db_cards:
            await ctx.reply("You don't have any of the specified cards!")
            return

        to_discard = []
        for c in db_cards:
            card = r.card(c.name)
            to_discard.append(
                f"**[{card.rarity}/{card.cost}] {card.name} lv: {c.level}** #`{c.id}`"
            )

        view = Confirm()
        confirm_msg = (
            "Are you sure you want to discard:\n"
            + "\n".join(to_discard)
            + f"\n{r.ICONS['berserk']} *(These can't be retrieved!)*"
        )
        msg = await ctx.reply(confirm_msg, view=view)
        await view.wait()

        if view.value is None:
            await msg.edit(content="Discarding timed out.", view=None)
            return
        if not view.value:
            await msg.edit(content="Discarding canceled.", view=None)
            return

        db.Card.delete().where(db.Card.id.in_([c.id for c in db_cards])).execute()
        s = "s" if len(to_discard) > 1 else ""  # lol
        await msg.edit(content=f"{len(to_discard)} card{s} successfully discarded.", view=None)

    @commands.hybrid_command(
        aliases=["up", "merge"], description="Upgrade a card by merging it with another."
    )
    @checks.not_preoccupied("upgrading cards")
    @checks.is_registered()
    async def upgrade(self, ctx: commands.Context, to_upgrade: int, to_destroy: int):
        """Upgrade a card by merging it with another."""

        if to_upgrade == to_destroy:
            await ctx.reply(f"You can't upgrade a card with itself!")
            return

        a = ctx.author
        upgraded = db.Card.get_or_none((db.Card.id == to_upgrade) & (db.Card.owner == a.id))
        destroyed = db.Card.get_or_none((db.Card.id == to_destroy) & (db.Card.owner == a.id))

        if upgraded is None:
            await ctx.reply(f"You don't own a card #`{to_upgrade}`!")
            return

        if destroyed is None:
            await ctx.reply(f"You don't own a card #`{to_destroy}`!")
            return

        if upgraded.level >= 15:
            await ctx.reply("The card to upgrade is maxed out already!")

        upgr_card = r.card(upgraded.name)
        destr_card = r.card(destroyed.name)
        if upgr_card.rarity != destr_card.rarity or upgraded.level != destroyed.level:
            await ctx.reply("Both cards have to be the same level and rarity!")
            return

        player = db.Player.get_by_id(a.id)
        upgrade_cost = math.floor(((upgraded.level + 1) ** 2) * 10)
        if player.coins < upgrade_cost:
            await ctx.reply(f"You don't have enough coins to upgrade! ({upgrade_cost} coins)")
            return

        view = Confirm()
        msg = await ctx.reply(
            f"{upgr_card} lv: {upgraded.level}\n"
            f"{destr_card} lv: {destroyed.level}\n"
            f"Upgrading cost {upgrade_cost} {r.ICONS['coin']}.",
            view=view,
        )
        await view.wait()

        if view.value is None:
            await msg.edit(content="Upgrading timed out.", view=None)
            return
        if not view.value:
            await msg.edit(content="Upgrading canceled.", view=None)
            return

        gained_xp = (upgraded.level + 1) * 10
        player.xp += gained_xp
        player.coins -= upgrade_cost
        player.save()
        await u.update_quest(db.QuestType.MERGE_CARDS, 1, ctx)

        upgraded.level += 1
        upgraded.save()
        destroyed.delete_instance()

        embed = discord.Embed(
            title="Card upgraded successfully!",
            description=f"-{upgrade_cost} {r.ICONS['coin']} +{gained_xp} {r.ICONS['exp']}",
            color=discord.Color.green(),
        )
        embed.add_field(
            name=f"You got a {upgr_card } lv: {upgraded.level} from:",
            value=f"{upgr_card} lv: {upgraded.level}\n{destr_card} lv: {destroyed.level}",
        )
        embed.set_thumbnail(url=ctx.author.avatar.url)
        await msg.edit(content=None, embed=embed, view=None)


async def setup(bot):
    await bot.add_cog(Card(bot))
