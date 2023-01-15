import platform

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks


class General(commands.Cog, name="general"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="help",
        description="List all commands the bot has loaded."
    )
    async def help(self, ctx: Context) -> None:
        prefix = self.bot.config["prefix"]
        embed = discord.Embed(
            title="Help", description="List of available commands:", color=0x9C84EF
        )
        for i in self.bot.cogs:
            cog = self.bot.get_cog(i.lower())
            data = []
            for cmd in cog.get_commands():
                description = cmd.description.partition('\n')[0]
                data.append(f"{prefix}{cmd.name} - {description}")
            help_text = "\n".join(data)
            embed.add_field(
                name=i.capitalize(), value=f'```{help_text}```', inline=False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="botinfo",
        description="Get some info about the bot.",
    )
    async def botinfo(self, ctx: Context) -> None:
        """Get some info about the bot."""
        embed = discord.Embed(
            description="Used [Krypton's](https://krypton.ninja) template",
            color=0x9C84EF
        )
        embed.set_author(name="Bot Information")
        embed.add_field(
            name="Owner:",
            value="Krypton#7331",
            inline=True
        )
        embed.add_field(
            name="Python Version:",
            value=f"{platform.python_version()}",
            inline=True
        )
        embed.add_field(
            name="Prefix:",
            value=f"/ (Slash Commands) or {self.bot.config['prefix']} for normal commands",
            inline=False
        )
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="serverinfo",
        description="Get some info about the server.",
    )
    async def serverinfo(self, ctx: Context) -> None:
        """Get some info about the server."""
        roles = [role.name for role in ctx.guild.roles]
        if len(roles) > 50:
            roles = roles[:50]
            roles.append(f">>>> Displaying[50/{len(roles)}] Roles")
        roles = ", ".join(roles)

        embed = discord.Embed(
            title="**Server Name:**",
            description=f"{ctx.guild}",
            color=0x9C84EF
        )
        if ctx.guild.icon is not None:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.add_field(
            name="Server ID",
            value=ctx.guild.id
        )
        embed.add_field(
            name="Member Count",
            value=ctx.guild.member_count
        )
        embed.add_field(
            name="Text/Voice Channels",
            value=f"{len(ctx.guild.channels)}"
        )
        embed.add_field(
            name=f"Roles ({len(ctx.guild.roles)})",
            value=roles
        )
        embed.set_footer(text=f"Created at: {ctx.guild.created_at}")
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
            color=0x9C84EF
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="server",
        description="Get the invite link of the discord server of the bot.",
    )
    async def server(self, ctx: Context) -> None:
        """Get the invite link of the discord server of the bot."""
        embed = discord.Embed(
            description=f"Bot server link [here](https://discord.gg/w2CkRtkj57).",
            color=0xD75BF4
        )
        try:
            await ctx.author.send(embed=embed)
            await ctx.send("I sent you a private message!")
        except discord.Forbidden:
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))
