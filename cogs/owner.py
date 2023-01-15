import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks


class Owner(commands.Cog, name="owner"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="sync",
        description="Synchronizes the slash commands.",
    )
    @checks.is_owner()
    async def sync(self, ctx: Context) -> None:
        """Synchronizes the slash commands."""
        await ctx.bot.tree.sync()
        await ctx.send(embed=discord.Embed(
            title="Slash Commands Sync",
            description="Slash commands have been globally synchronized.",
            color=0x9C84EF
        ))

    @commands.command(
        name="unsync",
        description="Unsynchonizes the slash commands.",
    )
    @checks.is_owner()
    async def unsync(self, ctx: Context) -> None:
        """Unsyncs the slash commands."""

        ctx.bot.tree.clear_commands(guild=ctx.guild)
        await ctx.bot.tree.sync()
        await ctx.send(embed=discord.Embed(
            title="Slash Commands Unsync",
            description="Slash commands have been globally unsynchronized.",
            color=0x9C84EF
        ))

    @commands.hybrid_command(
        name="load",
        description="Load a cog",
    )
    @app_commands.describe(cog="The name of the cog to load")
    @checks.is_owner()
    async def load(self, ctx: Context, cog: str) -> None:
        """
        The bot will load the given cog.
        :param cog: The name of the cog to load.
        """
        try:
            await self.bot.load_extension(f"cogs.{cog}")
        except:
            embed = discord.Embed(
                title="Error!",
                description=f"Could not load the `{cog}` cog.",
                color=0xE02B2B
            )
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(
            title="Load",
            description=f"Successfully loaded the `{cog}` cog.",
            color=0x9C84EF
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="unload",
        description="Unloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to unload")
    @checks.is_owner()
    async def unload(self, ctx: Context, cog: str) -> None:
        """
        The bot will unload the given cog.
        :param cog: The name of the cog to unload.
        """
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                title="Error!",
                description=f"Could not unload the `{cog}` cog.",
                color=0xE02B2B
            )
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(
            title="Unload",
            description=f"Successfully unloaded the `{cog}` cog.",
            color=0x9C84EF
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="reload",
        description="Reloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to reload")
    @checks.is_owner()
    async def reload(self, ctx: Context, cog: str) -> None:
        """
        The bot will reload the given cog.
        :param cog: The name of the cog to reload.
        """
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
        except Exception as e:
            embed = discord.Embed(
                title="Error!",
                description=f"Could not reload the `{cog}` cog.",
                color=0xE02B2B
            )
            await ctx.send(embed=embed)
            print(e)
            return
        embed = discord.Embed(
            title="Reload",
            description=f"Successfully reloaded the `{cog}` cog.",
            color=0x9C84EF
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="shutdown",
        description="Make the bot shutdown.",
    )
    @checks.is_owner()
    async def shutdown(self, ctx: Context) -> None:
        """Shuts down the bot."""
        embed = discord.Embed(
            description="Shutting down. Bye! :wave:",
            color=0x9C84EF
        )
        await ctx.send(embed=embed)
        await self.bot.close()

    @commands.hybrid_command(
        name="say",
        description="The bot will say anything you want.",
    )
    @app_commands.describe(message="The message that should be repeated by the bot")
    @checks.is_owner()
    async def say(self, ctx: Context, *, message: str) -> None:
        """
        The bot will say anything you want.
        :param message: The message that should be repeated by the bot.
        """
        await ctx.send(message)

    @commands.hybrid_command(
        name="embed",
        description="The bot will say anything you want, but within embeds.",
    )
    @app_commands.describe(message="The message that should be repeated by the bot")
    @checks.is_owner()
    async def embed(self, ctx: Context, *, message: str) -> None:
        """
        The bot will say anything you want, but using embeds.
        :param message: The message that should be repeated by the bot.
        """
        embed = discord.Embed(
            description=message,
            color=0x9C84EF
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Owner(bot))
