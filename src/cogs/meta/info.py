import datetime as dt
import typing as t

import discord
from discord.ext import commands
from discord.ext.commands import Context

import db
import resources as r
from helpers import checks
from helpers import util as u
from views import CardPages, Decks, Leaderboard, Shop


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="profile",
        description="Check a player's general information.",
        aliases=["p", "pro"],
    )
    async def profile(self, ctx: Context, user: discord.Member = commands.Author):
        """Check a player's general information."""

        player = db.Player.get_or_none(db.Player.id == user.id)
        if player is None:
            await ctx.reply(f"That user isn't registered yet!")
            return

        prem_expiration = player.premium_acc
        now = dt.date.today()
        if prem_expiration > now:
            days_left = (prem_expiration - now).days
            description_msg = f"14\n{r.ICONS['timer']}**ᴘʀᴇᴍɪᴜᴍ**: {days_left} days remaining\n"
            tickets = 10
        else:
            description_msg = "7\n"
            tickets = 5

        tick_msg = ""
        lvl = player.level
        if lvl >= 4:
            tick_msg = f"{r.ICONS['ticket']}**Raid Tickets: **{player.raid_tickets}/{tickets}"

        action = db.get_user_action(user.id)
        embed = discord.Embed(
            title=f"{user.display_name}'s profile:",
            description=f"```{action}```\n" if action is not None else None,
            color=discord.Color.gold(),
        )
        embed.set_thumbnail(url=user.avatar.url)

        hp = u.level_hp(lvl)
        if lvl < 30:
            embed.add_field(
                name=f"Current Level: {lvl}",
                value=f"{r.ICONS['exp']} {player.xp}/{u.level_xp(lvl)}\n{r.ICONS['hp']} {hp}",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"Max Level: {lvl}",
                value=f"{r.ICONS['exp']} {player.xp}\n{r.ICONS['hp']} {hp}",
                inline=False,
            )

        dts = "Right now!" if player.daily_date != now else u.time_til_midnight()
        embed.add_field(
            name="Currency",
            value=(
                f"{r.ICONS['coin']} **Golden Coins: **{player.coins}\n"
                f"{r.ICONS['gem']} **Shiny Gems: **{player.gems}\n"
                f"{r.ICONS['token']} **Confetti: **{player.event_tokens}\n"
                f"{r.ICONS['medal']} **Medals: **{player.medals}\n"
                f"{tick_msg}"
            ),
            inline=False,
        )

        embed.add_field(
            name="Tasks",
            value=f"{r.ICONS['streak']}**Daily streak: **{player.streak}/"
            + description_msg
            + f"{r.ICONS['timer']}**Next daily: **{dts}",
            inline=False,
        )

        if player.badges != 0:
            icons = ["beta b", "pro b", "art b", "egg b", "fbi b", "for b"]
            owned_badges = []
            for i in range(len(icons)):
                if player.badges & (1 << i):  # Checks if the ith bit is set
                    owned_badges.append(str(r.ICONS[icons[i]]))
            embed.add_field(name="Badges", value=" ".join(owned_badges))

        embed.set_footer(text=f"Player ID: {player.id}; Register Date: {player.creation_date}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="quests",
        description="Displays all current quests of a user.",
        aliases=["q", "quest", "qu"],
    )
    async def quests(self, ctx: Context, user: discord.Member = commands.Author):
        """Displays all current quests of a user."""
        player = db.Player.get_or_none(db.Player.id == user.id)
        if player is None:
            await ctx.reply(f"That user isn't registered yet!")
            return

        quests = list(player.quests)
        embed = discord.Embed(
            title=f"{user.display_name}'s Quests:",
            color=discord.Color.green(),
        )
        if not quests:
            embed.description = "You don't have any quests.\nCome back later for more!"
        else:
            for quest in quests:
                embed.add_field(
                    name=f"**{quest.rarity.name}. {quest.description()}**",
                    value=(
                        f"Finished {quest.progress}/{quest.requirement()}\n"
                        f"Reward: **{quest.xp_reward()} {r.ICONS['exp']}"
                        f" {quest.reward()} {quest.reward_type.emoji()}**"
                    ),
                    inline=False,
                )

        embed.set_thumbnail(url=user.avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        description="Displays a user's cards.",
        aliases=["card", "i", "inv"],
    )
    async def cards(self, ctx: Context, page: int = 1, user: discord.Member = commands.Author):
        if not db.Player.select().where(db.Player.id == user.id).exists():
            await ctx.reply(f"That user isn't registered yet!")
            return

        view = CardPages(ctx.author, user, page=page - 1)
        await ctx.send(embed=view.page_embed(), view=view)

    @commands.hybrid_command(
        name="leaderboard",
        description="Displays the world's top players.",
        aliases=["lb", "lbs"],
    )
    async def leaderboard(
        self,
        ctx: Context,
        name: t.Literal["level", "coins", "gems", "medals", "tokens"],
    ) -> None:
        view = Leaderboard(name, ctx.author.id, self.bot)
        await ctx.send(embed=await view.leaderboard_embed(), view=view)

    @commands.hybrid_command(
        name="deck", description="Displays the user's currently equipped deck."
    )
    async def deck(
        self, ctx: Context, deck: int = 0, user: discord.Member = commands.Author
    ) -> None:
        player = db.Player.get_or_none(db.Player.id == user.id)
        if player is None:
            await ctx.reply(f"That user isn't registered yet!")
            return

        deck = player.deck if deck == 0 else deck
        if not 1 <= deck <= 6:
            await ctx.reply("The deck number must between 1-6!")
            return

        if player.level < r.DECK_LVL_REQ[deck]:
            await ctx.reply(f"You need to reach level {r.DECK_LVL_REQ[deck]} to get that deck!")
            return

        view = Decks(user, deck)
        await ctx.send(embed=view.deck_embed(), view=view)

    @commands.hybrid_command(name="decks", description="Displays an overview of a user's decks.")
    async def decks(self, ctx: Context, user: discord.Member = commands.Author):
        if not db.Player.select().where(db.Player.id == user.id).exists():
            await ctx.reply(f"That user isn't registered yet!")
            return
        view = Decks(user)
        await ctx.send(embed=view.overview_embed(), view=view)

    @commands.hybrid_command(name="shop", description="Display the shop.")
    @checks.level_check(3)
    @checks.is_registered()
    async def shop(self, ctx: Context) -> None:
        embed = discord.Embed(
            title="Welcome to the card shop!",
            description="Click a page to get started.",
        )
        await ctx.send(embed=embed, view=Shop(ctx.author.id))


async def setup(bot):
    await bot.add_cog(Info(bot))
