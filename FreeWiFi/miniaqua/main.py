import discord
from discord.ext import commands

from dotenv import load_dotenv
import os
import re
import pathlib
from datetime import datetime
import logging
import traceback
import sys
import colorlog

from utils import presence
from utils.logging import save_log
from utils.youtube_scraper import PLAYLIST_URLS, SAVE_PATH, save_titles_to_json, scrape_playlist_titles_with_api

load_dotenv()
api_key = os.getenv('YOUTUBE_API_KEY')

session_id = None

class SessionIDHandler(logging.Handler):
    def emit(self, record):
        global session_id
        message = record.getMessage()
        match = re.search(r'Session ID: ([a-f0-9]+)', message)
        if match:
            session_id = match.group(1)
            print(f"セッションIDを検出しました: {session_id}")

logger = logging.getLogger('discord.gateway')
logger.setLevel(logging.INFO)
logger.addHandler(SessionIDHandler())

# Colorlogの設定
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white'
    }
))

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.handlers = [handler]

TOKEN = os.getenv('BOT_TOKEN')
command_prefix = ['aq/']
main_guild_id = int(os.getenv('MAIN_GUILD_ID'))

class MyBot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initialized = False
        self.cog_classes = {}

    async def logo(self):
        logo_log = logging.getLogger('logo')
        logo_log.debug("┌──────────────────────────────────────────────────────────────────────────┐")
        logo_log.debug("│                             MiniAqua                                     │")
        logo_log.debug("├──────────────────────────────────────────────────────────────────────────│")
        logo_log.debug("│                        Authors: FreeWiFi                                 │")
        logo_log.debug("├──────────────────────────────────────────────────────────────────────────│")
        logo_log.debug("│                         discord.py: v%s                              |", discord.__version__)
        logo_log.debug("│                           Python: v%s                                |", '.'.join(map(str, sys.version_info[:3])))
        logo_log.debug("└──────────────────────────────────────────────────────────────────────────┘")

    async def setup_hook(self):
        self.loop.create_task(self.after_ready())

    async def after_ready(self):
        logo_log = logging.getLogger('logo')
        await self.wait_until_ready()
        await self.logo()
        await self.change_presence(activity=discord.Game(name="起動中.."), status=discord.Status.idle)
        await self.load_cogs('cogs')
        await self.tree.sync()
        logo_log.debug('------')
        logo_log.debug('All cogs have been loaded and bot is ready.')
        logo_log.debug('------')
        #await self.update_playlists()
        #logo_log.debug('プレイリストの更新が完了しました。')
        await self.loop.create_task(presence.update_presence(self))
        logo_log.info('BOTの起動が完了しました。')

    async def update_playlists(self):
        self.logo_log = logging.getLogger('logo')
        self.logo_log.debug('プレイリストの更新を開始します。')
        all_titles = []
        for url in PLAYLIST_URLS:
            titles = scrape_playlist_titles_with_api(url, api_key)
            all_titles.extend(titles)
            self.logo_log.debug(f'{url}のプレイリストの更新が完了しました。')
        
        save_titles_to_json(all_titles, SAVE_PATH)
        self.logo_log.debug('すべてのプレイリストのタイトルが保存されました。')
        
    async def on_ready(self):
        log_data = {
            "event": "BotReady",
            "description": f"{self.user} has successfully connected to Discord.",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "session_id": session_id
        }
        save_log(log_data)
        if not self.initialized:
            try:
                logging.info("Bot is ready.")
            except Exception as e:
                logging.error(f"Error during startup: {e}")
            self.initialized = True

    async def load_cogs(self, folder_name: str):
        cur = pathlib.Path('.')
        for p in cur.glob(f"{folder_name}/**/*.py"):
            if p.stem == "__init__" or "backup" in p.parts:
                continue
            try:
                cog_path = p.relative_to(cur).with_suffix('').as_posix().replace('/', '.')
                await self.load_extension(cog_path)
                logging.info(f'{cog_path} loaded successfully.')
            except commands.ExtensionFailed as e:
                traceback.print_exc()
                logging.error(f'Failed to load extension {p.stem}: {e}\nFull error: {e.__cause__}')

intent: discord.Intents = discord.Intents.all()
bot = MyBot(command_prefix=command_prefix, intents=intent, help_command=None)
bot.run(TOKEN)
