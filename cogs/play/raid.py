import discord
from discord.ext import commands

from helpers import db_manager as dm
from helpers import checks
from views import BattleSelect, RaidInvite
import util as u


class Raid(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.hybrid_command(
        aliases=["coop", "cp"],
        description="Band with other players to fight OP bosses!"
    )
    @checks.level_check(4)
    @checks.is_registered()
    @checks.not_preoccupied("raiding a boss")
    async def raid(self, ctx: commands.Context):
        a = ctx.author

        members = 1
        view = BattleSelect(a, members, members)
        msg = await ctx.reply(view=view)
        while True:
            await view.wait()
            people = view.selected
            for p in people:
                id_ = p.id

                # level_req = 4
                # if dm.get_user_level(id_) < level_req:
                #     await ctx.reply(f"{u.mention} isn't level {level_req} yet!")
                #     break

                # if dm.get_user_ticket(id_) == 0:
                #     await ctx.reply(f"{p.mention} doesn't have any raid tickets!")
                #     break

                if dm.get_user_deck_count(id_) != 12:
                    await ctx.reply(f"{p.mention} doesn't have 12 cards in their deck!")
                    break
            else:
                break

            view = BattleSelect(a)
            await msg.edit(view=view)

        people = [ctx.author] + people
        req_msg = "Hey " + '\n'.join(c.mention for c in people[1:]) + "!\n" \
                  f"Wanna raid a boss with {a.mention}?\n" \
                  f"Keep in mind that you'll need one {u.ICON['tick']}."
        view = RaidInvite(ctx.author, people)
        await msg.edit(content=req_msg, view=view)
        await view.wait()

        if not view.start:
            return

        await ctx.reply("shit raids haven't been implemented yet lmao")


async def setup(bot: commands.Bot):
    await bot.add_cog(Raid(bot))
