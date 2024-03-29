import typing as t
import datetime as dt

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db_manager as dm, util as u, resources as r, checks
from views import Shop, CardPages, Decks, Leaderboard


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

        if not dm.is_registered(user.id):
            await ctx.send(f"{ctx.author.mention}, that user isn't registered!")
            return

        user_premium = dm.get_user_premium(user.id)
        now = dt.datetime.now(dt.timezone.utc)
        if user_premium > now:
            days_left = (user_premium - now).days
            description_msg = f"14\n{r.ICONS['timer']}**ᴘʀᴇᴍɪᴜᴍ**: {days_left} days remaining\n"
            tickets = 10
        else:
            description_msg = "7\n"
            tickets = 5

        tick_msg = ""
        lvl = dm.get_user_level(user.id)
        if lvl >= 4:
            tick_msg = (
                f"{r.ICONS['ticket']}**Raid Tickets: **{dm.get_user_ticket(user.id)}/{tickets}"
            )

        descr = f"```{dm.queues[user.id]}```\n" if user.id in dm.queues else None
        embed = discord.Embed(
            title=f"{user.display_name}'s profile:",
            description=descr,
            color=discord.Color.gold(),
        )
        embed.set_thumbnail(url=user.avatar.url)

        hp = u.level_hp(lvl)
        xp = dm.get_user_exp(user.id)
        if lvl < 30:
            embed.add_field(
                name=f"Current Level: {lvl}",
                value=f"{r.ICONS['exp']} {xp}/{u.level_xp(lvl)}\n{r.ICONS['hp']} {hp}",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"Max Level: {lvl}",
                value=f"{r.ICONS['exp']} {xp}\n{r.ICONS['hp']} {hp}",
                inline=False,
            )

        user_daily = dm.get_user_daily(user.id)
        dts = "Right now!" if user_daily.date() != dt.date.today() else u.time_til_midnight()
        embed.add_field(
            name="Currency",
            value=(
                f"{r.ICONS['coin']}**Golden Coins: **{dm.get_user_coin(user.id)}\n"
                f"{r.ICONS['gem']}**Shiny Gems: **{dm.get_user_gem(user.id)}\n"
                f"{r.ICONS['token']}**Confetti: **{dm.get_user_token(user.id)}\n"
                f"{r.ICONS['medal']}**Medals: **{dm.get_user_gem(user.id)}\n"
                f"{tick_msg}"
            ),
            inline=False,
        )

        next_quest = dm.get_user_next_quest(user.id).timestamp()
        nq = u.time_converter(int(next_quest - now)) if next_quest is not None else "--"
        embed.add_field(
            name="Tasks",
            value=f"{r.ICONS['streak']}**Daily streak: **{dm.get_user_streak(user.id)}/"
            + description_msg
            + f"{r.ICONS['timer']}**Next daily: **{dts}\n{r.ICONS['timer']}**Next quest: **{nq}",
            inline=False,
        )

        badges = dm.get_user_badge(user.id)
        if badges != 2**30:
            icons = ["beta b", "pro b", "art b", "egg b", "fbi b", "for b"]
            owned_badges = []
            for i in range(len(icons)):
                if badges & (1 << i):  # Checks if the ith bit is set
                    owned_badges.append(r.ICONS[icons[i]])
            embed.add_field(name="Badges: ", value=" ".join(owned_badges))

        embed.set_footer(
            text=(
                f"Player ID: {dm.get_id(user.id)}; "
                f"Register Date: {dm.get_user_register_date(user.id)}"
            )
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="quests",
        description="Displays all current quests of a user.",
        aliases=["q", "quest", "qu"],
    )
    async def quests(self, ctx: Context, user: discord.Member = commands.Author):
        """Displays all current quests of a user."""

        if not dm.is_registered(user.id):
            await ctx.send(f"{ctx.author.mention}, that user isn't registered yet!")
            return

        quests = dm.get_user_quests(user.id)
        u.add_quests(user.id, quests)

        if not quests:
            embed = discord.Embed(
                title=f"{user.display_name}'s Quests:",
                description="You don't have any quests.\nCome back later for more!",
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(
                title=f"{user.display_name}'s Quests:", color=discord.Color.gold()
            )
            for quest in quests:
                quest_info = u.quest_info(quest[1], quest[2], quest[3])
                embed.add_field(
                    name=f"**{quest_info['rarity']} {quest_info['description']}**",
                    value=(
                        f"Finished {quest[4]}/{quest_info['requirement']}\n"
                        f"Reward: **{quest_info['reward']['exp']} {r.ICONS['exp']}"
                        f" {quest_info['reward']['other']} {r.ICONS[quest_info['reward']['type']]}**"
                    ),
                    inline=False,
                )

        embed.set_thumbnail(url=user.avatar.url)
        next_quest = dm.get_user_next_quest(user.id)
        if next_quest is not None:
            time_left = u.time_converter(
                int((next_quest - dt.datetime.now(dt.timezone.utc)).total_seconds())
            )
            if time_left != "Right Now":
                embed.set_footer(text=f"{time_left} left till a new quest")
        else:
            embed.set_footer(
                text="You have reached the maximum number of quests. Finish some to get more!"
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        description="Displays a user's cards.",
        aliases=["card", "i", "inv"],
    )
    async def cards(self, ctx: Context, page: int = 1, user: discord.Member = commands.Author):
        if not dm.is_registered(user.id):
            await ctx.reply("That user isn't registered yet!")
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
        self, ctx: Context, slot: int = 0, user: discord.Member = commands.Author
    ) -> None:
        if not dm.is_registered(user.id):
            await ctx.reply(f"That user isn't registered yet!")
            return

        if slot != 0:
            if not 1 <= slot <= 6:
                await ctx.reply("The deck slot number must between 1-6!")
                return

            if dm.get_user_level(user.id) < r.DECK_LVL_REQ[slot]:
                await ctx.reply(
                    f"You need to reach level {r.DECK_LVL_REQ[slot]} to get that deck slot!"
                )
                return

        view = Decks(user, slot)
        await ctx.send(embed=view.deck_embed(), view=view)

    @commands.hybrid_command(name="decks", description="Displays an overview of a user's decks.")
    async def decks(self, ctx: Context, user: discord.Member = commands.Author):
        if not dm.is_registered(user.id):
            await ctx.reply(f"That user isn't registered!")
            return

        view = Decks(user)
        await ctx.send(embed=view.overview_embed(), view=view)

    @commands.hybrid_command(name="shop", description="Display the shop.")
    @checks.level_check(3)
    async def shop(self, ctx: Context) -> None:
        embed = discord.Embed(
            title="Welcome to the card shop!",
            description="Click a page to get started.",
        )
        await ctx.send(embed=embed, view=Shop(ctx.author.id))


async def setup(bot):
    await bot.add_cog(Info(bot))
