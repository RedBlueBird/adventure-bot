import discord

import db
from helpers import util as u, resources as r


def chunks(lst: list, n: int):
    """https://stackoverflow.com/questions/312443"""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


class CardPages(discord.ui.View):
    def __init__(
        self,
        author: discord.Member,
        user: discord.Member,
        cards: list[db.Card] | None = None,
        per_page: int = 15,
        page: int = 0,
    ):
        super().__init__()

        player = db.Player.get_by_id(user.id)

        self.author = author
        self.user = user
        # TODO: order by user preference
        cards = cards if cards is not None else db.Card.select().where(db.Card.owner == player.uid)
        self.num_cards = len(cards)

        self.deck_ids = {c.id for c in db.get_deck(player.uid)}

        self.per_page = per_page
        self.pages = list(chunks(cards, per_page))
        self.page = u.clamp(page, 0, len(self.pages) - 1)

        self.update_buttons()

    def update_buttons(self):
        prev_button: discord.ui.Button = self.children[0]
        next_button: discord.ui.Button = self.children[1]

        if self.page == 0:
            prev_button.disabled = True
        else:
            prev_button.disabled = False

        if self.page == len(self.pages) - 1:
            next_button.disabled = True
        else:
            next_button.disabled = False

    def page_embed(self) -> discord.Embed:
        all_cards = []
        for card in self.pages[self.page]:
            c_info = r.card(card.name)
            c_str = (
                f"{'**>**' if card.id in self.deck_ids else ''}"
                f"{c_info}, lv: {card.level}, id: `{card.id}`"
            )
            all_cards.append(c_str)

        embed = discord.Embed(
            title=f"{self.user.display_name}'s cards:",
            description="\n".join(all_cards),
            color=discord.Color.gold(),
        )
        show_start = self.page * self.per_page + 1
        show_end = min(show_start + self.per_page - 1, self.num_cards)
        embed.set_footer(
            text=f"{show_start}-{show_end}/{self.num_cards} cards on page {self.page + 1}"
        )
        return embed

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user != self.author:
            await i.response.send_message(
                "You must be the command sender to interact with this message.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.blurple)
    async def prev_page(self, i: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self.update_buttons()
        await i.response.edit_message(embed=self.page_embed(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next_page(self, i: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self.update_buttons()
        await i.response.edit_message(embed=self.page_embed(), view=self)
