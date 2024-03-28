import discord


class Confirm(discord.ui.View):
    def __init__(self, user: discord.Member, confirm: str = "Confirm", cancel: str = "Cancel"):
        super().__init__()
        self.value = None
        self.user = user
        self.children[0].label = confirm
        self.children[1].label = cancel

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, i: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await i.response.defer()
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, i: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await i.response.defer()
        self.stop()

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user.id != self.user.id:
            await i.response.send_message("You can't interact with this!", ephemeral=True)
            return False
        return True
