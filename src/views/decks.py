import discord

import db
import resources as r


class DeckButton(discord.ui.Button["Decks"]):
    def __init__(self, slot: int):
        super().__init__(
            label=f"Deck {slot}", style=discord.ButtonStyle.blurple, row=(slot - 1) // 3
        )
        self.slot = slot

    async def callback(self, i: discord.Interaction):
        assert self.view is not None
        self.view.slot = self.slot
        await i.response.edit_message(embed=self.view.deck_embed())


class OverviewButton(discord.ui.Button["Decks"]):
    def __init__(self, row: int):
        super().__init__(label="Overview", style=discord.ButtonStyle.gray, row=row)

    async def callback(self, i: discord.Interaction):
        await i.response.edit_message(embed=self.view.overview_embed())


class Decks(discord.ui.View):
    def __init__(self, user: discord.Member, slot: int = 0):
        super().__init__()

        assert 0 <= slot <= 6
        self.user = user
        self.db_user = db.Player.get_by_id(user.id)
        self.user_slot = self.db_user.deck
        self.slot = self.user_slot if slot == 0 else slot

        self.unlocked = 0
        for s in range(1, 6 + 1):
            if self.db_user.level >= r.DECK_LVL_REQ[s]:
                self.unlocked += 1
                self.add_item(DeckButton(s))
        self.add_item(OverviewButton((self.unlocked + 2) // 3))

    def overview_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"{self.user.display_name}'s decks",
            description=f"`{r.PREF}deck #` to view a specific deck",
            color=discord.Color.gold(),
        )

        for s in range(1, 6 + 1):
            name = f"**Deck {s}**"
            if s == self.user_slot:
                name += " - Selected"

            if s > self.unlocked:
                value = f"Unlocked at level {r.DECK_LVL_REQ[s]}"
            else:
                value = f"{len(db.get_deck(self.user.id, s))}/12 cards"

            embed.add_field(name=name, value=value, inline=False)

        embed.set_thumbnail(url=self.user.avatar.url)
        return embed

    def deck_embed(self) -> discord.Embed:
        deck = db.get_deck(self.user.id, self.slot)
        db.sort_cards(deck, self.db_user.card_order)
        cards = []
        total_energy = 0
        for card in deck:
            c_info = r.card(card.name)
            cards.append(f"{c_info}, lv: **{card.level}**, id: `{card.id}`")
            total_energy += c_info.cost

        if self.slot == self.user_slot:
            select_msg = ""
        else:
            select_msg = f"\n`{r.PREF}select {self.slot}` to modify this deck"

        embed = discord.Embed(
            title=f"{self.user.display_name}'s Deck #{self.slot}:",
            description=f"`{r.PREF}decks` to display an overview of all decks{select_msg}\n\n"
            + "\n".join(cards),
            color=discord.Color.gold(),
        )
        embed.set_thumbnail(url=self.user.avatar.url)
        if not deck:
            embed.add_field(
                name="You don't have any cards in your deck!",
                value=f"`{r.PREF}add (card_id)` to start adding cards!",
            )
        return embed
