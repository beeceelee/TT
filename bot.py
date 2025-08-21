from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests, os

BOT_TOKEN = os.getenv("BOT_TOKEN")  # read from Render Environment Variable
API_URL = "https://www.tikwm.com/api/"

def start(update, context):
    update.message.reply_text("👋 Send me a TikTok link and I’ll download it (no watermark)!")

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

def setup_dispatcher(dp):
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_tiktok))
    return dp
