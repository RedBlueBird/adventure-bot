import discord
import discord.ui as ui


class AdventureTemplate(ui.View):
    def __init__(self, user: discord.Member):
        super().__init__()
        self.user = user

    @ui.button(label="Exit", style=discord.ButtonStyle.red, row=4)
    async def exit(self, i: discord.Interaction, button: ui.Button):
        await i.response.defer()
        self.stop()

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user != self.user:
            await i.response.send_message(
                "You aren't the explorer here!",
                ephemeral=True
            )
            return False
        return True
