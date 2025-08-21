import os
from flask import Flask
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests

# Load bot token from environment (set in Render dashboard)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_URL = "https://www.tikwm.com/api/"

# --- Telegram Bot Handlers ---
def start(update, context):
    update.message.reply_text("👋 Send me a TikTok link and I’ll download it (no watermark).")

def download_tiktok(update, context):
    url = update.message.text.strip()

    if "tiktok.com" not in url:
        update.message.reply_text("❌ Please send a valid TikTok link.")
        return

    try:
        r = requests.post(API_URL, data={"url": url})
        data = r.json()

        if data.get("data"):
            video_url = data["data"]["play"]
            caption = "✅ TikTok Video (no watermark)\n\nDownloaded via: @Save4TiktokVideoBot"
            update.message.reply_video(video=video_url, caption=caption)
        else:
            update.message.reply_text("⚠️ Couldn’t download video. Try another link.")
    except Exception as e:
        update.message.reply_text(f"⚠️ Error: {e}")

# --- Flask Web App (to keep Render happy) ---
app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Telegram TikTok Bot is running!"

def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_tiktok))

    print("🤖 Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    # Start Telegram bot in background
    import threading
    threading.Thread(target=run_bot).start()

    # Start Flask web server (Render requires this)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
