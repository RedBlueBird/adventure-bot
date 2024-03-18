import os

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers.resources import PREF


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="List all commands the bot has loaded.")
    async def help(self, ctx: Context) -> None:
        embed = discord.Embed(
            title="Help", description="List of available commands:", color=0x9C84EF
        )
        for i in self.bot.cogs:
            cog = self.bot.get_cog(i)
            data = []
            for cmd in cog.get_commands():
                description = cmd.description.partition("\n")[0]
                data.append(f"{PREF}{cmd.name} - {description}")
            help_text = "\n".join(data)
            embed.add_field(name=i.capitalize(), value=f"```{help_text}```", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="links",
        description="Displays an embed containing some official bot info.",
        aliases=["invite", "support", "guild", "supports", "link", "join"],
    )
    async def links(self, ctx: Context) -> None:
        """Displays an embed containing some official bot info."""
        embed = discord.Embed(title="Official Links", description=None, color=discord.Color.green())
        embed.add_field(
            name="Bot Invite",
            value=(
                f"[Link](https://discordapp.com/oauth2/authorize?&client_id={os.environ['APP_ID']}"
                f"&scope=bot+applications.commands&permissions={os.environ['APP_PERMS']})"
            ),
        )
        embed.add_field(name="Official Server", value="[Link](https://discord.gg/w2CkRtkj57)")
        embed.add_field(
            name="Official Wiki",
            value="[Link](https://discord-adventurers-bot.fandom.com)",
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="ping",
        description="Check if the bot is alive.",
    )
    async def ping(self, ctx: Context) -> None:
        """Check if the bot is alive."""
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
            color=0x9C84EF,
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))
