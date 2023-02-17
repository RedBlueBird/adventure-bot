import discord

from helpers import db_manager as dm
import util as u


class DeckButton(discord.ui.Button["Decks"]):
    def __init__(self, slot: int):
        super().__init__(label=f"Deck {slot}", style=discord.ButtonStyle.blurple, row=0)
        self.slot = slot

    async def callback(self, i: discord.Interaction):
        assert self.view is not None
        self.view.slot = self.slot
        await i.response.edit_message(embed=self.view.deck_embed())


class Decks(discord.ui.View):
    def __init__(self, user: discord.Member, slot: int = 0):
        super().__init__()

        assert 0 <= slot <= 6
        self.user = user
        self.u_slot = dm.get_user_deck_slot(user.id)
        self.slot = self.u_slot if slot == 0 else slot

        level = dm.get_user_level(user.id)
        for s in range(1, 6 + 1):
            if level >= u.DECK_LVL_REQ[s]:
                self.add_item(DeckButton(s))

    @discord.ui.button(label="All Decks", style=discord.ButtonStyle.gray, row=1)
    async def all(self, i: discord.Interaction, button: discord.ui.Button):
        await i.response.edit_message(embed=self.decklist_embed())

    def decklist_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"{self.user.display_name}'s decks",
            description=f"`{u.PREF}deck #` to view a specific deck",
            color=discord.Color.gold()
        )

        for s in range(6):
            name = f"**Deck {s + 1}**"
            if dm.get_user_deck_slot(self.user.id) == s + 1:
                name += " - selected"

            if dm.get_user_level(self.user.id) < u.DECK_LVL_REQ[s + 1]:
                card_info = f"Unlocked at level {u.DECK_LVL_REQ[s + 1]}"
            else:
                deck_lens = dm.get_user_deck_count(self.user.id, s + 1)
                card_info = f"{deck_lens}/12 cards"

            embed.add_field(name=name, value=card_info, inline=False)

        embed.set_thumbnail(url=self.user.avatar.url)
        return embed

    def deck_embed(self) -> discord.Embed:
        deck = dm.get_user_deck(self.user.id, self.slot)
        all_cards = []
        tot_energy = 0
        for x in deck:
            card = f"[{u.rarity_cost(x[1])}] **{x[1]}**, lv: **{x[2]}**, id: `{x[0]}` "
            all_cards.append(card)
            tot_energy += u.cards_dict(x[2], x[1])["cost"]

        mod_msg = "" if self.slot == self.u_slot else f"\n`{u.PREF}select {self.slot}` to modify this deck"
        embed = discord.Embed(
            title=f"{self.user.display_name}'s Deck #{self.slot}:",
            description=f"`{u.PREF}decklist` to display all your decks{mod_msg}\n\n" +
                        "\n".join(all_cards),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=self.user.avatar.url)
        if not deck:
            embed.add_field(
                name="You don't have any cards in your deck!",
                value=f"`{u.PREF}add (card_id)` to start adding cards!"
            )
        return embed
