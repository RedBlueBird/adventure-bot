from discord.ext import commands


class UserNotAdmin(commands.CheckFailure):
    """Thrown when a user is attempting something, but is not an owner of the bot."""

    def __init__(self, message="User is not an owner of the bot!"):
        self.message = message
        super().__init__(self.message)


class UserNotRegistered(commands.CheckFailure):
    """Thrown when a user attempts to perform an activity without registering first."""

    def __init__(self, message: str = "User isn't registered in the bot!"):
        self.message = message
        super().__init__(self.message)


class UserPreoccupied(commands.CheckFailure):
    """Thrown when a user tries to perform an activity will still in another one."""

    def __init__(self, activity: str = "doing something"):
        self.action = activity
        self.message = f"User is currently {activity}!"
        super().__init__(self.message)


class UserSkillIssue(commands.CheckFailure):
    def __init__(self, req_lvl: int):
        self.req_lvl = req_lvl
        self.message = f"User is not a high enough level!"
        super().__init__(self.message)
