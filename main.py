import discord
import re
import requests
import pandas as pd
from dotenv import load_dotenv
import os

# .env ファイルを読み込む
load_dotenv()

# 環境変数から Webhook URL と Bot Token を取得
webhook_url = os.getenv("WEBHOOK_URL")
discord_token = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# CSVファイルからプロジェクトキーを読み込む関数
def load_project_keys(csv_file):
    df = pd.read_csv(csv_file)
    return df["project_name"].tolist()


project_keys = load_project_keys("project_keys.csv") 


@client.event
async def on_ready():
    print(f"logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return  

    if "linkgenerator" in message.content:
        return

    # $stopコマンドでボットを強制ログアウト
    if message.content == "$stop":
        await message.channel.send("Bot is logging out...")
        await client.close()
        return

    new_content = message.content  # new_contentを初期化（これを修正する）
    sender = message.author.display_name  # メッセージ送信者のサーバー表示名を取得
    avatar_url = message.author.avatar.url if message.author.avatar else None

    # 各プロジェクトキーを検知してリンクを生成
    for project_key in project_keys:
        pattern = re.compile(rf"({project_key}-\d+)\s+(.+?)(?=\s|$)") # 課題キー+件名のフォーマット
        new_content = pattern.sub(
            lambda m: f"[{m.group(0)}](https://saino-inc.backlog.com/view/{m.group(1)})",
            new_content,
        )

    # リンクが見つかった場合、新しいメッセージを送信して元のメッセージを削除
    if new_content != message.content:
        reply_content = f"{new_content}\nedited by linkgenerator as **{sender}**"
        data = {
            "username": sender,  # Webhookを使用して送信するときのユーザー名
            "content": reply_content,  # 送信する内容
            "avatar_url": avatar_url,
        }
        response = requests.post(webhook_url, json=data)
        if response.status_code != 204:
            print(
                f"Error sending message through webhook: {response.status_code}, {response.text}"
            )

        # 元のメッセージを削除
        await message.delete()


client.run(discord_token)
