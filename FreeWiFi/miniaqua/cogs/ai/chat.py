import discord
from discord.ext import commands
from openai import OpenAI
import json
import os
from typing import Optional

api_key = os.getenv("OPENAI_API_KEY_DEV")
if not api_key:
    raise ValueError("APIキーが設定されていません。")

client = OpenAI(api_key=api_key)

class ChatCogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_messages_channels = {}
        self.user_messages_dm = {}

    async def load_prompt(self):
        file_path = "config/ai/prompt.json"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        return ""

    @commands.hybrid_command(name='chat')
    async def chat(self, ctx, *, message: str):
        await ctx.defer()
        prompt = await self.load_prompt()
        if prompt:
            response = await self.get_chatgpt_response(prompt, message, ctx.author.id)
            await ctx.reply(response)
        else:
            await ctx.reply("プロンプトが設定されていません。")

    async def get_chatgpt_response(self, prompt, message, user_id, is_dm=False):
        if is_dm:
            if user_id not in self.user_messages_dm:
                self.user_messages_dm[user_id] = []
            self.user_messages_dm[user_id].append(message)
            full_prompt = f"{prompt}\n" + "\n".join(self.user_messages_dm[user_id])
        else:
            if user_id not in self.user_messages_channels:
                self.user_messages_channels[user_id] = []
            self.user_messages_channels[user_id].append(message)
            full_prompt = f"{prompt}\n" + "\n".join(self.user_messages_channels[user_id])
        
        response = client.chat.completions.create(model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": full_prompt}
        ])
        return response.choices[0].message.content

    @commands.hybrid_group(name='config')
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
        return
    
    @config.command(name='ai_chat_option')
    async def ai_chat_option(self, ctx, channel: Optional[discord.TextChannel | discord.ForumChannel], enabled: bool):
        if channel is None:
            channel = ctx.channel
        else:
            channel = channel
        guild_id = ctx.guild.id
        file_path = f"data/ai/chat/guilds/{guild_id}/channels.json"
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                channels = json.load(f)
        else:
            channels = {}

        channels[str(channel.id)] = enabled

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(channels, f)

        await ctx.reply(f"チャンネル {channel.mention} の自動返信が {'有効' if enabled else '無効'} になりました。")

    @config.command(name='ai_chat_dm')
    async def ai_chat_dm(self, ctx, enabled: bool):
        id = ctx.author.id
        file_path = f"data/ai/chat/users/{id}/dm.json"
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                channels = json.load(f)
        else:
            channels = {}

        channels['dm'] = enabled

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(channels, f)

        await ctx.reply(f"DMの自動返信が {'有効' if enabled else '無効'} になりました。")

    @commands.Cog.listener()
    async def on_message(self, message):
        prompt = await self.load_prompt()
        channels = {}
        if message.author == self.bot.user:
            return
        
        if message.guild is None:
            await self.handle_dm_response(message, prompt)
            return
        
        guild_id = message.guild.id
        file_path = f"data/ai/chat/guilds/{guild_id}/channels.json"
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                channels = json.load(f)

        if str(message.channel.id) in channels and channels[str(message.channel.id)]:
            await message.channel.typing()
            response = await self.get_chatgpt_response(prompt, message.content, message.author.id, is_dm=False)
            await message.reply(response, mention_author=False)

    async def handle_dm_response(self, message, prompt):
        id = message.author.id
        dm_file_path = f"data/ai/chat/users/{id}/dm.json"
        if os.path.exists(dm_file_path):
            with open(dm_file_path, 'r', encoding='utf-8') as f:
                dm_settings = json.load(f)
                if dm_settings.get('dm', True):
                    await message.channel.typing()
                    response = await self.get_chatgpt_response(prompt, message.content, message.author.id, is_dm=True)
                    await message.author.send(response)

async def setup(bot):
    await bot.add_cog(ChatCogs(bot))