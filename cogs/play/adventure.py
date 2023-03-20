import random
import math
import io

from PIL import Image
import discord
from discord.ext import commands

from helpers import db_manager as dm, util as u, resources as r, checks
from helpers.battle import BattleData

import views.adventure.games as g
import views.adventure.hometown as ht
import views.adventure.wild as w


def choices_list(choices) -> str:
    logs = []
    for c in choices:
        logs.append(f"**[{len(logs) + 1}]** {c}")
    return "\n".join(logs)


def mark_location(bg_pic: str, x: int | float, y: int | float) -> io.BytesIO:
    background = Image.open(f"resources/img/{bg_pic}.png")
    new_image = Image.open("resources/img/marker.png")
    background.paste(new_image, (10 + 32 * x, 32 * y), new_image)
    out = io.BytesIO()
    background.save(out, format="png")
    out.seek(0)
    return out


def setup_minigame(
        game_name: str, show_map: bool
) -> tuple[discord.Embed, discord.File | None]:
    embed = discord.Embed(
        title=f"Minigame - {game_name}!",
        color=discord.Color.gold()
    )

    logs = [f"• {r}" for r in r.MINIGAMES[game_name].rules]
    embed.add_field(name="Rules", value="\n".join(logs))

    embed.set_footer(text=f"{u.PREF}exit -quit minigame")
    if show_map:
        if r.MINIGAMES[game_name].img is not None:
            return (
                embed,
                discord.File(r.MINIGAMES[game_name].img)
            )
        else:
            return embed, None
    else:
        return embed, None


class Adventure(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases=["ad", "adv"],
        description="Go on an adventure!"
    )
    @checks.not_preoccupied("on an adventure")
    @checks.is_registered()
    async def adventure(self, ctx: commands.Context):
        a = ctx.author

        lvl = dm.get_user_level(a.id)
        inv = dm.get_user_inventory(a.id)
        pos = dm.get_user_position(a.id)
        show_map = dm.get_user_map(a.id)

        adventure = False
        # region hometown exploration
        loading = discord.Embed(title="Loading...", description=u.ICON['load'])
        adv_msg = await ctx.send(embed=loading)

        while True:
            embed = discord.Embed(
                title=f"{a.display_name}'s Adventure",
                description=f"{u.HTOWN[pos]['description']}",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=a.avatar.url)

            file = discord.File(
                mark_location("hometown_map", *u.HTOWN[pos]["coordinate"]),
                filename="hometown_map.png"
            )

            view = ht.Decision(a, u.HTOWN[pos]["choices"], file)
            attach = [file] if show_map else []
            await adv_msg.edit(embed=embed, attachments=attach, view=view)
            await view.wait()

            if view.show_map is not None:
                show_map = view.show_map
            choice = view.decision

            if choice is None:
                await adv_msg.edit(
                    content="You spaced out and the adventure was ended.",
                    embed=None, view=None, attachments=[]
                )
                break

            if choice == "exit":
                await adv_msg.edit(
                    content="You quit this adventure.",
                    embed=None, view=None, attachments=[]
                )
                break

            state = u.HTOWN[pos]["choices"][choice]

            if state[1] == "self":
                if state[0] in u.HTOWN:
                    pos = state[0]
                else:
                    await ctx.reply("Sorry, this route is still in development!")

            elif state[1] == "selling":
                view = ht.Sell(a)
                embed.set_footer(
                    text="You can use `a.info item (name)` "
                         "to check the sell price of an item!"
                )
                await adv_msg.edit(
                    content=None,
                    embed=u.container_embed(inv),
                    view=view
                )
                await view.wait()

                coins = dm.get_user_coin(a.id)
                inv = dm.get_user_inventory(a.id)

            elif state[1] == "buying":
                offers = [
                    "forest fruit", "fruit salad", "raft", "torch", "herb",
                    "health potion", "power potion", "large health potion",
                    "large power potion", "resurrection amulet", "teleportation stone"
                ]
                offer_str = []
                for o in map(u.items_dict, offers):
                    offer_str.append(
                        f"[{o['rarity']}/{o['weight']}] {o['name']} - {o['buy']} gc"
                    )

                embed = discord.Embed(
                    title="Jessie's Shop:",
                    description="I have everything adventurers need!\n"
                                "```" + "\n".join(offer_str) + "```",
                    color=discord.Color.gold()
                )
                view = ht.Shop(a, offers)
                await adv_msg.edit(embed=embed, view=view)
                await view.wait()

                coins = dm.get_user_coin(a.id)
                inv = dm.get_user_inventory(a.id)

            elif state[1] == "chest":
                embed = u.container_embed(dm.get_user_storage(a.id), "Chest", lvl) \
                    .add_field(name="Your Backpack", value=f"```{u.container_str(inv)}```")
                view = ht.Chest(a)
                await adv_msg.edit(
                    content=None,
                    embed=embed,
                    view=view
                )
                await view.wait()

                inv = dm.get_user_inventory(a.id)

            elif state[1] == "minigame":
                dm.queues[a.id] = "playing a minigame"
                if state[0] == "coin flip":
                    view = g.CoinFlip(a)
                elif state[0] == "fishing":
                    view = g.Fishing(a)
                elif state[0] == "blackjack":
                    view = g.Blackjack(a)

                embed, img = setup_minigame(
                    u.HTOWN[pos]["choices"][choice][0],
                    show_map
                )
                await adv_msg.edit(
                    embed=embed,
                    attachments=[] if img is None else [img],
                    view=view
                )
                await view.wait()
                dm.queues[a.id] = "wandering around town"

            elif state[1] == "adventure":
                if dm.get_user_deck_count(a.id) != 12:
                    await ctx.reply("You need 12 cards in your deck first!")
                    continue

                if state[0] == "boss raid":
                    lvl_req = 9
                    if lvl < lvl_req:
                        await ctx.reply(
                            f"You need to be at least "
                            f"level {lvl_req} to fight a boss!",
                            ephemeral=True
                        )
                        continue
                    if dm.get_user_ticket(a.id) < 1:
                        await ctx.reply("You need a raid ticket first!", ephemeral=True)
                        continue

                    embed = discord.Embed(
                        title="Raid Preparation",
                        description="How hard do you want the raid to be?",
                        color=discord.Color.yellow()
                    )
                    view = ht.LevelSelect(a)
                    await adv_msg.edit(embed=embed, view=view)
                    await view.wait()

                    if view.exit:
                        continue
                    if view.level is not None:
                        raid_lvls = view.level
                        dm.set_user_ticket(a.id, dm.get_user_ticket(a.id) - 1)
                        adventure = True
                else:
                    adventure = True

                break

        dm.set_user_map(a.id, show_map)
        dm.set_user_inventory(a.id, inv)
        dm.set_user_position(a.id, pos)
        # endregion

        if not adventure:
            return

        max_hp = u.level_hp(lvl)
        hp = max_hp
        stamina = 100
        dist = 0
        badges = dm.get_user_badge(a.id)

        coins = dm.get_user_coin(a.id)
        gems = dm.get_user_gem(a.id)
        xp = dm.get_user_exp(a.id)

        adv = u.ADVENTURES[pos]
        start = "main", "start", 0
        embed = discord.Embed(
            title=f"{a.display_name}'s {pos.title()} Adventure",
            description="test description"
        )
        view = w.Adventure(a, adv, start)
        await adv_msg.edit(embed=embed, view=view, attachments=[])

        await ctx.reply("Sorry, the devs are still working on this!")


async def setup(bot):
    await bot.add_cog(Adventure(bot))
