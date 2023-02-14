import discord
from discord.ui import UserSelect


class BattleSelectMenu(UserSelect["BattleSelect"]):
    def __init__(self, max_players: int):
        super().__init__(
            min_values=1,
            max_values=max_players,
            placeholder="Who do you want to invite?"
        )

    async def callback(self, i: discord.Interaction):
        assert self.view is not None
        if self.view.host in self.values:
            await i.response.send_message(
                "You can't invite yourself!",
                ephemeral=True
            )
            return
        
        self.view.selected = self.values
        await i.response.send_message("Processing...", ephemeral=True)
        self.view.stop()


class BattleSelect(discord.ui.View):
    def __init__(self, host: discord.Member, max_players: int = 5):
        super().__init__()
        self.host = host
        self.add_item(BattleSelectMenu(max_players))
        self.selected = None

    async def interaction_check(self, i: discord.Interaction) -> bool:
        return i.user == self.host
