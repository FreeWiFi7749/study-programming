import discord
import asyncio
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timezone
import pytz
import logging
import random

from utils.youtube_scraper import load_titles_from_json

load_dotenv()

STATS_PATH = "data/tts/v00/stats"
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def load_stats(filename):
    if not os.path.exists(STATS_PATH):
        os.makedirs(STATS_PATH, exist_ok=True)
    filepath = os.path.join(STATS_PATH, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {"count": 0}

presences = [
    {"type": "Playing", "name": "BOT情報を更新中...", "state": "", "status": "online"},
    {"type": "Playing", "name": "AI情報を更新中...", "state": "", "status": "online"},
    {"type": "Listening", "name": "音楽情報を更新中...", "state": "", "status": "online"},
    {"type": "Playing", "name": "こんあくあ〜", "state": "", "status": "online"},

]

async def update_presence(bot):
    index = 0
    while not bot.is_closed():
        total_member_count = sum(guild.member_count for guild in bot.guilds)
        total_guild_count = len(bot.guilds)

        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(timezone.utc).astimezone(jst)
        last_update = now.strftime("%Y/%m/%d")

        custom_presence_bot = {
            "type": "Playing",
            "name": f"BOT情報: {last_update}時点",
            "state": f"サーバー数:{total_guild_count}サーバー / ユーザー数:{total_member_count}人",
            "status": "online"
        }
        custom_presence_ai = {
            "type": "Playing",
            "name": f"AI情報: {last_update}時点",
            "state": "APIステータス N/A",
            "status": "online"
        }

        video_titles = load_titles_from_json("data/music/titles.json")

        custom_presence_music = {
            "type": "Listening",
            "name": "🎵",
            "state": f"現在の曲: {random.choice(video_titles) if video_titles else '曲が見つかりません'}",
            "status": "online",
            "activity": discord.Activity(
                type=discord.ActivityType.listening,
                name=f"🎵{random.choice(video_titles) if video_titles else '曲が見つかりません'}"
            )
        }
        presences[index] = custom_presence_bot if index == 0 else custom_presence_ai if index == 1 else custom_presence_music if index == 2 else presences[3]

        #presence = presences[index]
        #activity_type = getattr(discord.ActivityType, presence["type"].lower(), discord.ActivityType.playing)

        #logging.debug(f"Setting presence: {presence}, activity_type: {activity_type}")

        #if presence["state"] != "":
        #    activity = discord.Activity(
        #        type=activity_type,
        #        name=presence["name"],
        #        state=presence["state"]
        #    )
        #else:
        #    activity = discord.Activity(
        #        type=activity_type,
        #        name=presence["name"]
        #    )

        #await bot.change_presence(activity=activity, status=discord.Status[presence["status"]])
        await bot.change_presence(activity=custom_presence_music["activity"], status=discord.Status[custom_presence_music["status"]])
        #logging.info(f"Presenceを更新しました: {presence}")

        await asyncio.sleep(120)
        #await asyncio.sleep(10)

        if index == len(presences):
            index = 0
