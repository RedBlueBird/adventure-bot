import asyncio
import io
import random
import time
from string import ascii_lowercase

from PIL import Image, ImageDraw, ImageFont
import discord
from discord.ext import commands

from helpers import db_manager as dm, util as u, resources as r, checks

from views.adventure import Decision
from views.adventure import games as g, hometown as ht, wild as w


def mark_location(bg_pic: str, x: int | float, y: int | float) -> io.BytesIO:
    background = Image.open(f"resources/img/{bg_pic}.png")
    mark = Image.open("resources/img/marker.png")
    background.paste(mark, (10 + 32 * x, 32 * y), mark)

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

    logs = [f"• {rule}" for rule in r.MINIGAMES[game_name].rules]
    embed.add_field(name="Rules", value="\n".join(logs))

    embed.set_footer(text=f"{r.PREF}exit -quit minigame")
    if show_map:
        if r.MINIGAMES[game_name].img is not None:
            return embed, discord.File(r.MINIGAMES[game_name].img)
        else:
            return embed, None
    else:
        return embed, None


def txt_on_img(txt: str) -> io.BytesIO:
    font = ImageFont.truetype("arial.ttf", 50)
    width, height = 300, 125
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # https://stackoverflow.com/a/66793499/12128483
    d.text((width / 2, height / 2), txt, fill="black", font=font, anchor="mm")

    out = io.BytesIO()
    img.save(out, format="PNG")
    out.seek(0)
    return out


async def embed_addon(
        msg: discord.Message, embed: discord.Embed,
        addon: str, title: str = "Quick!",
        img: discord.File | None = None
) -> discord.Message:
    new = embed.copy()
    new.add_field(name=title, value=addon)
    files = []
    if img is not None:
        img.filename = "embed_img.png"
        new.set_image(url=f"attachment://{img.filename}")
        files = [img]
    return await msg.edit(embed=new, view=None, attachments=files)


class Adventure(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
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
        raid_lvl = None
        # region hometown exploration
        loading = discord.Embed(title="Loading...", description=r.ICON["load"])
        adv_msg = await ctx.reply(embed=loading, mention_author=False)
        while True:
            embed = discord.Embed(
                title=f"{a.display_name}'s Adventure",
                description=f"{r.HTOWN[pos].description}",
                color=discord.Color.gold()
            )

            file = discord.File(
                mark_location("hometown_map", *r.HTOWN[pos].coordinate),
                filename="hometown_map.png"
            )

            view = Decision(a, r.HTOWN[pos].choices, file)
            attach = []
            if show_map:
                embed.set_image(url=f"attachment://{file.filename}")
                attach = [file]
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

            state = r.HTOWN[pos].choices[choice]
            match state.action:
                case "self":
                    if state.pos in r.HTOWN:
                        pos = state.pos
                    else:
                        await ctx.reply("Sorry, this route is still in development!")

                case "selling":
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
                    inv = dm.get_user_inventory(a.id)

                case "buying":
                    offers = [
                        "forest fruit", "fruit salad", "raft", "torch", "herb",
                        "health potion", "large health potion",
                        "power potion", "large power potion",
                        "resurrection amulet", "teleportation stone"
                    ]
                    offer_str = []
                    for o in map(r.item, offers):
                        offer_str.append(
                            f"[{o.rarity}/{o.weight}] {o.name} - {o.buy} gc"
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

                    inv = dm.get_user_inventory(a.id)

                case "chest":
                    inv_str = u.container_str(inv)
                    embed = u.container_embed(dm.get_user_storage(a.id), "Chest", lvl) \
                        .add_field(name="Your Backpack", value=f"```{inv_str}```")
                    view = ht.Chest(a)
                    await adv_msg.edit(
                        content=None,
                        embed=embed,
                        view=view
                    )
                    await view.wait()

                    inv = dm.get_user_inventory(a.id)

                case "minigame":
                    dm.queues[a.id] = "playing a minigame"
                    if state.pos == "coin flip":
                        view = g.CoinFlip(a)
                    elif state.pos == "fishing":
                        view = g.Fishing(a)
                    elif state.pos == "blackjack":
                        view = g.Blackjack(a)

                    embed, img = setup_minigame(
                        r.HTOWN[pos].choices[choice].pos,
                        show_map
                    )
                    await adv_msg.edit(
                        embed=embed,
                        attachments=[] if img is None else [img],
                        view=view
                    )
                    await view.wait()
                    dm.queues[a.id] = "wandering around town"

                case "adventure":
                    if dm.get_user_deck_count(a.id) != 12:
                        await ctx.reply("You need 12 cards in your deck first!")
                        continue

                    if state.pos == "boss raid":
                        lvl_req = 9
                        if lvl < lvl_req:
                            await ctx.reply(
                                f"You need to be at least "
                                f"level {lvl_req} to fight a boss!",
                                ephemeral=True
                            )
                            continue
                        if dm.get_user_ticket(a.id) < 1:
                            await ctx.reply(
                                "You need a raid ticket first!",
                                ephemeral=True
                            )
                            continue

                        embed = discord.Embed(
                            title="Raid Preparation",
                            description="How hard do you want the raid to be?",
                            color=discord.Color.yellow()
                        )
                        view = ht.LevelSelect(a)
                        await adv_msg.edit(embed=embed, view=view)
                        await view.wait()

                        if view.level is not None:
                            raid_lvl = view.level
                            dm.set_user_ticket(a.id, dm.get_user_ticket(a.id) - 1)
                            adventure = True
                    else:
                        adventure = True

                    break  # out of the exploration loop

        # save their current state before setting them on an adventure
        dm.set_user_map(a.id, show_map)
        dm.set_user_inventory(a.id, inv)
        dm.set_user_position(a.id, pos)
        # endregion

        if adventure:
            await self.explore(ctx, adv_msg, pos, raid_lvl)

    async def explore(
            self, ctx: commands.Context,
            adv_msg: discord.Message,
            journey: str, raid_lvl: int | None
    ):
        a = ctx.author

        lvl = dm.get_user_level(a.id)
        max_hp = u.level_hp(lvl)
        hp = max_hp
        dist = 0

        coins = dm.get_user_coin(a.id)
        gems = dm.get_user_gem(a.id)
        xp = dm.get_user_exp(a.id)
        inv = dm.get_user_inventory(a.id)

        adv = r.ADVENTURES[journey]
        start = "main", "start", 0
        curr_op = adv[start[0]][start[1]][start[2]]
        end_cause = None
        while True:
            embed = discord.Embed(
                title=f"{a.display_name}'s {journey.title()} Adventure",
                description=curr_op.description,
                color=discord.Color.green()
            )
            decision_view = Decision(a, curr_op.choices or ["Continue"])
            if curr_op.instant is not None:
                if curr_op.instant.trap == "reaction":
                    addon = "Press the button as soon as you see it!"
                    adv_msg = await embed_addon(adv_msg, embed, addon)
                    wait = random.uniform(3, 7)
                    await asyncio.sleep(wait)

                    start = time.time()
                    react_view = w.Reaction(a)
                    await adv_msg.edit(view=react_view)
                    await react_view.wait()

                    diff = time.time() - start
                    if diff > 2:
                        hp_loss = 300
                        embed.description = f"**Oh no!**\n" \
                                            f"You were too slow and lost {hp_loss} HP!"
                        hp -= hp_loss
                    else:
                        embed.description = "**Awesome!**\nYou dodged just fast enough!"

                elif curr_op.instant.trap == "memorize":
                    chars = "".join(random.choice(ascii_lowercase) for _ in range(5))
                    addon = "Memorize these characters:"
                    img = discord.File(txt_on_img(chars))
                    adv_msg = await embed_addon(adv_msg, embed, addon, img=img)
                    await asyncio.sleep(3)

                    reaction_embed = adv_msg.embeds[0]
                    reaction_embed.set_field_at(
                        0, name="Alright...",
                        value="What were those letters?\n"
                              f"Type `{r.PREF}[what you remember]`!"
                    )
                    reaction_embed.set_image(url=None)
                    await adv_msg.edit(embed=reaction_embed, attachments=[])

                    try:
                        msg = await self.bot.wait_for(
                            "message", timeout=5,
                            check=checks.valid_reply("", a, ctx.message.channel)
                        )
                        reply = msg.content[2:]
                        await msg.delete()
                    except asyncio.TimeoutError:
                        reply = ""

                    if reply != chars:
                        hp_loss = 200
                        embed.description = f"**Oh no!**\n" \
                                            f"You misremembered (the letters were {chars}) " \
                                            f"and lost {hp_loss} HP!"
                        hp -= hp_loss
                        if hp <= 0:
                            end_cause = "death"
                            break
                    else:
                        embed.description = "**Awesome!**\nYou got the letters right!"

            await adv_msg.edit(embed=embed, view=decision_view, attachments=[])
            await decision_view.wait()
            decision = decision_view.decision

            if decision is None or decision == "exit":
                end_cause = "leave"
                break

            if curr_op.choices is not None:
                choice = curr_op.choices[decision]
                req_filled = True
                for req in choice.reqs:
                    if inv.get(req.name, 0) < req.amt:
                        req_filled = False
                        break

                if not req_filled:
                    bad_msg = await ctx.reply("You don't have those items!")
                    await bad_msg.delete(delay=5)
                    # Have them make the decision again (inefficient, but lmao)
                    continue

                for req in choice.reqs:
                    inv[req.name] -= req.amt if req.taken else 0
                    if inv[req.name] == 0:
                        del inv[req.name]

                dm.set_user_inventory(a.id, inv)
            else:
                choice = curr_op.to

            match choice.action:
                case "item":
                    stored = u.bp_weight(inv)
                    if stored >= r.BP_CAP:
                        msg = await ctx.reply(
                            "Your backpack was too full: "
                            "you have no choice but to ignore the items.",
                            mention_author=False
                        )
                    else:
                        name, (lb, ub) = curr_op.item
                        to_add = min(r.BP_CAP - stored, random.randint(lb, ub))
                        inv[name] = inv.get(name, 0) + to_add

                        msg = await ctx.reply(
                            f"You got {to_add} {name.title()}!",
                            mention_author=False
                        )
                    await msg.delete(delay=5)

                case "trade":
                    trader = r.mob(list(curr_op.encounters.keys())[0])
                    assert trader.trades is not None

                    to_include = {}
                    for item, trade in trader.trades.items():
                        if random.random() <= trade.prob:
                            to_include[item] = trade.reqs

                    # maybe vary the description based on a random list?
                    embed = discord.Embed(
                        title=trader.name.title(),
                        description=trader.dialogue
                    )
                    decision_view = w.Trade(a, to_include)
                    await adv_msg.edit(embed=embed, view=decision_view)
                    await decision_view.wait()

                case "exit":
                    end_cause = "win"
                    if journey == "enchanted forest":
                        badges = dm.get_user_badge(a.id)
                        dm.set_user_badge(a.id, badges | (1 << 5))
                    break

                case "fight":
                    # TODO
                    enemies = []
                    for m, probs in curr_op.encounters.items():
                        for p in probs:
                            if random.random() < p:
                                enemies.append(r.mob(m))

                    print(enemies)

            valid_ops = []
            weights = []
            for op in adv[choice.section][choice.subsec]:
                for s in op.spawns:
                    if s.lb <= dist <= s.ub:
                        valid_ops.append(op)
                        weights.append(s.weight)
                        break

            curr_op = random.choices(valid_ops, weights)[0]

        dm.set_user_inventory(a.id, inv)
        await adv_msg.edit(
            content=f"adventure finished. end cause: {end_cause}",
            embed=None, view=None
        )


async def setup(bot):
    await bot.add_cog(Adventure(bot))
