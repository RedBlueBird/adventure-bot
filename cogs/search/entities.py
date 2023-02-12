import discord
from discord.ext import commands
from discord.ext.commands import Context

import util as u


RARITIES = {
    "C": "Common", "R": "Rare", "E": "Epic", "EX": "Exclusive",
    "L": "Legendary", "M": "N/A", "NA": "N/A"
}


class EntitySearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(aliases=["in", "check"], description="Looks up info on entities.")
    async def info(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="Here's the things you can search up:") \
                .add_field(name="Cards", value="`a.info card`") \
                .add_field(name="Monsters", value="`a.info monster`") \
                .add_field(name="Items", value="`a.info item`") \
                .add_field(name="Effects", value="`a.info effect`")
            await ctx.reply(embed=embed)

    @info.command()
    async def card(self, ctx: Context, name: str, level: int = 1):
        max_level = 15
        if not 1 <= level <= max_level:
            await ctx.reply(f"The card level has to be between 1 and {max_level}!")
            return

        card_info = u.cards_dict(level, " ".join(name.lower().split("_")))
        info_str = [
            f"**Name:** {card_info['name']}",
            f"**Level:** {level}",
            f"**Rarity:** {RARITIES[card_info['rarity']]}",
            f"**Energy Cost:** {card_info['cost']}",
            f"**Accuracy:** {card_info['acc']}%",
            f"**Critical Chance:** {card_info['crit']}%"
        ]

        if card_info["rarity"] == "M":
            info_str.insert(len(info_str), "**[Monster Card]** - Unobtainable")
        if card_info["rarity"] == "EX":
            info_str.insert(len(info_str), "**[Exclusive Card]** - Obtainable in events")

        embed = discord.Embed(title="Card's info:", description=None, color=discord.Color.green())
        embed.add_field(name="Description: ", value="\n".join(info_str), inline=False)
        embed.add_field(name="Uses: ", value=u.fill_args(card_info, level), inline=False)
        embed.add_field(name="Brief: ", value=card_info["brief"], inline=False)
        """
        if "journal" in card_info:
            embed.add_field(name="Scout's Journal: ", value="*" + card_info["journal"] + "*", inline=False)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        """
        await ctx.send(embed=embed)

    @info.command()
    async def monster(self, ctx: Context, name: str, level: int = 1):
        mob_info = u.mobs_dict(level, " ".join(name.lower().split("_")))
        info_str = [
            f"**Name:** {mob_info['name']}",
            f"**Level:** " + str(level),
            f"**Rarity:** {RARITIES[mob_info['rarity']]}",
            f"**Energy Lag:** {mob_info['energy_lag']} turns",
            f"**Health:** {mob_info['health']}",
            f"**Stamina:** {mob_info['stamina']}"
        ]

        embed = discord.Embed(title="Mob's info:", description=None, color=discord.Color.green())
        embed.add_field(name="Description: ", value="\n".join(info_str), inline=False)
        embed.add_field(name="Brief: ", value=f"*{mob_info['brief']}*", inline=False)
        """
        if "tip" in mob_info:
            embed.add_field(name="Fighting Tips: ", value="*" + mob_info["tip"] + "*", inline=False)
        if "journal" in mob_info:
            embed.add_field(name="Scout's Journal: ", value="*" + mob_info["journal"] + "*", inline=False)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        """
        await ctx.send(embed=embed)

    @info.command()
    async def item(self, ctx: Context, name: str):
        item_info = u.items_dict(" ".join(name.lower().split("_")))
        name = item_info["name"]
        info_str = [
            f"**Name:** {name}",
            f"**Weight:** {item_info['weight']}",
            f"**Rarity:** {RARITIES[item_info['rarity']]}",
            f"**Accuracy:** {item_info['acc']}%",
            f"**Critical Chance:** {item_info['crit']}%",
            f"**One Use:** {item_info['one_use']}",
            f"**Use In Battle:** {item_info['in_battle']}",
            f"**Sell Price:** {item_info['sell']}gc",
            f"**Abbreviation:** {item_info['abb']}"
        ]

        embed = discord.Embed(title="Item's info:", description=None, color=discord.Color.green())
        embed.add_field(name="Description: ", value="\n".join(info_str), inline=False)
        embed.add_field(name="Uses: ", value=item_info["description"], inline=False)
        embed.add_field(name="Brief: ", value=f"*{item_info['brief']}*", inline=False)

        """
        if "journal" in item_info:  
            embed.add_field(name="Scout's Journal: ", value="*" + item_info["journal"] + "*", inline=False)
        embed.set_thumbnail(url=ctx.author.avatar.url)a.
        """
        # print(u.ICON[item_info['name'].lower()])
        if name.lower() in u.ICON:
            icon = u.ICON[name.lower()]
            icon_id = icon[icon.rfind(":") + 1:-1]
            embed.set_image(url=f"https://cdn.discordapp.com/emojis/{icon_id}.png")
        await ctx.send(embed=embed)

    @info.command()
    async def effect(self, ctx: Context, name: str):
        fx_info = u.fx_dict(" ".join(name.lower().split("_")))
        embed = discord.Embed(title="Effect's info:", description=None, color=discord.Color.green())
        embed.add_field(name="Description: ", value=f"**Name:** {fx_info['name']}", inline=False)
        embed.add_field(name="Uses: ", value=fx_info["description"], inline=False)
        embed.set_image(
            url=f"https://cdn.discordapp.com/emojis/"
                f"{u.CONVERT[fx_info['name'].lower()][4:-1]}.png"
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EntitySearch(bot))
