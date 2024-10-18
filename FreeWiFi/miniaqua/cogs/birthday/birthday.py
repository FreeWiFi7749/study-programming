import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, time
import pytz
import json
import os
import logging

logger = logging.getLogger(__name__)

tzinfo = pytz.timezone("Asia/Tokyo")

def load_data(file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('{}')
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(file_path, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_check.start()

    @commands.hybrid_group(name="birthday", description="誕生日・記念日に関するコマンド")
    async def birthday(self, ctx: commands.Context):
        pass

    # ホロメン登録用
    @birthday.command(name="regist", description="ホロメンの誕生日,記念日,記念数を登録")
    @commands.has_permissions(administrator=True)
    async def regist(self, ctx: commands.Context, name: str,  b_date: str, a_date: str, a_count: int):
        data = load_data("data/birthday/holomen.json")

        if name in data:
            await ctx.send(embed=discord.Embed(
                title="このホロメンは既に登録されています",
                color=discord.Color.yellow()
            ), ephemeral=True)
            logger.warning(f"ホロメン名: {name} は既に登録されています。")
            return

        birth_date = datetime.strptime(b_date, "%m%d").replace(tzinfo=tzinfo).isoformat()
        anni_date = datetime.strptime(a_date, "%m%d").replace(tzinfo=tzinfo).isoformat()
        data[name] = {"birthdate": birth_date, "annidate": anni_date, "annicount": a_count}
        
        save_data("data/birthday/holomen.json", data)
        
        logger.info(f"{name}の誕生日、記念日、記念数が登録されました。")
        
        await ctx.send(embed=discord.Embed(
            title="ホロメンの登録に成功しました",
            color=discord.Color.green(),
        ), ephemeral=True)
        
    
    @birthday.command(name="activate", description="ホロメンの誕生日、記念日の通知を有効にします")
    @commands.has_permissions(administrator=True)
    async def activate(self, ctx: commands.Context, channel: discord.TextChannel):
        data = load_data("data/birthday/serverinfo.json")
        
        if ctx.guild.id not in data:
            data[ctx.guild.id] = []

        if channel.id in data[ctx.guild.id]:
            await ctx.send(embed=discord.Embed(
                title="このチャンネルでは、既に通知が有効になっています",
                color=discord.Color.yellow()
            ), ephemeral=True)
            logger.warning(f"サーバーID: {ctx.guild.id} のチャンネルID: {channel.id} では、既に通知が有効になっています。")
            return

        data[ctx.guild.id].append(channel.id)
        save_data("data/birthday/serverinfo.json", data)
        await ctx.send(embed=discord.Embed(
            title="通知が有効になりました",
            color=discord.Color.green()
        ), ephemeral=True)
        logger.info(f"サーバーID: {ctx.guild.id} のチャンネルID: {channel.id} で通知が有効になりました。")
            
    @activate.error
    async def activate_error(self, ctx: commands.Context, error):
        if isinstance(error, app_commands.MissingPermissions):
            await ctx.send(embed=discord.Embed(
                title="権限が不足しています",
                description="このコマンドの実行には、「サーバー管理」の権限が必要です",
                color=discord.Color.red()
            ))
            logger.error("権限が不足しています。このコマンドの実行には、「サーバー管理」の権限が必要です。")
            
    
    @birthday.command(name="deactivate", description="ホロメンの誕生日・記念日通知を無効にします")
    @commands.has_permissions(administrator=True)
    async def deactivate(self, ctx: commands.Context):
        data = load_data("data/birthday/serverinfo.json")
            
        if ctx.guild.id not in data:
            await ctx.send(embed=discord.Embed(
                title="このサーバーでは通知が有効になっていません",
                color=discord.Color.yellow()
            ))
            logger.warning(f"サーバーID: {ctx.guild.id} では通知が有効になっていません。")
        else:
            data.pop(ctx.guild.id)
            logger.info(f"サーバーID: {ctx.guild.id} で通知が無効になりました。")

        await ctx.send(embed=discord.Embed(
            title="通知が無効になりました",
            color=discord.Color.green()
        ))
        save_data("data/birthday/serverinfo.json", data)
            
    @deactivate.error
    async def deactivate_error(self, ctx: commands.Context, error):
        if isinstance(error, app_commands.MissingPermissions):
            await ctx.send(embed=discord.Embed(
                title="権限が不足しています",
                description="このコマンドの実行には、「サーバー管理」の権限が必要です",
                color=discord.Color.red()
            ))
            logger.error("権限が不足しています。このコマンドの実行には、「サーバー管理」の権限が必要です。")
            
 
    @tasks.loop(time=time(hour=0, minute=0, tzinfo=tzinfo))
    async def daily_check(self):
        logger.info("daily_checkタスクが実行されました。")
        birth_data = load_data("data/birthday/holomen.json")
        server_data = load_data("data/birthday/serverinfo.json")
            
        today = datetime.now(tz=tzinfo).date()
        
        for name, value in birth_data.items():
            birth_date = datetime.fromisoformat(value["birthdate"]).date()
            anni_date = datetime.fromisoformat(value["annidate"]).date()
            
            if today == birth_date:
                for c in server_data.keys():
                    for channel_id in server_data[c]:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            await channel.send(f"今日は{name}ちゃんのお誕生日です！ぜひお祝いしましょう！")
                            logger.info(f"今日は{name}ちゃんのお誕生日です。")
                        else:
                            logger.error(f"チャンネルID: {channel_id} が見つかりませんでした。")
                    
            elif today == anni_date:
                birth_data[name]["annicount"] += 1
                annicount = birth_data[name]["annicount"]
                
                save_data("data/birthday/holomen.json", birth_data)
                    
                for c in server_data.keys():
                    for channel_id in server_data[c]:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            await channel.send(f"今日は{name}ちゃんの{annicount}周年の日です！ぜひお祝いしましょう！")
                            logger.info(f"今日は{name}ちゃんの{annicount}周年の日です。")
                        else:
                            logger.error(f"チャンネルID: {channel_id} が見つかりませんでした。")

async def setup(bot):
    await bot.add_cog(Birthday(bot))
