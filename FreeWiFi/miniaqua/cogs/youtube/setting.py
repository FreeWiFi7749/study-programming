import discord
from discord.ext import commands

class SettingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='test_setting')
    async def test_setting(self, ctx):
        await ctx.send("Setting")

async def setup(bot):
    await bot.add_cog(SettingCog(bot))