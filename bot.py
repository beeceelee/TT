import os
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Take token from Render env var
API_URL = "https://www.tikwm.com/api/"

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

# Dispatcher is required to handle updates
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)


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


# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, download_tiktok))


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok", 200


@app.route("/")
def index():
    return "🤖 Bot is running!", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
