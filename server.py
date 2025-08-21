from flask import Flask, request
from telegram import Update
from telegram.ext import Updater, Dispatcher
import os

from bot import setup_dispatcher

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 5000))

# Create updater and dispatcher
updater = Updater(BOT_TOKEN, use_context=True)
dp = setup_dispatcher(updater.dispatcher)

@app.route("/")
def home():
    return "✅ Telegram bot is running with webhook!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), updater.bot)
    dp.process_update(update)
    return "ok"

if __name__ == "__main__":
    # Set webhook to Render URL
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")  # Render provides this automatically
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{BOT_TOKEN}"
        updater.bot.set_webhook(webhook_url)
        print(f"🌐 Webhook set to {webhook_url}")
    app.run(host="0.0.0.0", port=PORT)
