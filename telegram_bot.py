
from dotenv import load_dotenv
import os
load_dotenv()

bot = os.getenv("BOT_TOKEN")
id = os.getenv("ID_TOKEN")
PORT = 8000

import requests

TOKEN = bot
CHAT_ID = id

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Gönderme Hatası:", e)