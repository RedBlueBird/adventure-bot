import discord

from helpers import db_manager as dm


class RaidInvite(discord.ui.View):
    def __init__(
            self,
            host: discord.Member,
            invited: list[discord.Member]
    ):
        super().__init__()
        self.host = host
        self.invited = set(invited)
        self.invited.add(host)
        self.joined = {host}
        self.rejected = set()
        self.start = None

    @discord.ui.button(label="Start!", style=discord.ButtonStyle.green)
    async def start_raid(self, i: discord.Interaction, button: discord.ui.Button):
        if i.user != self.host:
            await i.response.send_message(
                "Only the host can start the raid!",
                ephemeral=True
            )
            return

        if len(self.joined) != len(self.invited):
            await i.response.send_message(
                "All invitees have to join the raid first!",
                ephemeral=True
            )
            return

        self.start = True
        await i.response.defer()
        self.stop()

    @discord.ui.button(label="Join", style=discord.ButtonStyle.green)
    async def join(self, i: discord.Interaction, button: discord.ui.Button):
        if i.user in self.joined:
            await i.response.defer()
            return

        id_ = i.user.id
        not_host = id_ != self.host.id
        if not_host and id_ in dm.queues and i.user not in self.rejected:
            await i.response.send_message(
                f"You can't accept the request- you're still {dm.queues[id_]}!",
                ephemeral=True
            )
            return

        self.joined.add(i.user)
        if i.user in self.rejected:
            self.rejected.remove(i.user)
            msg = f"{i.user.mention} rejected the invite at first, but joined anyway."
        else:
            msg = f"{i.user.mention} has joined!"
        await i.response.send_message(msg)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, i: discord.Interaction, button: discord.ui.Button):
        if i.user in self.rejected:
            await i.response.defer()
            return

        if i.user == self.host:
            await i.response.edit_message(
                content="The host canceled the raid.", view=None
            )
            self.start = False
            self.stop()
            return

        self.rejected.add(i.user)
        if i.user in self.joined:
            self.joined.remove(i.user)
            msg = f"{i.user.mention} joined at first, but changed their mind."
        else:
            msg = f"{i.user.mention} rejected the invite."
        await i.response.send_message(msg)

        if len(self.rejected) == len(self.invited) - 1:
            await i.edit_original_response(
                content="Everyone rejected the battle...",
                view=None
            )
            self.start = False
            self.stop()

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user in self.invited:
            await i.response.send_message(
                "You must be invited to interact with this message.",
                ephemeral=True
            )
            return False
        return True
