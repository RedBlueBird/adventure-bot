from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks


class Template(commands.Cog, name="template"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="testcommand",
        description="This is a testing command that does nothing.",
    )
    # This will only allow non-blacklisted members to execute the command
    @checks.not_blacklisted()
    # This will only allow owners of the bot to execute the command -> config.json
    @checks.is_owner()
    async def testcommand(self, ctx: Context):
        """
        This is a testing command that does nothing.

        :param context: The application command context.
        """
        await ctx.reply("yeah yeah")


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot):
    await bot.add_cog(Template(bot))
