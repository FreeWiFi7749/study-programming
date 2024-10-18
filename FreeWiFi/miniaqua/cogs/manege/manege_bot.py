import discord
from discord.ext import commands
import sys
import subprocess
import platform
import asyncio
import time
from dotenv import load_dotenv
import os

from utils import api

load_dotenv()

api_url = os.getenv('TTS_ISOTOPE_API_URL')

class ManagementBotCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def rstart_bot(self):
        try:
            if platform.system() == "Linux":
                subprocess.Popen(["sudo", "systemctl", "restart", "chibiaqua.service"])
            elif platform.system() == "Darwin":
                subprocess.Popen(["/bin/sh", "-c", "sleep 1; exec python3 " + " ".join(sys.argv)])
            else:
                print("このOSはサポートされていません。")
                return
            await self.bot.close()
        except Exception as e:
            print(f"再起動中にエラーが発生しました: {e}")

    @commands.group(name='admin', hidden=True)
    @commands.is_owner()
    async def admin(self, ctx):
        """管理者専用のコマンド"""
        if ctx.invoked_subcommand is None:
            await ctx.send("このコマンドは管理者専用です。", ephemeral=True)


    @admin.command(name='menu')
    async def menu(self, ctx):
        """管理者専用のコマンド"""
        e = discord.Embed(title="管理者専用のコマンド", color=0xFF8FDF)
        e.add_field(name="restart", value="Botを再起動する", inline=False)
        e.add_field(name="sync", value="コマンドを同期する", inline=False)
        e.add_field(name="shutdown", value="Botを終了する", inline=False)
        await ctx.send(embed=e)

    @admin.command(name='restart', hidden=True)
    @commands.is_owner()
    async def restart(self, ctx):
        """Botを再起動する"""
        msg = await ctx.send('10秒後にBotを再起動します')
        for i in range(9, 0, -1):
            await asyncio.sleep(1)
            await msg.edit(content=f"{i}秒後にBotを再起動します")
            if i == 1:
                await msg.edit(content="Botの再起動を開始します...")
                
        await self.rstart_bot()

    @commands.hybrid_command(name='ping', hidden=True)
    async def ping(self, ctx):
        """BotのPingを表示します"""
        start_time = time.monotonic()
        api_ping = await api.measure_api_ping()
        e = discord.Embed(title="Pong!", color=0xFF8FDF)
        e.add_field(name="API Ping", value=f"{round(api_ping)}ms" if api_ping else "測定失敗", inline=True)
        e.add_field(name="WebSocket Ping", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        sent_message = await ctx.send(embed=e)
        end_time = time.monotonic()

        bot_ping = round((end_time - start_time) * 1000)

        e.add_field(name="Bot Ping", value=f"{bot_ping}ms", inline=True)
        await sent_message.edit(embed=e)

    @admin.command(name='shutdown', hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Botを終了します"""
        await ctx.send("Botを終了します。")
        await self.bot.close()

    @admin.command(name='sync', hidden=True)
    @commands.is_owner()
    async def sync(self, ctx):
        """コマンドを同期する"""
        await ctx.send("コマンドが同期されました。")
        self.bot.tree.clear_commands(guild=None)
        await self.bot.tree.sync()


    @restart.error
    async def restart_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("このコマンドを使用する権限がありません。", ephemeral=True)
        else:
            await ctx.send(f"エラーが発生しました: {error}", ephemeral=True)

    @ping.error
    async def ping_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("このコマンドを使用する権限がありません。", ephemeral=True)
        else:
            await ctx.send(f"エラーが発生しました: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ManagementBotCog(bot))
