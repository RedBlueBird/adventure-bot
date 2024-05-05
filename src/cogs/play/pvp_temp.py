import random
import math

import discord
from discord.ext import commands

import db
from helpers import checks
import resources as r
from helpers.battle import BattleData2, Player, Card
from views.battle import PvpInvite, Select, Actions


class Pvp2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["pvp2"], description="Battle with other players!")
    @checks.level_check(5)
    @checks.not_preoccupied("in a friendly battle")
    @checks.is_registered()
    async def battle2(
        self,
        ctx: commands.Context,
        gamble_medals: int = 0,
    ):
        a = ctx.author
        if not 0 <= gamble_medals <= 10:
            await ctx.reply("You can't bet that amount of medals!")
            return

        # region Invitation UI
        view = Select(a)
        msg = await ctx.reply(view=view)
        while True:
            await view.wait()
            if view.quit:
                await msg.edit(content="Battle quit.", view=None)
                return
            elif view.selected is None:
                await msg.edit(content="Selection timed out.", view=None)
                return

            ppl = view.selected
            for p in ppl:
                player = db.Player.get_by_id(p.id)

                if player.medals < gamble_medals:
                    await ctx.reply(f"{p.display_name} doesn't have {gamble_medals} {r.ICONS['medal']}!")
                    break

                sel_deck = db.Deck.get((db.Deck.owner == player.id) & (db.Deck.slot == player.deck))
                if len(sel_deck.cards) != 12:
                    await ctx.reply(f"{p.display_name} doesn't have 12 cards in their deck!")
                    break
            else:
                break

            # restart the view
            view = Select(a)
            await msg.edit(view=view)

        ppl = [ctx.author] + ppl
        ppl_db = {p.id: db.Player.get_by_id(p.id) for p in ppl}

        req_msg = "Hey " + "\n".join(c.mention for c in ppl[1:]) + "!\n"
        if gamble_medals > 0:
            req_msg += f"{a.mention} wants to battle with {gamble_medals} {r.ICONS['medal']}!\n"
        else:
            req_msg += f"{a.mention} wants to have a friendly battle!\n"

        view = PvpInvite(ctx.author, ppl, 6)
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

                p_db = ppl_db[p.id]
                player_deck = [Card(name=i.name, lvl=i.level) for i in db.get_deck(p.id)]
                random.shuffle(player_deck)
                player = Player(
                    level=p_db.level,
                    hp=100 * math.floor(p_db.level / 2),
                    max_hp=100 * math.floor(p_db.level / 2),
                    user=p,
                    team=t_id,
                    id=counter,
                    deck=player_deck,
                )
                for card in player.deck:
                    card.owner = player
                players.append(player)
                counter += 1
                db.lock_user(p.id, "pvp", "in a PvP battle")

        if gamble_medals > 0:
            s = "s" if gamble_medals > 1 else ""
            title = f"A {gamble_medals}-Medal{s} Battle Just Started!"
        else:
            title = "A Friendly Battle Just Started!"

        desc = " vs ".join([str(x.user.name) for x in players])
        embed = discord.Embed(title=title, description=desc, color=discord.Color.gold())
        await ctx.send(embed=embed)

        dd = BattleData2(players=players)
        stats_msg = await ctx.send(embed=dd.set_up())
        battle_buttons = Actions(battledata=dd, stats_msg=stats_msg)
        # endregion

        await stats_msg.edit(embed=dd.show_stats(), view=battle_buttons)

        for player in players:
            db.unlock_user(player.user.id, "pvp")

    @commands.hybrid_command(aliases=["m"], description="Make a move.")
    @checks.is_registered()
    async def move(self, ctx: commands.Context, moves: commands.Greedy[int]):
        # dm.set_user_battle_command(ctx.author.id, " ".join([str(i) for i in moves]))
        try:
            await ctx.message.delete()
        except:
            pass


async def setup(bot):
    await bot.add_cog(Pvp2(bot))
