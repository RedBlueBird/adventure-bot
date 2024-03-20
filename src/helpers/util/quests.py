import random
from datetime import datetime, timedelta, timezone

import discord
from discord.ext.commands import Context

from ..resources import ICONS
from ..util import randint_log
from .. import db_manager as dm


def quest_info(quest_type: int, reward_type: int, rarity: int):
    descriptions = [
        "Kill {amount} opponents while adventuring",
        "Accumulate items of weight over {amount} while adventuring",
        "Adventure {amount} meters",
        "Win {amount} non-friendly PvP battles",
        "Earn {amount} coins adventuring",
        "Earn {amount} medals in PvP battles",
        "Merge {amount} pairs of cards",
        "Catch {amount} fish in the public boat",
    ]
    rarities = ["C", "R", "E", "L", "EX"]
    requirements = [
        [5, 10, 20, 50],  # Kill mobs
        [10, 20, 40, 60],  # Collect items
        [500, 1000, 2000, 5000],  # Travel a certain distance
        [1, 3, 5, 10],  # Battle
        [100, 200, 500, 1000],  # Collect coins
        [5, 10, 25, 50],  # Collect medals
        [1, 2, 5, 10],  # Merge cards
        [3, 5, 10, 20],  # Catch fish
    ]
    exp_rewards = [25, 50, 100, 200, 250]
    other_rewards = [[200, 500, 1000, 2500], [0, 1, 2, 4]]
    reward_types = ["coin", "gem"]
    return {
        "description": descriptions[quest_type].format(amount=requirements[quest_type][rarity]),
        "rarity": rarities[rarity],
        "requirement": requirements[quest_type][rarity],
        "reward": {
            "exp": exp_rewards[rarity],
            "other": other_rewards[reward_type][rarity],
            "type": reward_types[reward_type],
        },
    }


async def update_quest(ctx: Context, uid: int, quest_type: int, change: int):
    quests = dm.get_user_quests(uid, quest_type)
    if not quests:
        return
    quest = list(quests[0])
    quest[4] += change

    qi = quest_info(quest[1], quest[2], quest[3])
    if quest[4] >= qi["requirement"]:
        embed = discord.Embed(
            title=f"QUEST COMPLETE {ctx.author.name}!",
            description=None,
            color=discord.Color.green(),
        )
        embed.add_field(
            name=f"**{qi['rarity']} {qi['description']}**",
            value=(
                f"**+{qi['reward']['exp']} {ICONS['exp']}"
                f" +{qi['reward']['other']} {ICONS[qi['reward']['type']]}**"
            ),
            inline=False,
        )
        embed.set_thumbnail(url=ctx.author.avatar.url)
        await ctx.channel.send(embed=embed)

        dm.delete_user_quest(quest[0])

        dm.set_user_exp(uid, dm.get_user_exp(uid) + qi["reward"]["exp"])
        dm.set_user_token(uid, dm.get_user_token(uid) + 1)
        if qi["reward"]["type"] == "coin":
            dm.set_user_coin(uid, dm.get_user_coin(uid) + qi["reward"]["coin"])
        elif qi["reward"]["type"] == "gem":
            dm.set_user_gem(uid, dm.get_user_gem(uid) + qi["reward"]["gem"])

        next_quest = dm.get_user_next_quest(uid)
        now = datetime.now(timezone.utc)
        is_premium = dm.get_user_premium(uid) > now
        if next_quest is None and len(quests) < 4 + is_premium:
            next_quest = now + timedelta(minutes=(15 if is_premium else 30))
            dm.set_user_next_quest(uid, next_quest)
    else:
        dm.set_user_quest_progress(quest[0], quest[5])


def add_quest(uid: int, quests: list[tuple[int, int, int, int, int]]):
    rarity = randint_log(0, 3)
    reward_type = 0
    if random.randint(1, 100) > 75:
        reward_type = 1
    while True:
        quest_type = random.randint(0, 7)
        repeat = False
        for quest in quests:
            if quest[1] == quest_type:
                repeat = True
        if not repeat:
            break
    quests.append((uid, quest_type, reward_type, rarity, 0))


def add_quests(uid: int, quests: list[tuple[int, int, int, int, int]]):
    now = datetime.now()
    is_premium = dm.get_user_premium(uid) > now
    next_quest = dm.get_user_next_quest(uid)
    if next_quest is None:
        return
    added = 0
    while len(quests) < 4 + is_premium and now >= next_quest:
        add_quest(uid, quests)
        next_quest += timedelta(minutes=(15 if is_premium else 30))
        added += 1
    if added:
        if len(quests) == 4 + is_premium:
            return
        dm.add_user_quests(quests[-added:])
        dm.set_user_next_quest(uid, next_quest)
