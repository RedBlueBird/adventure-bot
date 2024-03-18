import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks


class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="sync",
        description="Synchronizes the slash commands.",
    )
    @app_commands.describe(scope="The scope of the sync. Can be `global` or `guild`")
    @checks.is_admin()
    async def sync(self, ctx: Context, scope: str) -> None:
        """Synchronizes the slash commands."""

        if scope == "global":
            await ctx.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands have been globally synchronized.",
                color=0x9C84EF,
            )
            await ctx.send(embed=embed)
            return
        elif scope == "guild":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            embed = discord.Embed(
                description="Slash commands have been synchronized in this guild.",
                color=0x9C84EF,
            )
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(description="The scope must be `global` or `guild`.", color=0xE02B2B)
        await ctx.send(embed=embed)

    @commands.command(
        name="unsync",
        description="Unsynchronizes the slash commands.",
    )
    @app_commands.describe(scope="The scope of the sync. Can be `global` or `guild`")
    @checks.is_admin()
    async def unsync(self, ctx: Context, scope: str) -> None:
        """Unsyncs the slash commands."""

        if scope == "global":
            ctx.bot.tree.clear_commands(guild=None)
            await ctx.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands have been globally unsynchronized.",
                color=0x9C84EF,
            )
            await ctx.send(embed=embed)
            return
        elif scope == "guild":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            embed = discord.Embed(
                description="Slash commands have been unsynchronized in this guild.",
                color=0x9C84EF,
            )
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(description="The scope must be `global` or `guild`.", color=0xE02B2B)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="load",
        description="Load a cog",
    )
    @app_commands.describe(cog="The name of the cog to load")
    @checks.is_admin()
    async def load(self, ctx: Context, cog: str) -> None:
        """
        The bot will load the given cog.
        :param cog: The name of the cog to load.
        """
        try:
            await self.bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            embed = discord.Embed(
                title="Error!",
                description=f"Couldn't load the `{cog}` cog.\n{type(e).__name__}: {e}",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(
            title="Load",
            description=f"Successfully loaded the `{cog}` cog.",
            color=0x9C84EF,
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="unload",
        description="Unloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to unload")
    @checks.is_admin()
    async def unload(self, ctx: Context, cog: str) -> None:
        """The bot will unload the given cog."""
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
        except Exception as e:
            embed = discord.Embed(
                title="Error!",
                description=f"Couldn't unload the `{cog}` cog.\n{type(e).__name__}: {e}",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(
            title="Unload",
            description=f"Successfully unloaded the `{cog}` cog.",
            color=0x9C84EF,
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="reload",
        description="Reloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to reload")
    @checks.is_admin()
    async def reload(self, ctx: Context, cog: str) -> None:
        """The bot will reload the given cog."""
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
        except Exception as e:
            embed = discord.Embed(
                title="Error!",
                description=f"Couldn't reload the `{cog}` cog.\n{type(e).__name__}: {e}",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(
            title="Reload",
            description=f"Successfully reloaded the `{cog}` cog.",
            color=0x9C84EF,
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Owner(bot))
