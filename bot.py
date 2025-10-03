import os
import io
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))


# Minimal HTTP server for Render health check
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running!")


def run_http_server():
    server = HTTPServer(("0.0.0.0", PORT), SimpleHandler)
    server.serve_forever()


# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me a TikTok link and I will download HD for you!"
    )


async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Skip replying in groups
    if update.message.chat.type in ["group", "supergroup"]:
        return

    url = update.message.text.strip()
    if "tiktok.com" not in url:
        await update.message.reply_text("❌ Please send a valid TikTok link.")
        return

    await update.message.reply_text("⏳ Downloading video...")

    try:
        buffer = io.BytesIO()

        ydl_opts = {
            "format": "mp4/best",
            "quiet": True,
            "noplaylist": True,
            "merge_output_format": "mp4",
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://www.tiktok.com/",
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get("url")
            if not video_url:
                await update.message.reply_text(
                    "❌ Unable to find video stream. It may be private or removed."
                )
                return

            with ydl.urlopen(video_url) as resp:
                buffer.write(resp.read())

        if buffer.getbuffer().nbytes == 0:
            await update.message.reply_text("❌ Downloaded video is empty.")
            return

        buffer.seek(0)

        bot_username = context.bot.username
        caption = f"Downloaded by @{bot_username}"

        # Inline button example
        keyboard = [
            [InlineKeyboardButton("📥 Download Again", callback_data="download_again")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_video(
            video=InputFile(buffer, filename="tiktok.mp4"),
            caption=caption,
            reply_markup=reply_markup
        )

    except yt_dlp.utils.DownloadError:
        await update.message.reply_text(
            "❌ Unable to download this video. It may be private, removed, or region-locked."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to download: {e}")


# Run bot
def run_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
    app_bot.run_polling()


if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    run_bot()
