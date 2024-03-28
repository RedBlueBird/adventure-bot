import discord
from discord.ext.commands import Context

import db
from ..resources import ICONS


# this function modifies the player instance so be sure to save or wahtever
async def update_quest(quest_type: db.QuestType, progress: int, ctx: Context):
    if progress <= 0:
        return

    for q in db.Player.get_by_id(ctx.author.id).quests:
        if q.quest_type != quest_type:
            continue

        q.progress += progress
        q.save()
        if q.progress < q.requirement():
            continue

        embed = discord.Embed(
            title=f"**QUEST COMPLETE {ctx.author.name}!**",
            description=None,
            color=discord.Color.green(),
        )
        embed.add_field(
            name=f"**{q.rarity.name} {q.description()}**",
            value=f"**+{q.xp_reward()} {ICONS['exp']} +{q.reward()} {q.reward_type.emoji()}**",
            inline=False,
        )
        embed.set_thumbnail(url=ctx.author.avatar.url)
        await ctx.channel.send(embed=embed)

        match q.reward_type:
            case db.RewardType.COINS:
                q.player.coins += q.reward()
            case db.RewardType.GEMS:
                q.player.gems += q.reward()
        q.player.xp += q.xp_reward()
        q.player.save()

        q.delete_instance()
