import discord

from helpers import db_manager as dm


class TeamButton(discord.ui.Button["PvpInvite"]):
    def __init__(self, team: int):
        super().__init__(
            label=f"Team {team}",
            style=discord.ButtonStyle.blurple,
            row=1 + (team - 1) // 3
        )
        self.team = team

    async def callback(self, i: discord.Interaction):
        assert self.view is not None

        id_ = i.user.id
        not_host = id_ != self.view.host.id
        if not_host and id_ in dm.queues and i.user not in self.view.rejected:
            await i.response.send_message(
                f"You can't accept the request- you're still {dm.queues[id_]}!",
                ephemeral=True
            )
            return

        if self.view.user_team.get(i.user, None) == self.team:
            await i.response.defer()
            return

        if i.user in self.view.user_team:
            self.view.teams[self.view.user_team[i.user]].remove(i.user)

        self.view.user_team[i.user] = self.team
        self.view.teams[self.team].add(i.user)

        if i.user in self.view.rejected:
            self.view.rejected.remove(i.user)
            await i.response.send_message(
                f"{i.user} rejected at first, but joined again anyway on team {self.team}."
            )
        else:
            await i.response.send_message(f"{i.user} has joined team {self.team}!")


class PvpInvite(discord.ui.View):
    def __init__(
            self,
            host: discord.Member,
            invited: list[discord.Member],
            team_num: int
    ):
        super().__init__()
        self.host = host
        self.invited = set(invited)
        self.invited.add(host)  # just to make sure
        self.rejected = set()

        self.teams: dict[int, set[discord.Member]] = {}
        for team in range(1, team_num + 1):
            self.teams[team] = set()
            self.add_item(TeamButton(team))
        self.user_team: dict[discord.Member, int] = {}
        self.start = None

    @discord.ui.button(label="Start!", style=discord.ButtonStyle.green)
    async def start_pvp(self, i: discord.Interaction, button: discord.ui.Button):
        if i.user != self.host:
            await i.response.send_message(
                "Only the host can start the battle!",
                ephemeral=True
            )
            return

        if self.host not in self.user_team:
            await i.response.send_message(
                "The host has to join a team first!",
                ephemeral=True
            )

        if len(self.user_team) < 2:
            await i.response.send_message(
                "At least two people have to join the battle!",
                ephemeral=True
            )
            return

        if sum(bool(t) for t in self.teams.values()) < 2:
            await i.response.send_message(
                "There have to be at least two teams for the battle to start!",
                ephemeral=True
            )
            return

        self.start = True
        await i.response.defer()
        self.stop()

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, i: discord.Interaction, button: discord.ui.Button):
        if i.user in self.rejected:
            await i.response.defer()
            return

        if i.user == self.host:
            await i.response.edit_message(
                content="The host cancelled the battle.", view=None
            )
            self.stop()
            return

        if i.user in self.user_team:
            team = self.user_team.pop(i.user)
            self.teams[team].remove(i.user)
            self.rejected.add(i.user)
            await i.response.send_message(
                f"{i.user.mention} joined, but then left team {team}..."
            )
        else:
            self.rejected.add(i.user)
            await i.response.send_message(f"{i.user} rejected the battle...")
            if len(self.rejected) == len(self.invited) - 1:
                await i.response.edit_message(
                    content="Everyone rejected the battle...",
                    view=None
                )
                self.stop()

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user not in self.invited:
            await i.response.send_message(
                "You must be invited to interact with this message.",
                ephemeral=True
            )
            return False
        return True
