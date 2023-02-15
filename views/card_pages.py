import discord

from helpers import db_manager as dm
import util as u


class CardPages(discord.ui.View):
    def __init__(
            self,
            user: discord.Member,
            cards: list | None = None,
            per_page: int = 15,
            page: int = 0
    ):
        super().__init__()

        self.user = user
        self.deck_ids = {card[0] for card in dm.get_user_deck(user.id)}
        if cards is None:
            cards = dm.get_user_cards(user.id)
        self.num_cards = len(cards)

        self.per_page = per_page
        self.pages = list(self.chunks(cards, per_page))
        self.page = u.clamp(page, 0, len(self.pages) - 1)

        self.update_buttons()

    def chunks(self, lst: list, n: int):
        """https://stackoverflow.com/questions/312443"""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

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
            c_str = (f"{'**>**' if card[0] in self.deck_ids else ''}"
                    f"[{u.rarity_cost(card[1])}] **{card[1]}**, "
                    f"lv: **{card[2]}**, id: `{card[0]}`")
            all_cards.append(c_str)

        embed = discord.Embed(
            title=f"{self.user.display_name}'s cards:",
            description="\n".join(all_cards),
            color=discord.Color.gold()
        )
        show_start = self.page * self.per_page + 1
        show_end = min(show_start + self.per_page - 1, self.num_cards)
        embed.set_footer(
            text=f"{show_start}-{show_end}/{self.num_cards} cards on page {self.page + 1}"
        )
        return embed

    async def interaction_check(self, i: discord.Interaction):
        if i.user != self.user:
            await i.response.send_message(
                "You must be the command sender to interact with this message.",
                ephemeral=True
            )
            return False

        return True

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.blurple)
    async def prev_page(self, i: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self.update_buttons()
        await i.response.defer()
        await i.edit_original_response(embed=self.page_embed())
        
    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next_page(self, i: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self.update_buttons()
        await i.response.defer()
        await i.edit_original_response(embed=self.page_embed())
