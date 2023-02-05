import json
import os
import platform
import sys
import pkgutil
import importlib
import typing as t
from types import ModuleType

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db_manager as dm

import exceptions
from util import PREF


def walk_modules(start: str) -> t.Iterator[ModuleType]:
    """Yield imported modules from the bot.cogs subpackage."""
    def on_error(name: str) -> t.NoReturn:
        raise ImportError(name=name)  # pragma: no cover

    # The mock prevents asyncio.get_event_loop() from being called.
    prefix = f"{start}."
    for module in pkgutil.walk_packages([start], prefix, onerror=on_error):
        if not module.ispkg:
            yield importlib.import_module(module.name)


config_path = f"{os.path.realpath(os.path.dirname(__file__))}/config.json"
if not os.path.isfile(config_path):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(config_path) as config_file:
        config = json.load(config_file)


class AdventurerBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self) -> None:
        print(f"Logged in as {bot.user.name}")
        print(f"discord.py API version: {discord.__version__}")
        print(f"Python version: {platform.python_version()}")
        print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        print("-------------------")
        if config["sync_commands_globally"]:
            print("Syncing commands globally...")
            await bot.tree.sync()
            print("Finished syncing!")

    async def on_command_completion(self, ctx: Context) -> None:
        """Executed every time a normal command has been *successfully* executed"""
        full_command_name = ctx.command.qualified_name
        split = full_command_name.split(" ")
        executed_command = str(split[0])
        if ctx.guild is not None:
            print(
                f"Executed {executed_command} command in {ctx.guild.name} "
                f"(ID: {ctx.guild.id}) by {ctx.author} (ID: {ctx.author.id})"
            )
        else:
            print(
                f"Executed {executed_command} command by {ctx.author} "
                f"(ID: {ctx.author.id}) in DMs"
            )
        dm.queues.pop(str(ctx.author.id), None)

    async def on_command_error(self, ctx: Context, error) -> None:
        """Executed every time a normal valid command catches an error."""
        embed = discord.Embed(title="Error!", color=0xE02B2B)
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            hours = hours % 24
            embed = discord.Embed(
                title="Hey, please slow down!",
                description=f"You can use this command again in "
                            f"{f'{round(hours)} hours' if round(hours) > 0 else ''} "
                            f"{f'{round(minutes)} minutes' if round(minutes) > 0 else ''} "
                            f"{f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
                color=0xE02B2B
            )
        elif isinstance(error, exceptions.UserNotOwner):
            # UserNotOwner happens with @checks.is_owner() (or you can manually raise it)
            embed.description = "You're not an owner of the bot!"
        elif isinstance(error, exceptions.UserPreoccupied):
            embed.description = f"You're still {error.action}! " \
                                "If you think this is a bug, please report it [here](https://discord.gg/w2CkRtkj57)!"
        elif isinstance(error, exceptions.UserSkillIssue):
            embed.description = f"You need to be at least level {error.req_lvl} to unlock this command!"
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Error!",
                description="You are missing the permission(s) `" +
                            ", ".join(error.missing_permissions) +
                            "` to execute this command!",
                color=0xE02B2B
            )
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                title="Error!",
                description="I am missing the permission(s) `" +
                            ", ".join(error.missing_permissions) +
                            "` to fully perform this command!",
                color=0xE02B2B
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error!",
                description=str(error).capitalize(),
                color=0xE02B2B
            )
        elif isinstance(error, commands.CommandNotFound):
            return

        dm.queues.pop(str(ctx.author.id), None)
        await ctx.send(embed=embed)
        raise error

    async def setup_hook(self):
        for ext in walk_modules("cogs"):
            name = ext.__name__
            try:
                await bot.load_extension(name)
                print(f"Loaded extension '{name}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                print(f"Failed to load extension {name}\n{exception}")


intents = discord.Intents.default()
intents.message_content = True

bot = AdventurerBot(
    command_prefix=commands.when_mentioned_or(PREF),
    intents=intents,
    help_command=None,
    case_insensitive=True
)
bot.config = config

if __name__ == "__main__":
    dm.init()
    bot.run(config["token"])
