import discord
from discord.ext import commands

class MusicNCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='test_music_n')
    async def test_music_n(self, ctx):
        await ctx.send("Music N")

async def setup(bot):
    await bot.add_cog(MusicNCog(bot))