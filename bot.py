from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests, os
import sys
from PIL import Image
from io import BytesIO

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Render will set this

API_URL = "https://www.tikwm.com/api/"

def get_image_type(file_content):
    try:
        image = Image.open(BytesIO(file_content))
        return image.format  # Returns the image format (JPEG, PNG, etc.)
    except IOError:
        return None

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

            # Send video with caption
            update.message.reply_video(
                video_url,
                caption="✅ TikTok Video (no watermark)\n\nDownloaded via @Save4TiktokVideos_bot"
            )

            # Optionally: Check image type with the new Pillow function
            # Example: assuming file_content is available (e.g., video file)
            image_type = get_image_type(file_content)
            if image_type:
                print(f"File type detected: {image_type}")
            else:
                print("Invalid file or unsupported format.")

        else:
            update.message.reply_text("⚠️ Couldn’t download video. Try another link.")

    except Exception as e:
        update.message.reply_text(f"⚠️ Error: {e}")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_tiktok))

    print("🤖 Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
