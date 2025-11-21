import os
import logging
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

# 環境変数を読み込む
load_dotenv()

# ログ設定（ファイルのみに出力、エラーと翻訳実行時のみ）
LOG_FILE = 'bot_translation.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8')
        # コンソール出力は削除（エラーと翻訳実行時のみファイルに記録）
    ]
)
logger = logging.getLogger(__name__)

# Botの設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージ内容を読み取るために必要

# Botのインスタンスを作成
bot = commands.Bot(command_prefix='!', intents=intents)


# 各言語のUIテキスト
UI_TEXTS = {
    'ja': {
        'title': '🌐 翻訳結果',
        'translation': '翻訳（日本語）',
        'original': '原文',
        'translated_from': '翻訳元',
        'show_original': '原文を表示',
        'hide_original': '原文を非表示',
        'no_text': '翻訳するテキストがありません。',
        'bot_message': 'Bot自身のメッセージは翻訳できません。',
        'error': '翻訳中にエラーが発生しました'
    },
    'en': {
        'title': '🌐 Translation Result',
        'translation': 'Translation (English)',
        'original': 'Original',
        'translated_from': 'Translated from',
        'show_original': 'Show Original',
        'hide_original': 'Hide Original',
        'no_text': 'No text to translate.',
        'bot_message': 'Cannot translate bot messages.',
        'error': 'An error occurred during translation'
    },
    'zh-CN': {
        'title': '🌐 翻译结果',
        'translation': '翻译（中文）',
        'original': '原文',
        'translated_from': '翻译来源',
        'show_original': '显示原文',
        'hide_original': '隐藏原文',
        'no_text': '没有要翻译的文本。',
        'bot_message': '无法翻译机器人消息。',
        'error': '翻译过程中发生错误'
    }
}


class TranslationView(discord.ui.View):
    """翻訳結果の原文をトグル表示するView"""
    
    def __init__(self, original_text: str, translated_text: str, source_lang_name: str, author_name: str, target_lang_code: str, target_lang_name: str, emoji: str, color: discord.Color):
        super().__init__(timeout=None)  # タイムアウトなし
        self.original_text = original_text
        self.translated_text = translated_text
        self.source_lang_name = source_lang_name
        self.author_name = author_name
        self.target_lang_code = target_lang_code
        self.target_lang_name = target_lang_name
        self.emoji = emoji
        self.color = color
        self.show_original = False  # 最初は非表示
        self.ui_texts = UI_TEXTS.get(target_lang_code, UI_TEXTS['en'])
        
        # ボタンを動的に作成
        self.toggle_button = discord.ui.Button(
            label=self.ui_texts['show_original'],
            style=discord.ButtonStyle.secondary,
            emoji='📝'
        )
        self.toggle_button.callback = self.toggle_original_callback
        self.add_item(self.toggle_button)
    
    async def toggle_original_callback(self, interaction: discord.Interaction):
        """原文の表示/非表示を切り替える（コールバック）"""
        self.show_original = not self.show_original
        
        # Embedを再作成
        embed = discord.Embed(
            title=self.ui_texts['title'],
            color=self.color
        )
        
        # 原文の表示/非表示
        if self.show_original:
            original_display = self.original_text
            if len(original_display) > 1000:
                original_display = original_display[:1000] + '...'
            embed.add_field(
                name=f'📝 {self.ui_texts["original"]}（{self.source_lang_name}）',
                value=original_display,
                inline=False
            )
            self.toggle_button.label = self.ui_texts['hide_original']
            self.toggle_button.emoji = '🔽'
        else:
            self.toggle_button.label = self.ui_texts['show_original']
            self.toggle_button.emoji = '📝'
        
        # 翻訳結果（常に表示）
        translated_display = self.translated_text
        if len(translated_display) > 1000:
            translated_display = translated_display[:1000] + '...'
        
        embed.add_field(
            name=f'{self.emoji} {self.ui_texts["translation"]}',
            value=translated_display,
            inline=False
        )
        
        embed.set_footer(text=f'{self.ui_texts["translated_from"]}: {self.author_name}')
        
        # メッセージを更新
        await interaction.response.edit_message(embed=embed, view=self)
    


@bot.event
async def on_ready():
    """Botが起動したときに実行されるイベント"""
    print(f'{bot.user}としてログインしました！')
    print(f'Bot ID: {bot.user.id}')
    print('------')
    
    # コンテキストメニューコマンドを同期
    try:
        synced = await bot.tree.sync()
        print(f'{len(synced)}個のコマンドを同期しました')
    except Exception as e:
        print(f'コマンド同期エラー: {e}')


def detect_source_language(text: str) -> str:
    """元の言語を簡易検出（表示用）"""
    if any(ord(char) >= 0x3040 and ord(char) <= 0x309F for char in text[:50]):
        return '日本語'
    elif any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in text[:50]):
        return '韓国語'
    elif any(ord(char) >= 0x4E00 and ord(char) <= 0x9FFF for char in text[:50]):
        return '中国語'
    elif all(ord(char) < 128 for char in text[:50]):
        return '英語（推定）'
    else:
        return '自動検出'


async def translate_message(interaction: discord.Interaction, message: discord.Message, target_lang: str, target_code: str, emoji: str, color: discord.Color):
    """共通の翻訳処理"""
    ui_texts = UI_TEXTS.get(target_code, UI_TEXTS['en'])
    
    # Bot自身のメッセージは無視
    if message.author == bot.user:
        await interaction.response.send_message(
            ui_texts['bot_message'],
            ephemeral=True
        )
        return
    
    # メッセージが空の場合はエラー
    if not message.content.strip():
        await interaction.response.send_message(
            ui_texts['no_text'],
            ephemeral=True
        )
        return
    
    # 翻訳処理を開始（応答を遅延させる）
    await interaction.response.defer(ephemeral=True)
    
    try:
        # 自動検出で指定言語に翻訳
        translator_instance = GoogleTranslator(source='auto', target=target_code)
        translated_text = translator_instance.translate(message.content)
        
        # 元の言語を簡易検出（表示用）
        source_lang_name = detect_source_language(message.content)
        
        # 翻訳結果をEmbed形式で表示（ephemeral=Trueで履歴に残らない）
        embed = discord.Embed(
            title=ui_texts['title'],
            color=color
        )
        
        # 翻訳結果（長い場合は切り詰め）
        translated_display = translated_text
        if len(translated_display) > 1000:
            translated_display = translated_display[:1000] + '...'
        
        embed.add_field(
            name=f'{emoji} {ui_texts["translation"]}',
            value=translated_display,
            inline=False
        )
        
        embed.set_footer(text=f'{ui_texts["translated_from"]}: {message.author.display_name}')
        
        # View（ボタン）を作成
        view = TranslationView(
            original_text=message.content,
            translated_text=translated_text,
            source_lang_name=source_lang_name,
            author_name=message.author.display_name,
            target_lang_code=target_code,
            target_lang_name=target_lang,
            emoji=emoji,
            color=color
        )
        
        # ボタンのラベルはView作成時に既に設定されているので、ここでは何もしない
        
        # ログを記録
        user_name = interaction.user.display_name or interaction.user.name
        text_preview = message.content[:50] + ('...' if len(message.content) > 50 else '')
        logger.info(f"翻訳使用 - ユーザー: {user_name} | 翻訳先: {target_lang} ({target_code}) | テキスト: {text_preview}")
        
        # ephemeral=Trueで一時的なメッセージとして表示（履歴に残らない）
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        
    except Exception as e:
        # エラーログを記録
        user_name = interaction.user.display_name or interaction.user.name
        text_preview = message.content[:50] + ('...' if len(message.content) > 50 else '')
        logger.error(f"翻訳エラー - ユーザー: {user_name} | 翻訳先: {target_lang} ({target_code}) | テキスト: {text_preview} | エラー: {str(e)}")
        
        await interaction.followup.send(
            f'❌ {ui_texts["error"]}: {str(e)}',
            ephemeral=True
        )


@bot.tree.context_menu(name='To JP 🇯🇵')
async def translate_to_japanese(interaction: discord.Interaction, message: discord.Message):
    """メッセージを右クリックして「To JP 🇯🇵」を選択したときに実行される"""
    await translate_message(interaction, message, '日本語', 'ja', '🇯🇵', discord.Color.blue())


@bot.tree.context_menu(name='To EN 🇺🇸')
async def translate_to_english(interaction: discord.Interaction, message: discord.Message):
    """メッセージを右クリックして「To EN 🇺🇸」を選択したときに実行される"""
    await translate_message(interaction, message, '英語', 'en', '🇺🇸', discord.Color.green())


@bot.tree.context_menu(name='To CN 🇨🇳')
async def translate_to_chinese(interaction: discord.Interaction, message: discord.Message):
    """メッセージを右クリックして「To CN 🇨🇳」を選択したときに実行される"""
    await translate_message(interaction, message, '中国語・簡体字', 'zh-CN', '🇨🇳', discord.Color.red())


# Botを起動
if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("エラー: DISCORD_TOKENが設定されていません。")
        print(".envファイルにDISCORD_TOKENを設定してください。")
    else:
        bot.run(token)

