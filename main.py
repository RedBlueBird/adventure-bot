import json
import os
import platform
import sys
import pkgutil
import importlib
import typing as t
import math
import random
import asyncio
from types import ModuleType

import discord
from discord.ext import commands
from discord.ext.commands import Context

import util as u
from helpers import db_manager as dm
import cogs

import exceptions
from util import PREF


def walk_modules(start: str) -> t.Iterator[ModuleType]:
    """Yield imported modules from the bot.cogs subpackage."""

    def on_error(name: str) -> t.NoReturn:
        raise ImportError(name=name)  # pragma: no cover

    # The mock prevents asyncio.get_event_loop() from being called.
    # The first parameter has to be cogs.__path__ otherwise when main.py executed through
    # absolute path  no cogs will be appended
    prefix = f"{start}."
    for module in pkgutil.walk_packages(cogs.__path__, prefix, onerror=on_error):
        if not module.ispkg:
            yield importlib.import_module(module.name)


config_path = dirname = os.path.join(os.path.dirname(__file__), "config.json")
if not os.path.isfile(config_path):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(config_path) as config_file:
        config = json.load(config_file)


class AdventurerBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user.name}")
        print(f"discord.py API version: {discord.__version__}")
        print(f"Python version: {platform.python_version()}")
        print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        print("-------------------")
        if config["sync_commands_globally"]:
            print("Syncing commands globally...")
            await self.tree.sync()
            print("Finished syncing!")
        game = discord.Game(f"{len(self.guilds)} Servers")
        await self.change_presence(status=discord.Status.online, activity=game)

    async def on_command(self, ctx: Context) -> None:
        if ctx.author.bot:
            return

        # region Check user level up
        a = ctx.author
        user_level = dm.get_user_level(a.id)
        if not user_level:
            return
        user_exp = dm.get_user_exp(a.id)

        if user_exp > u.level_xp(user_level) and user_level < 30:
            level_msg = []
            if (user_level + 1) % 2 == 0:
                add_hp = round(
                    (u.SCALE[1] ** math.floor((user_level + 1) / 2) -
                     u.SCALE[1] ** math.floor(user_level / 2)) * 100 * u.SCALE[0]
                )
                level_msg.append(f"Max health +{add_hp}!")

            # At levels 17 and 27, the user gets a week of free premium.
            if user_level + 1 in [17, 27]:
                dm.set_user_premium(a.id, user_premium_date + dt.timedelta(days=7))

            if u.LEVELS[user_level - 1]:
                level_msg.extend(u.LEVELS[user_level - 1].format(u.PREF).split("\n"))

            embed = discord.Embed(
                title=f"Congratulations {a.name}!",
                description=None,
                color=discord.Color.green()
            )
            embed.add_field(
                name=f"You're now level {user_level + 1}!",
                value=f"+{user_level * 50} {u.ICON['coin']} \n"
                      f"+{math.ceil((user_level + 1) / 5) + 1} {u.ICON['gem']} \n"
                      "```» " + "\n\n» ".join(level_msg) + "```"
            )
            embed.set_thumbnail(url=a.avatar.url)
            await ctx.channel.send(embed=embed)

            dm.set_user_exp(a.id, user_exp - u.level_xp(user_level))
            dm.set_user_level(a.id, user_level + 1)
            dm.set_user_coin(a.id, dm.get_user_coin(a.id) + user_level * 50)
            dm.set_user_coin(a.id, dm.get_user_gem(a.id) + math.ceil((user_level + 1) / 5) + 1)
        # endregion

        # region Quest Completion Check (scuffed)
        quests = dm.get_user_quest(a.id).split(",")
        if len(quests) > 1:
            quest_com = [
                math.floor(int(quests[x].split(".")[2]) / u.quest_index(quests[x])[0] * 100)
                for x in range(len(quests) - 1)
            ]
            for x in range(len(quests) - 1):
                if quest_com[x] >= 100:
                    quest = u.quest_index(quests[x])
                    embed = discord.Embed(
                        title=f"QUEST COMPLETE {a.name}!",
                        description=None,
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name=f"**{quest[2]} {u.quest_str_rep(quests[x].split('.')[1], quest[0])}**",
                        value=f"**+{' '.join(quest[1::2])} +{quest[4]} {u.ICON['exp']}**",
                        # " +1{u.icon['token']}**",
                        inline=False
                    )
                    embed.set_thumbnail(url=a.avatar.url)
                    await ctx.channel.send(embed=embed)

                    gained = [0, 0, quest[4]]  # coin, gem, exp
                    if quest[3] == u.ICON["coin"]:
                        gained[0] += int(quest[1])
                    elif quest[3] == u.ICON["gem"]:
                        gained[1] += int(quest[1])

                    quests.remove(quests[x])
                    dm.set_user_coin(a.id, dm.get_user_coin(a.id) + gained[0])
                    dm.set_user_gem(a.id, dm.get_user_gem(a.id) + gained[1])
                    dm.set_user_exp(a.id, dm.get_user_exp(a.id) + gained[2])
                    dm.set_user_token(a.id, dm.get_user_token(a.id) + 1)
                    dm.set_user_quest(a.id, ','.join(quests))
                    break
        # endregion

        # region Gold Spawn Logic
        if random.randint(1, 25) == 1:
            if random.randint(1, 30) == 1:
                amt = random.randint(250, 500)
            else:
                amt = random.randint(50, 100)

            spawn_msg = await ctx.channel.send(embed=discord.Embed(
                title=f"A bag of gold showed up out of nowhere!",
                description=f"Quick! Type `{u.PREF}collect {amt} coins` to collect them! \n"
                            f"They'll be gone in 10 minutes!",
                color=discord.Color.green()
            ))

            try:
                rep = await self.wait_for(
                    "message", timeout=600.0,
                    check=lambda m:
                    m.content.lower().startswith(f"{u.PREF}collect {amt} coins") and
                    m.channel == spawn_msg.channel
                )
                mention = rep.author.mention

                user_coin = dm.get_user_coin(a.id)
                if user_coin:
                    dm.set_user_coin(a.id, user_coin + amt)
                    if random.randint(1, 100) == 1:
                        dm.set_user_gem(a.id, dm.get_user_gem(a.id) + 1)
                        msg = f"{mention}, you got {amt} {u.ICON['coin']} and 1 {u.ICON['gem']} as well!"
                    else:
                        msg = f"{mention}, you got {amt} {u.ICON['coin']}!"
                else:
                    msg = f"{mention}, you have to register in this bot first with `{u.PREF}register`! \n"

                await rep.channel.send(msg)
            except asyncio.TimeoutError:
                print("No one claimed the bag of coins.")
        # endregion

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
        dm.queues.pop(ctx.author.id, None)

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
            embed.title = "Hold on!"
            embed.description = f"You're still {error.action}! " \
                                "If you think this is a bug, please report it " \
                                "[here](https://discord.gg/w2CkRtkj57)!"
        elif isinstance(error, exceptions.UserSkillIssue):
            embed.description = f"You need to be at least level {error.req_lvl} to unlock this command!"
        elif isinstance(error, commands.MissingPermissions):
            embed.description = "You are missing the permission(s) `" + \
                                ", ".join(error.missing_permissions) + \
                                "` to execute this command!"
        elif isinstance(error, commands.BotMissingPermissions):
            embed.description = "I am missing the permission(s) `" + \
                                ", ".join(error.missing_permissions) + \
                                "` to fully perform this command!"
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.description = str(error).capitalize()
        elif isinstance(error, commands.CommandNotFound):
            return
        else:
            embed.description = f"{type(error).__name__}: {error}"

        dm.queues.pop(ctx.author.id, None)
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
