import discord
from discord.ui import UserSelect

import db


class SelectMenu(UserSelect["Select"]):
    def __init__(self, min_players: int, max_players: int):
        # min_players doesn't include the host
        super().__init__(
            min_values=min_players,
            max_values=max_players,
            placeholder="Who do you want to invite?",
        )

    async def callback(self, i: discord.Interaction):
        assert self.view is not None
        if self.view.host in self.values:
            await i.response.send_message("You can't invite yourself!", ephemeral=True)
            return

        for u in self.values:
            if not db.Player.select().where(db.Player.id == u.id).exists():
                await i.response.send_message(
                    f"{u.mention} doesn't exist in the bot yet!", ephemeral=True
                )
                return

            action = db.get_user_action(u.id)
            if action is not None and u.id != self.view.host.id:
                await i.response.send_message(f"{u.mention} is still {action}!", ephemeral=True)
                return

        self.view.selected = self.values
        self.view.quit = False
        await i.response.defer()
        self.view.stop()


class Select(discord.ui.View):
    def __init__(self, host: discord.Member, min_players: int = 1, max_players: int = 5):
        super().__init__()
        self.host = host

        quit_select = self.quit_select
        self.remove_item(quit_select)
        self.add_item(SelectMenu(min_players, max_players))
        self.add_item(quit_select)

        self.selected: list[discord.Member] | None = None
        self.quit: bool | None = None

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user != self.host:
            await i.response.send_message(
                "You must be the host to interact with this message.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.red)
    async def quit_select(self, i: discord.Interaction, button: discord.ui.Button):
        self.quit = True
        self.stop()
