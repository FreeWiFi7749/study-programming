from discord.ext import commands
import discord
from discord import app_commands
import re
import uuid
import json
from pathlib import Path
from typing import List

# データの保存
def save_data(file_path: Path, data: dict):
    """指定されたファイルにデータを保存する"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# データの読み込み
def load_data(file_path: Path) -> dict:
    """指定されたファイルからデータを読み込む"""
    if file_path.exists():
        with file_path.open('r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# ボタン用のクラス
class PollButton(discord.ui.Button):
    def __init__(self, label: str, poll_id: str, choice_index: int, emoji: str = None):
        super().__init__(label=label, style=discord.ButtonStyle.primary, emoji=emoji)
        self.poll_id = poll_id
        self.choice_index = choice_index

    async def callback(self, interaction: discord.Interaction):
        poll_path = Path(f'data/polls/{interaction.guild.id}/{self.poll_id}.json')
        
        poll_data = load_data(poll_path)
        if not poll_data:
            await interaction.response.send_message("この投票は既に終了しています。", ephemeral=True)
            return

        # 投票の集計を更新
        poll_data['answers'][self.choice_index][2] += 1
        
        save_data(poll_path, poll_data)

        await interaction.response.send_message(f"「{poll_data['answers'][self.choice_index][1]}」に投票しました！」", ephemeral=True)

# 排他的投票ボタン用のクラス
class ExclusivePollButton(discord.ui.Button):
    def __init__(self, label: str, poll_id: str, choice_index: int, emoji: str = None):
        super().__init__(label=label, style=discord.ButtonStyle.primary, emoji=emoji)
        self.poll_id = poll_id
        self.choice_index = choice_index

    async def callback(self, interaction: discord.Interaction):
        poll_path = Path(f'data/polls/{interaction.guild.id}/{self.poll_id}.json')
        poll_data = load_data(poll_path)
        if not poll_data:
            await interaction.response.send_message("この投票は既に終了しています。", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        # 既に投票しているか確認
        for answer in poll_data['answers']:
            if user_id in answer[3]:
                answer[3].remove(user_id)
                answer[2] -= 1

        # 新しい選択肢に投票
        poll_data['answers'][self.choice_index][2] += 1
        poll_data['answers'][self.choice_index][3].append(user_id)
        save_data(poll_path, poll_data)
        await interaction.response.send_message(f"「{poll_data['answers'][self.choice_index][1]}」に投票先を変更しました！", ephemeral=True)

# 投票作成用のビュー
class PollView(discord.ui.View):
    def __init__(self, poll_id: str, choices: list, exclusive: bool = False):
        super().__init__(timeout=None)
        for index, choice in enumerate(choices):
            emoji = f"{index+1}\N{COMBINING ENCLOSING KEYCAP}"
            if exclusive:
                self.add_item(ExclusivePollButton(label=choice[1], poll_id=poll_id, choice_index=index, emoji=emoji))
            else:
                self.add_item(PollButton(label=choice[1], poll_id=poll_id, choice_index=index, emoji=emoji))

# 投票集計用のコマンド
class PollsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def save_poll_data(self, guild_id: int, poll_id: str, data: dict, message_id: int):
        """投票データを保存する"""
        active_polls_path = Path(f'data/polls/{guild_id}/{poll_id}.json')
        data['message_id'] = message_id
        save_data(active_polls_path, data)

    @commands.hybrid_group(name='polls', aliases=['vote'])
    async def polls_group(self, ctx: commands.Context):
        """投票に関するコマンド"""
        await ctx.send("投票に関するサブコマンドを使ってください")

    @polls_group.command(name='poll', aliases=['po'])
    async def quickpoll(self, ctx: commands.Context, *, 質問と選択肢: str):
        """複数投票可能な投票を作成します。"""
        args = re.split(r'[ 　]+', 質問と選択肢)

        if len(args) < 3:
            return await ctx.send('質問と最低2つの選択肢を入力してください。')

        question = args[0]
        choices = args[1:]

        if len(choices) > 20:
            return await ctx.send('選択肢は最大20個までです。')

        poll_id = str(uuid.uuid4())

        poll_data = {
            "question": question,
            "answers": [],
            "author": ctx.author.id,
            "multiple": True
        }

        for index, choice in enumerate(choices):
            if ':' in choice:
                emoji, text = choice.split(':', 1)
            else:
                emoji = f"{index+1}\N{COMBINING ENCLOSING KEYCAP}"
                text = choice
            poll_data["answers"].append([emoji, text, 0])

        embed = discord.Embed(
            title=question,
            description="投票が作成されました。\n以下のボタンから投票してください。\nこの投票は**複数投票**が可能です。",
            color=0x00ff00
        )
        embed.add_field(name="投票の選択肢", value="\n".join([f"{emoji} {text}" for emoji, text, _ in poll_data["answers"]]), inline=False)
        embed.set_footer(text="/polls end で終了")
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        poll_message = await ctx.send(embed=embed)

        view = PollView(poll_id=poll_id, choices=poll_data['answers'])
        await poll_message.edit(view=view)

        await self.save_poll_data(ctx.guild.id, poll_id, poll_data, poll_message.id)

    @polls_group.command(name='expoll', aliases=['exclusivepoll'])
    async def exclusive_poll(self, ctx: commands.Context, *, 質問と選択肢: str):
        """一つの選択肢しか選べない投票を作成します。"""
        args = re.split(r'[ 　]+', 質問と選択肢)

        if len(args) < 3:
            return await ctx.send('質問と最低2つの選択肢を入力してください。')

        question = args[0]
        choices = args[1:]

        if len(choices) > 20:
            return await ctx.send('選択肢は最大20個までです。')

        poll_id = str(uuid.uuid4())

        poll_data = {
            "question": question,
            "answers": [[f"{index+1}", choice, 0, []] for index, choice in enumerate(choices)],  # 4番目の要素にユーザーIDのリストを追加
            "author": ctx.author.id,
            "exclusive": True
        }

        embed = discord.Embed(
            title=question,
            description="以下のボタンから投票してください。",
            color=0x00ff00
        )
        embed.add_field(name="投票の選択肢", value="\n".join([f"{emoji} {text}" for emoji, text, _, _ in poll_data["answers"]]), inline=False)
        embed.set_footer(text="/polls end で終了")
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        poll_message = await ctx.send(embed=embed)

        view = PollView(poll_id=poll_id, choices=poll_data['answers'], exclusive=True)
        await poll_message.edit(view=view)

        await self.save_poll_data(ctx.guild.id, poll_id, poll_data, poll_message.id)

    async def poll_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """オートコンプリート用の関数"""
        guild_id = interaction.guild.id
        polls_path = Path(f'data/polls/{guild_id}')
        choices = []

        if polls_path.exists() and polls_path.is_dir():
            for poll_file in polls_path.glob('*.json'):
                poll = load_data(poll_file)
                if poll and current.lower() in poll['question'].lower():
                    choices.append(app_commands.Choice(name=poll['question'], value=poll_file.stem))

        return choices[:25]

    @app_commands.command(name="sum", description="指定した投票の集計をします。")
    @app_commands.autocomplete(poll_id=poll_autocomplete)
    async def sum_poll(self, interaction: discord.Interaction, poll_id: str):
        """指定した投票の集計をします。"""
        guild_id = interaction.guild.id
        poll_file = Path(f'data/polls/{guild_id}/{poll_id}.json')
        poll = load_data(poll_file)

        if not poll:
            await interaction.response.send_message("指定された投票が見つかりません。", ephemeral=True)
            return

        results = sorted(poll["answers"], key=lambda x: x[2], reverse=True)
        total_votes = sum(choice[2] for choice in poll["answers"])
        result_text = ""
        for index, (emoji, choice, votes) in enumerate(results, start=1):
            percentage = (votes / total_votes) * 100 if total_votes > 0 else 0
            result_text += f"{emoji}\N{COMBINING ENCLOSING KEYCAP} {choice}: {votes}票 ({percentage:.1f}%)\n"

        embed = discord.Embed(
            title=poll['question'],
            description=result_text,
            color=0x00ff00
        )
        message_link = f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{poll['message_id']}"
        embed.add_field(name="投票を見る", value=f"[メッセージへ]({message_link})", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="end", description="自分で作成した投票を終了します。")
    @app_commands.autocomplete(poll_id=poll_autocomplete)
    async def end_poll(self, interaction: discord.Interaction, poll_id: str):
        """自分で作成した投票を終了します。"""
        guild_id = interaction.guild.id
        poll_file = Path(f'data/polls/{guild_id}/{poll_id}.json')
        poll = load_data(poll_file)

        if not poll:
            await interaction.response.send_message("指定された投票が見つかりません。", ephemeral=True)
            return

        message = await interaction.channel.fetch_message(poll['message_id'])
        results = sorted(poll["answers"], key=lambda x: x[2], reverse=True)
        result_text = "\n".join([f"{emoji}\N{COMBINING ENCLOSING KEYCAP} {choice}: {votes}票" for emoji, choice, votes, _ in results])

        embed = message.embeds[0]
        embed.set_field_at(0, name="投票結果", value=result_text or "結果がありません", inline=False)
        embed.color = discord.Color.red()
        await message.edit(embed=embed, view=None)
        
        # アーカイブディレクトリに移動
        archive_path = poll_file.parent / 'archive'
        archive_path.mkdir(parents=True, exist_ok=True)
        
        if poll_file.exists():
            poll_file.rename(archive_path / f'{poll_id}.json')
        else:
            await interaction.response.send_message(f"ファイルが見つかりません: {poll_file}", ephemeral=True)

        await interaction.response.send_message(f"投票「{poll['question']}」が終了しました。", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(PollsCog(bot))