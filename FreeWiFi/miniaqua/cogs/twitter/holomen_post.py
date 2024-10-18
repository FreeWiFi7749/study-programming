import discord
from discord.ext import commands, tasks
import json
import os
import tweepy
import httpx
import requests
import os
import json
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv

load_dotenv()

class TwitterPoster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = self.setup_twitter_api()
        self.twitter_loop.start()

    def setup_twitter_api(self):
        auth = tweepy.OAuth2BearerHandler(os.getenv('TWITTER_BEARER_TOKEN'))
        return tweepy.API(auth)

    def get_guild_data(self, guild_id):
        data_path = f'data/twitter/{guild_id}/settings.json'
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                return json.load(f)
        return {}

    @tasks.loop(minutes=5)
    async def twitter_loop(self):
        for guild in self.bot.guilds:
            data = self.get_guild_data(guild.id)
            if not data:
                continue

            channel = self.bot.get_channel(data.get('channel_id'))
            if not channel:
                continue

            webhook = await self.get_or_create_webhook(channel)

            accounts = data.get('accounts', [])
            post_types = data.get('post_types', [])

            for account_name in accounts:
                tweets = self.api.user_timeline(screen_name=account_name, count=5, tweet_mode='extended')
                for tweet in reversed(tweets):
                    if 'tweets' in post_types and not hasattr(tweet, 'retweeted_status') and not tweet.is_quote_status and not tweet.in_reply_to_status_id:
                        await self.post_tweet(webhook, account_name, tweet)
                    elif 'retweets' in post_types and hasattr(tweet, 'retweeted_status'):
                        await self.post_tweet(webhook, account_name, tweet)
                    elif 'replies' in post_types and tweet.in_reply_to_status_id:
                        await self.post_tweet(webhook, account_name, tweet)

    async def get_or_create_webhook(self, channel):
        """チャンネルにWebhookが存在しない場合、作成"""
        webhooks = await channel.webhooks()
        for webhook in webhooks:
            if webhook.name == "tweet from ChibiAqua":
                return webhook

        return await channel.create_webhook(name="tweet from ChibiAqua")

    async def post_tweet(self, webhook, account_name, tweet):
        if hasattr(tweet, 'retweeted_status'):
            content = f"🔁 {tweet.user.name} リツイート: {tweet.retweeted_status.full_text}"
        elif tweet.is_quote_status:
            content = f"🔁 {tweet.user.name} 引用リツイート: {tweet.full_text}\n引用元: {tweet.quoted_status.full_text}"
        elif tweet.in_reply_to_status_id:
            content = f"💬 {tweet.user.name} リプライ: {tweet.full_text}"
        else:
            content = f"📢 {tweet.user.name} ツイート: {tweet.full_text}"

        await webhook.send(content, username=account_name, avatar_url=tweet.user.profile_image_url)

async def setup(bot):
    await bot.add_cog(TwitterPoster(bot))