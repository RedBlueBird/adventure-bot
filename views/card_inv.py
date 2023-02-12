import discord

from helpers import db_manager as dm
import util as u


def chunks(lst: list, n: int):
    """https://stackoverflow.com/questions/312443"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class CardPages(discord.ui.View):
    def __init__(
            self, user: discord.Member,
            page_len: int = 15, page: int = 0,
            override: list | None = None
    ):
        super().__init__()

        self.user = user
        self.deck_ids = {card[0] for card in dm.get_user_deck(user.id)}
        cards = dm.get_user_cards(user.id) if override is None else override
        self.card_amt = len(cards)

        self.pages = list(chunks(cards, page_len))
        self.page_len = page_len
        self.page = u.clamp(page, 0, len(self.pages) - 1)

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.blurple)
    async def prev_page(self, i: discord.Interaction, button: discord.ui.Button):
        await i.response.defer()
        if self.page == 0:
            return
        self.page -= 1
        await i.edit_original_response(embed=self.page_embed())
        
    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next_page(self, i: discord.Interaction, button: discord.ui.Button):
        await i.response.defer()
        if self.page == len(self.pages) - 1:
            return
        self.page += 1
        await i.edit_original_response(embed=self.page_embed())

    def page_embed(self) -> discord.Embed:
        all_cards = []
        for card in self.pages[self.page]:
            c_str = ("**>**" if card[0] in self.deck_ids else "") + \
                    f"[{u.rarity_cost(card[1])}] **{card[1]}**, " \
                    f"lv: **{card[2]}**, id: `{card[0]}`"
            all_cards.append(c_str)

        embed = discord.Embed(
            title=f"{self.user.display_name}'s cards:",
            description="\n".join(all_cards),
            color=discord.Color.gold()
        )
        show_start = self.page * self.page_len + 1
        show_end = min(show_start + self.page_len - 1, self.card_amt)
        embed.set_footer(
            text=f"{show_start}-{show_end}/{self.card_amt} cards on page {self.page + 1}"
        )
        return embed
