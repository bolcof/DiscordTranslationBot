# Discord Bot - 右クリック翻訳機能

Discordのメッセージを右クリックして「和訳」を選択すると、翻訳結果が一時的なメッセージ（履歴に残らない）として表示されるBotです。

## 機能

- **右クリックメニューから翻訳**: メッセージを右クリックして「和訳」を選択するだけで翻訳
- **一時的な表示**: 翻訳結果は`ephemeral`メッセージとして表示され、チャンネルの履歴に残りません
- **自動言語検出**: 元の言語を自動検出して日本語に翻訳
- **見やすい表示**: Embed形式で原文と翻訳結果を分かりやすく表示

## セットアップ手順

### 1. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. Discord Bot Tokenの取得

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」をクリックして新しいアプリケーションを作成
3. 左側のメニューから「Bot」を選択
4. 「Add Bot」をクリック
5. 「Reset Token」をクリックしてトークンを取得（このトークンは一度しか表示されないので、必ず保存してください）
6. 「Privileged Gateway Intents」セクションで以下を有効化：
   - **MESSAGE CONTENT INTENT**（メッセージ内容を読み取るために必須）

### 3. Botをサーバーに招待

1. 左側のメニューから「OAuth2」→「URL Generator」を選択
2. 「Scopes」で以下を選択：
   - `bot`
   - `applications.commands`（コンテキストメニューコマンドに必要）
3. 「Bot Permissions」で必要な権限を選択：
   - Send Messages
   - Read Message History
   - Use External Emojis（オプション）
4. 生成されたURLをコピーしてブラウザで開き、Botをサーバーに招待

### 4. 環境変数の設定

`.env`ファイルを作成して、取得したトークンを設定してください：

```
DISCORD_TOKEN=your_bot_token_here
```

### 5. Botの起動

```bash
python bot.py
```

Botが起動すると、コンテキストメニューコマンドが自動的に同期されます。

## 使い方

1. Discordでメッセージを**右クリック**します
2. メニューから**「和訳」**を選択します
3. 翻訳結果が一時的なメッセージとして表示されます（あなただけに見えます）
4. チャンネルの履歴には残りません

## 注意事項

- `.env`ファイルには機密情報が含まれるため、Gitにコミットしないでください
- Bot Tokenは絶対に他人に共有しないでください
- 翻訳機能はGoogle Translate API（googletrans）を使用しています
- コンテキストメニューコマンドは、Botを起動してから最大1時間かかる場合があります（通常は数秒〜数分）

## トラブルシューティング

### 右クリックメニューに「和訳」が表示されない

- Botを起動してから数分待ってみてください（コマンドの同期に時間がかかることがあります）
- Botがサーバーに正しく招待されているか確認してください
- Botに`applications.commands`スコープが付与されているか確認してください
- Botを再起動してみてください

### 翻訳が動作しない

- `.env`ファイルに`DISCORD_TOKEN`が正しく設定されているか確認してください
- Botに「MESSAGE CONTENT INTENT」が有効になっているか確認してください

