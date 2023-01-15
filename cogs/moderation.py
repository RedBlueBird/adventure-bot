import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks


class Moderation(commands.Cog, name="moderation"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="kick",
        description="Kick a user out of the server.",
    )
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(user="The user that should be kicked.", reason="The reason why the user should be kicked.")
    async def kick(self, ctx: Context, user: discord.User, *, reason: str = "Not specified") -> None:
        """
        Kick a user out of the server.
        :param user: The user that should be kicked from the server.
        :param reason: The reason for the kick. Default is "Not specified".
        """
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)
        if member.guild_permissions.administrator:
            embed = discord.Embed(
                title="Error!",
                description="User has Admin permissions.",
                color=0xE02B2B
            )
            await ctx.send(embed=embed)
        else:
            try:
                embed = discord.Embed(
                    title="User Kicked!",
                    description=f"**{member}** was kicked by **{ctx.author}**!",
                    color=0x9C84EF
                )
                embed.add_field(
                    name="Reason:",
                    value=reason
                )
                await ctx.send(embed=embed)
                try:
                    await member.send(
                        f"You were kicked by **{ctx.author}**!\nReason: {reason}"
                    )
                except:
                    # Couldn't send a message in the private messages of the user
                    pass
                await member.kick(reason=reason)
            except:
                embed = discord.Embed(
                    title="Error!",
                    description="An error occurred while trying to kick the user. "
                                "Make sure my role is above the role of the user you want to kick.",
                    color=0xE02B2B
                )
                await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="nick",
        description="Change the nickname of a user on a server.",
    )
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.describe(user="The user that should have a new nickname.", nickname="The new nickname.")
    async def nick(self, ctx: Context, user: discord.User, *, nickname: str = None) -> None:
        """
        Change the nickname of a user on a server.
        :param user: The user that should have its nickname changed.
        :param nickname: The new nickname of the user. Default is None, which will reset the nickname.
        """
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)
        try:
            await member.edit(nick=nickname)
            embed = discord.Embed(
                title="Changed Nickname!",
                description=f"**{member}'s** new nickname is **{nickname}**!",
                color=0x9C84EF
            )
            await ctx.send(embed=embed)
        except:
            embed = discord.Embed(
                title="Error!",
                description="An error occurred while trying to change the nickname of the user. "
                            "Make sure my role is above the role of the user you want to change the nickname of.",
                color=0xE02B2B
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="ban",
        description="Bans a user from the server.",
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(user="The user that should be banned.", reason="The reason why the user should be banned.")
    async def ban(self, ctx: Context, user: discord.User, *, reason: str = "Not specified") -> None:
        """
        Bans a user from the server.
        :param user: The user that should be banned from the server.
        :param reason: The reason for the ban. Default is "Not specified".
        """
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)
        try:
            if member.guild_permissions.administrator:
                embed = discord.Embed(
                    title="Error!",
                    description="User has Admin permissions.",
                    color=0xE02B2B
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="User Banned!",
                    description=f"**{member}** was banned by **{ctx.author}**!",
                    color=0x9C84EF
                )
                embed.add_field(
                    name="Reason:",
                    value=reason
                )
                await ctx.send(embed=embed)
                try:
                    await member.send(f"You were banned by **{ctx.author}**!\nReason: {reason}")
                except:
                    # Couldn't send a message in the private messages of the user
                    pass
                await member.ban(reason=reason)
        except:
            embed = discord.Embed(
                title="Error!",
                description="An error occurred while trying to ban the user. "
                            "Make sure my role is above the role of the user you want to ban.",
                color=0xE02B2B
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="purge",
        description="Delete a number of messages.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="The amount of messages that should be deleted.")
    async def purge(self, ctx: Context, amount: int) -> None:
        """
        Delete a number of messages.
        :param amount: The number of messages that should be deleted.
        """
        # Prevent an "Unknown Interaction" response
        await ctx.send("Deleting messages...")
        purged_messages = await ctx.channel.purge(limit=amount+1)
        embed = discord.Embed(
            title="Chat Cleared!",
            description=f"**{ctx.author}** cleared **{len(purged_messages)-1}** messages!",
            color=0x9C84EF
        )
        await ctx.channel.send(embed=embed)

    @commands.hybrid_command(
        name="hackban",
        description="Bans a user without the user having to be in the server.",
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(user_id="The user ID that should be banned.", reason="The reason why the user should be banned.")
    async def hackban(self, ctx: Context, user_id: str, *, reason: str = "Not specified") -> None:
        """
        Bans a user without the user having to be in the server.
        :param user_id: The ID of the user that should be banned.
        :param reason: The reason for the ban. Default is "Not specified".
        """
        try:
            await self.bot.http.ban(user_id, ctx.guild.id, reason=reason)
            user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
            embed = discord.Embed(
                title="User Banned!",
                description=f"**{user} (ID: {user_id}) ** was banned by **{ctx.author}**!",
                color=0x9C84EF
            )
            embed.add_field(
                name="Reason:",
                value=reason
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error!",
                description="An error occurred while trying to ban the user. "
                            "Make sure ID is an existing ID that belongs to a user.",
                color=0xE02B2B
            )
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
