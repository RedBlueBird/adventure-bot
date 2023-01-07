import asyncio
import json
import os
import platform
import sys

import aiosqlite
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context

from helpers import db_manager, asset_manager

import exceptions

config_path = f"{os.path.realpath(os.path.dirname(__file__))}/config.json"
if not os.path.isfile(config_path):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(config_path) as config_file:
        config = json.load(config_file)

intents = discord.Intents.default()
intents.message_content = True

bot = Bot(command_prefix=commands.when_mentioned_or(config["prefix"]), 
          intents=intents, 
          help_command=None,
          case_insensitive=True)


async def init_db():
    async with aiosqlite.connect(f"{os.path.realpath(os.path.dirname(__file__))}/database/database.db") as db:
        with open(f"{os.path.realpath(os.path.dirname(__file__))}/database/schema.sql") as file:
            await db.executescript(file.read())
        await db.commit()


bot.config = config


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user.name}")
    print(f"discord.py API version: {discord.__version__}")
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    print("-------------------")
    if config["sync_commands_globally"]:
        print("Syncing commands globally...")
        await bot.tree.sync()


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user or message.author.bot:
        return
    print('called main')
    await bot.process_commands(message)


@bot.event
async def on_command_completion(ctx: Context) -> None:
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


@bot.event
async def on_command_error(ctx: Context, error) -> None:
    """
    The code in this event is executed every time a normal valid command catches an error
    :param ctx: The context of the normal command that failed executing.
    :param error: The error that has been faced.
    """
    if isinstance(error, commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        hours = hours % 24
        embed = discord.Embed(
            title="Hey, please slow down!",
            description=f"You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
    elif isinstance(error, exceptions.UserBlacklisted):
        """
        The code here will only execute if the error is an instance of
        'UserBlacklisted', which can occur when using the @checks.not_blacklisted()
        check in your command, or you can raise the error by yourself.
        """
        embed = discord.Embed(
            title="Error!",
            description="You are blacklisted from using the bot.",
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
    elif isinstance(error, exceptions.UserNotOwner):
        """
        Same as above, just for the @checks.is_owner() check.
        """
        embed = discord.Embed(
            title="Error!",
            description="You are not the owner of the bot!",
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="Error!",
            description="You are missing the permission(s) `" + ", ".join(
                error.missing_permissions) + "` to execute this command!",
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(
            title="Error!",
            description="I am missing the permission(s) `" + ", ".join(
                error.missing_permissions) + "` to fully perform this command!",
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Error!",
            # We need to capitalize because the command arguments have no capital letter in the code.
            description=str(error).capitalize(),
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
    raise error


async def load_cogs() -> None:
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                await bot.load_extension(f"cogs.{extension}")
                print(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                print(f"Failed to load extension {extension}\n{exception}")


if __name__ == "__main__":
    db_manager.init()
    asset_manager.init(bot)
    asyncio.run(init_db())
    asyncio.run(load_cogs())
    bot.run(config["token"])
