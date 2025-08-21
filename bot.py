from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
import os

# Get BOT_TOKEN from environment variable on Render
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Set this in Render Dashboard as environment variable
API_URL = "https://www.tikwm.com/api/"

# Command handler to start the bot
async def start(update: Update, context):
    await update.message.reply_text("👋 Send me a TikTok link and I’ll download it (no watermark)!")

# Function to handle TikTok link downloads
async def download_tiktok(update: Update, context):
    url = update.message.text.strip()

    if "tiktok.com" not in url:
        await update.message.reply_text("❌ Please send a valid TikTok link.")
        return

    try:
        r = requests.post(API_URL, data={"url": url})
        data = r.json()

        if data.get("data"):
            video_url = data["data"]["play"]

            # Add signature in caption
            caption = "✅ TikTok Video (no watermark)\n\nDownloaded via: @Save4TiktokVideos_bot"

            await update.message.reply_video(video_url, caption=caption)
        else:
            await update.message.reply_text("⚠️ Couldn’t download video. Try another link.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# Main function to start the bot
def main():
    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers for the start command and the text messages
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))

    # Start polling the bot
    application.run_polling()

if __name__ == "__main__":
    main()
