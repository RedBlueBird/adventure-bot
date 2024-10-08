from string import Template

import discord
from discord.ext import commands
from discord.ext.commands import Context

import resources as r
from helpers import util as u

RARITIES = {
    "C": "Common",
    "R": "Rare",
    "E": "Epic",
    "EX": "Exclusive",
    "L": "Legendary",
    "M": "N/A",
    "NA": "N/A",
}


def fill_args(card: dict, level: int, type_: str):
    param = [
        "block",
        "absorb",
        "heal",
        "tramp",
        "damage",
        "self_damage",
        "pierce_damage",
        "crush",
        "revenge",
        "lich_revenge",
        "inverse_damage",
    ]

    on_hand = card.get("on_hand", {})
    args = {"level": level}
    for p in param:
        if p in card:
            args[p] = card[p]

        if p in on_hand:
            args[f"on_hand_{p}"] = on_hand[p]

        # c_attr = "_".split(i[len("eff_app"):])
        # card[i][c_attr[0]][c_attr[1]][c_attr[2]] = round(card[i][c_attr[0]][c_attr[1]][c_attr[2]] * lvl)
        if "eff_app" in card:
            curr_dir = ["eff_app"]
            for side in card["eff_app"]:
                curr_dir.append(side)
                for effect in card["eff_app"][side]:
                    curr_dir.append(effect)
                    for attr in card["eff_app"][side][effect]:
                        curr_dir.append(attr)
                        if attr in param:
                            args["_".join(curr_dir)] = card["eff_app"][side][effect][attr]
                        del curr_dir[-1]
                    del curr_dir[-1]
                del curr_dir[-1]

    return Template(card[type_]).safe_substitute(args)


class EntitySearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(aliases=["in", "check"], description="Looks up info on entities.")
    async def info(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            embed = (
                discord.Embed(title="Here's the things you can search up:")
                .add_field(name="Cards", value=f"`{r.PREF}info card`")
                .add_field(name="Monsters", value=f"`{r.PREF}info monster`")
                .add_field(name="Items", value=f"`{r.PREF}info item`")
                .add_field(name="Effects", value=f"`{r.PREF}info effect`")
            )
            await ctx.reply(embed=embed)

    @info.command()
    async def card(self, ctx: Context, name: str, level: int = 1):
        max_level = 15
        if not 1 <= level <= max_level:
            await ctx.reply(f"The card level has to be between 1 and {max_level}!")
            return

        card = u.cards_dict(level, " ".join(name.lower().split("_")))
        if card is None:
            await ctx.reply("The requested card was not found!")
            return

        info_str = [
            f"**Name:** {card['name']}",
            f"**Level:** {level}",
            f"**Rarity:** {RARITIES[card['rarity']]}",
            f"**Energy Cost:** {card['cost']}",
            f"**Crit:** {card['crit']}%",
            f"**Priority:** {card['priority']}",
        ]

        if card["rarity"] == "M":
            info_str.append("**[Monster Card]** - Unobtainable")
        if card["rarity"] == "EX":
            info_str.append("**[Exclusive Card]** - Obtainable in events")

        embed = discord.Embed(title="Card's info:", color=discord.Color.green())
        embed.add_field(name="Description:", value="\n".join(info_str), inline=False)
        embed.add_field(name="Uses:", value=fill_args(card, level, "desc"), inline=False)
        embed.add_field(name="On Crit:", value=fill_args(card, level, "cdesc"), inline=False)
        embed.add_field(name="Brief:", value=card["brief"], inline=False)

        await ctx.send(embed=embed)

    @info.command()
    async def monster(self, ctx: Context, name: str, level: int = 1):
        mob = r.mob(name, level)
        if mob is None:
            await ctx.reply("The requested item was not found!")
            return

        info = [
            f"**Level:** {level}",
            f"**Rarity:** {RARITIES[mob.rarity]}",
            f"**Energy Lag:** {mob.energy_lag} turns",
            f"**Health:** {mob.health}",
            f"**Stamina:** {mob.stamina}",
        ]

        embed = discord.Embed(title=f"{mob.name}:", color=discord.Color.green())
        embed.add_field(name="Description:", value="\n".join(info), inline=False)
        embed.add_field(name="Brief:", value=f"*{mob.brief}*", inline=False)

        await ctx.send(embed=embed)

    @info.command()
    async def item(self, ctx: Context, name: str):
        item = r.item(name)
        if item is None:
            await ctx.reply("The requested item was not found!")
            return

        name = item.name
        info_str = [
            f"**Weight:** {item.weight}",
            f"**Rarity:** {RARITIES[item.rarity]}",
            f"**Accuracy:** {item.acc}%",
            f"**Critical Chance:** {item.crit}%",
            f"**One Use:** {item.one_use}",
            f"**Use In Battle:** {item.in_battle}",
            f"**Sell Price:** {item.sell}gc",
            f"**Abbreviation:** {item.abb}",
        ]

        embed = discord.Embed(title=f"{name}:", description=None, color=discord.Color.green())
        embed.add_field(name="Description: ", value="\n".join(info_str), inline=False)
        embed.add_field(name="Uses: ", value=item.description, inline=False)
        embed.add_field(name="Brief: ", value=f"*{item.brief}*", inline=False)

        """
        if "journal" in item_info:  
            embed.add_field(name="Scout's Journal: ", value="*" + item_info["journal"] + "*", inline=False)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        """

        if name.lower() in r.ICONS:
            icon = r.ICONS[name.lower()]
            embed.set_image(url=f"https://cdn.discordapp.com/emojis/{icon.id}.png")
        await ctx.send(embed=embed)

    @info.command()
    async def effect(self, ctx: Context, name: str):
        eff = r.effect(name)
        if eff is None:
            await ctx.reply("The requested effect was not found!")
            return

        embed = discord.Embed(title="Effect's info:", description=None, color=discord.Color.green())
        embed.add_field(name="Description: ", value=f"**Name:** {eff.name}", inline=False)
        embed.add_field(name="Uses: ", value=eff.description, inline=False)
        embed.set_image(url=f"https://cdn.discordapp.com/emojis/{r.ICONS[eff.name].id}.png")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EntitySearch(bot))
