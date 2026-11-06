import os

import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
datos = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", timeout=3).json()

mensajes = [u["message"] for u in datos.get("result", []) if "message" in u]
if not mensajes:
    print("No hay mensajes. Abre tu bot en Telegram, envíale /start y vuelve a ejecutar esto.")
for m in mensajes:
    chat = m["chat"]
    print(chat.get("username") or chat.get("first_name"), "-> chat_id:", chat["id"])
