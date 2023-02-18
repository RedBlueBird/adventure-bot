import discord

from helpers import db_manager as dm
import util as u


class DeckButton(discord.ui.Button["Decks"]):
    def __init__(self, slot: int, row: int):
        super().__init__(label=f"Deck {slot}", style=discord.ButtonStyle.blurple, row=row)
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
        self.user_slot = dm.get_user_deck_slot(user.id)
        self.slot = self.user_slot if slot == 0 else slot

        self.unlocked = 0
        level = dm.get_user_level(user.id)
        for slot in range(1, 6 + 1):
            if level >= u.DECK_LVL_REQ[slot]:
                self.unlocked += 1
                self.add_item(DeckButton(slot, (slot-1)//3))
        self.children[0].row = (self.unlocked+2)//3

    @discord.ui.button(label="Overview", style=discord.ButtonStyle.gray)
    async def overview(self, i: discord.Interaction, button: discord.ui.Button):
        await i.response.edit_message(embed=self.overview_embed())

    def overview_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"{self.user.display_name}'s decks",
            description=f"`{u.PREF}deck #` to view a specific deck",
            color=discord.Color.gold()
        )

        for slot in range(1, 6 + 1):
            name = f"**Deck {slot}**"
            if slot == self.user_slot:
                name += " - Selected"

            if slot > self.unlocked:
                value = f"Unlocked at level {u.DECK_LVL_REQ[slot]}"
            else:
                deck_count = dm.get_user_deck_count(self.user.id, slot)
                value = f"{deck_count}/12 cards"

            embed.add_field(name=name, value=value, inline=False)

        embed.set_thumbnail(url=self.user.avatar.url)
        return embed

    def deck_embed(self) -> discord.Embed:
        deck = dm.get_user_deck(self.user.id, self.slot)
        cards = []
        total_energy = 0
        for card in deck:
            card_str = f"[{u.rarity_cost(card[1])}] **{card[1]}**, lv: **{card[2]}**, id: `{card[0]}` "
            cards.append(card_str)
            total_energy += u.cards_dict(card[2], card[1])["cost"]

        if self.slot == self.user_slot:
            select_msg = ""
        else:
            select_msg = f"\n`{u.PREF}select {self.slot}` to modify this deck"

        embed = discord.Embed(
            title=f"{self.user.display_name}'s Deck #{self.slot}:",
            description=f"`{u.PREF}decks` to display an overview of all decks{select_msg}\n\n" +
                        "\n".join(cards),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=self.user.avatar.url)
        if not deck:
            embed.add_field(
                name="You don't have any cards in your deck!",
                value=f"`{u.PREF}add (card_id)` to start adding cards!"
            )
        return embed
