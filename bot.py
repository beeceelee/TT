import io
import os
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Set this in Render environment

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
            'outtmpl': '-',
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Read downloaded video from buffer
        buffer.seek(0)
        await update.message.reply_video(
            video=InputFile(buffer, filename="tiktok.mp4")
        )

    except Exception as e:
        await update.message.reply_text(f"Failed to download: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
    print("Bot started...")
    app.run_polling()
