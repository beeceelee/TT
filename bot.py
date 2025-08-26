import io
import os
import threading
from flask import Flask
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

# Flask app to satisfy Render
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running!"

# Telegram bot functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a TikTok link and I will download the video for you!")

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if "tiktok.com" not in url:
        await update.message.reply_text("Please send a valid TikTok link.")
        return

    await update.message.reply_text("Downloading video... ⏳")
    
    try:
        buffer = io.BytesIO()
        
        ydl_opts = {
            'format': 'mp4',
            'quiet': True,
            'noplaylist': True,
            'outtmpl': '-',        # '-' means stdout
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'postprocessors': [],
        }

        # Capture video bytes
        def download_hook(d):
            if d['status'] == 'finished':
                print("Download finished.")

        ydl_opts['progress_hooks'] = [download_hook]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info to get URL
            info = ydl.extract_info(url, download=False)
            video_url = info['url']
            # Download video content
            import requests
            video_bytes = requests.get(video_url).content
            buffer.write(video_bytes)

        buffer.seek(0)
        await update.message.reply_video(video=InputFile(buffer, filename="tiktok.mp4"))

    except Exception as e:
        await update.message.reply_text(f"Failed to download: {e}")

# Run Telegram bot in a separate thread
def run_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
    app_bot.run_polling()

threading.Thread(target=run_bot).start()

# Run Flask app to satisfy Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
