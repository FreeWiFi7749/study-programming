import discord
from discord.ext import commands

class VideoNCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='test_video_n')
    async def test_video_n(self, ctx):
        await ctx.send("Video N")

async def setup(bot):
    await bot.add_cog(VideoNCog(bot))