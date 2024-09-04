import datetime
import importlib
import logging
import os
import pkgutil
import platform
import typing as t
from types import ModuleType

import discord
from discord.ext import commands
from discord.ext.commands import Context

import cogs
import db
import env
import exceptions
import resources as r
from helpers import util as u


def walk_modules(start: str) -> t.Iterator[ModuleType]:
    """Yield imported modules from the bot.cogs subpackage."""

    def on_error(name: str) -> t.NoReturn:
        raise ImportError(name=name)  # pragma: no cover

    """
    The mock prevents asyncio.get_event_loop() from being called.
    The first parameter has to be cogs.__path__
    otherwise when main.py executed through absolute path no cogs will be added
    """
    prefix = f"{start}."
    for module in pkgutil.walk_packages(cogs.__path__, prefix, onerror=on_error):
        if not module.ispkg:
            yield importlib.import_module(module.name)


class AdventurerBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self) -> None:
        logging.info(f"Logged in as {self.user.name}")
        logging.info(f"discord.py API version: {discord.__version__}")
        logging.info(f"Python version: {platform.python_version()}")
        logging.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        logging.info("-------------------")
        if env.SYNC_CMD_GLOBALLY:
            logging.info("Syncing commands globally...")
            await self.tree.sync()
            logging.info("Finished syncing!")
        game = discord.Game(f"{len(self.guilds)} Servers")
        await self.change_presence(status=discord.Status.online, activity=game)

    async def on_command_completion(self, ctx: Context) -> None:
        """Executed every time a normal command has been *successfully* executed"""
        cmd_name = ctx.command.qualified_name
        executed_command = cmd_name.split(" ")[0]
        a = ctx.author
        if ctx.guild is not None:
            logging.info(
                f"Executed {executed_command} command in {ctx.guild.name} "
                f"(ID: {ctx.guild.id}) by {a} (ID: {a.id})"
            )
        else:
            logging.info(f"Executed {executed_command} command by {a} (ID: {a.id}) in DMs")

        db.unlock_user(a.id, cmd_name)

    async def on_command_error(self, ctx: Context, error) -> None:
        """Executed every time a normal valid command catches an error."""
        embed = discord.Embed(title="Error!", color=0xE02B2B)
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="Hey, please slow down!",
                description=(
                    f"You can use this command again in {u.time_converter(int(error.retry_after))}."
                ),
                color=0xE02B2B,
            )
        elif isinstance(error, exceptions.UserNotAdmin):
            # UserNotOwner happens with @checks.is_admin() (or you can manually raise it)
            embed.description = "You're not an admin of the bot!"
        elif isinstance(error, exceptions.UserPreoccupied):
            embed.title = "Hold on!"
            embed.description = (
                f"You're still {error.action}! "
                "If you think this is a bug, please report it "
                "[here](https://discord.gg/w2CkRtkj57)!"
            )
        elif isinstance(error, exceptions.UserSkillIssue):
            embed.description = (
                f"You need to be at least level {error.req_lvl} to unlock this command!"
            )
        elif isinstance(error, commands.MissingPermissions):
            embed.description = (
                "You're missing the permission(s) `"
                + ", ".join(error.missing_permissions)
                + "` to execute this command!"
            )
        elif isinstance(error, commands.BotMissingPermissions):
            embed.description = (
                "I'm missing the permission(s) `"
                + ", ".join(error.missing_permissions)
                + "` to fully perform this command!"
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.description = str(error).capitalize()
        elif isinstance(error, commands.CommandNotFound):
            return
        else:
            embed.description = f"{type(error).__name__}:\n```{error}```"

        if not isinstance(error, exceptions.UserPreoccupied):
            db.unlock_user(ctx.author.id, ctx.command.qualified_name)
        await ctx.send(embed=embed)
        raise error

    async def setup_hook(self):
        for ext in walk_modules("cogs"):
            name = ext.__name__
            try:
                await bot.load_extension(name)
                logging.info(f"Loaded extension '{name}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                logging.error(f"Failed to load extension {name}\n{exception}")


intents = discord.Intents.default()
intents.message_content = True

bot = AdventurerBot(
    command_prefix=commands.when_mentioned_or(r.PREF),
    intents=intents,
    help_command=None,
    case_insensitive=True,
)

if __name__ == "__main__":
    fh = logging.FileHandler(f"logs/{datetime.date.today().strftime('%d_%m_%Y.txt')}")
    sh = logging.StreamHandler()
    logging.basicConfig(handlers=[fh, sh], level=logging.INFO)
    bot.run(env.BOT_TOKEN)
