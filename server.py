from flask import Flask, request
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
import requests

TOKEN = os.environ.get("BOT_TOKEN")  # Set this in Render dashboard (Environment Variables)
API_URL = "https://www.tikwm.com/api/"

app = Flask(__name__)

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

# Telegram bot setup
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_tiktok))

# Flask route (needed for Render to bind a port)
@app.route('/')
def home():
    return "Bot is running ✅"

# Start bot polling when Render service boots
@app.before_first_request
def run_bot():
    import threading
    threading.Thread(target=updater.start_polling).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
