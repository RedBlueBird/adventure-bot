import discord


class Player:
    def __init__(
            self,
            level: int = 1, user: discord.Member = None,
            team: int = 0, id_: int = 0, deck=None
    ):
        self.team = team
        self.icon = None
        self.id = id_
        self.user = user
        self.level = level
        self.hp = 100  # u.level_hp(level)
        self.max_hp = 100  # u.level_hp(level)
        self.block = 0
        self.stamina = 30
        self.stored_energy = 2
        self.deck = deck
        self.hand_size = 4
        self.dialogue = []
        self.dead = False
        self.flee = False
        self.skip = False
        self.crit = 0
        self.inbox = {1:[],2:[],3:[]}
