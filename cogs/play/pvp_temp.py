import random
import discord
from discord.ext import commands

from helpers import db_manager as dm, resources as r, checks
from helpers.battle import BattleData2, Player, Card
from views.battle import PvpInvite, Select, Actions


class Pvp2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        aliases=["pvp2"],
        description="Battle with other players!"
    )
    @checks.level_check(5)
    @checks.not_preoccupied("in a friendly battle")
    @checks.is_registered()
    async def battle2(
            self, ctx: commands.Context,
            gamble_medals: int = 0,
    ):
        a = ctx.author
        if not 0 <= gamble_medals <= 10:
            await ctx.reply("You can't bet that amount of medals!")
            return

        # region UI
        view = Select(a)
        msg = await ctx.reply(view=view)
        while True:
            await view.wait()
            people = view.selected
            for p in people:
                id_ = p.id

                level_req = 1
                if dm.get_user_level(id_) < level_req:
                    await ctx.reply(f"{p.mention} isn't level {level_req} yet!")
                    break

                if dm.get_user_medal(id_) < gamble_medals:
                    await ctx.reply(f"{p.mention} doesn't have {gamble_medals}!")
                    break

                if dm.get_user_deck_count(id_) != 12:
                    await ctx.reply(f"{p.mention} doesn't have 12 cards in their deck!")
                    break
            else:
                break

            view = Select(a)
            await msg.edit(view=view)

        people = [ctx.author] + people

        req_msg = "Hey " + "\n".join(c.mention for c in people[1:]) + "!\n"
        if gamble_medals > 0:
            req_msg += f"{a.mention} wants to battle with {gamble_medals} {r.ICON['medal']}!\n"
        else:
            req_msg += f"{a.mention} wants to have a friendly battle!\n"

        view = PvpInvite(ctx.author, people, 6)
        await msg.edit(content=req_msg, view=view)
        await view.wait()

        if not view.start:
            return
        # endregion

        # region setting up the Battle
        players = []
        counter = 1
        for t_id, t in view.teams.items():
            for p in t:
                if p not in view.user_team:
                    continue
                player_deck = [
                    Card(name=i[1], lvl=i[2])
                    for i in dm.get_user_deck(p.id, dm.get_user_deck_slot(p.id))
                ]
                random.shuffle(player_deck)
                player = Player(
                    level=dm.get_user_level(p.id),
                    user=p,
                    team=t_id,
                    id=counter,
                    deck=player_deck
                )
                for card in player.deck:
                    card.owner = player
                players.append(player)
                counter += 1
                dm.queues[p.id] = "in a pvp battle"

        if gamble_medals > 0:
            s = "s" if gamble_medals > 1 else ""
            title = f"A {gamble_medals}-Medal{s} Battle Just Started!"
        else:
            title = "A Friendly Battle Just Started!"
        desc = " vs ".join([str(x.user.name) for x in players])
        embed = discord.Embed(
            title=title,
            description=desc,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

        dd = BattleData2(
            players=players
        )
        stats_msg = await ctx.send(embed=dd.set_up())
        battle_buttons = Actions(
            battledata=dd,
            stats_msg=stats_msg
        )
        # endregion

        await stats_msg.edit(embed=dd.show_stats(), view=battle_buttons)

        for player in players:
            if int(player.user.id) in dm.queues:
                del dm.queues[int(player.user.id)]

    @commands.hybrid_command(
        aliases=["m"],
        description="Make a move."
    )
    @checks.is_registered()
    async def move(
            self, ctx: commands.Context,
            moves: commands.Greedy[int]
    ):
        dm.set_user_battle_command(ctx.author.id, " ".join([str(i) for i in moves]))
        try:
            await ctx.message.delete()
        except:
            pass


async def setup(bot):
    await bot.add_cog(Pvp2(bot))
