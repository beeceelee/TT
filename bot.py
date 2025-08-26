import os
import io
import threading
import tempfile
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InputFile
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
        "Send me a TikTok link and I will download HD for you!"
    )


async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "tiktok.com" not in url:
        await update.message.reply_text("Please send a valid TikTok link.")
        return

    await update.message.reply_text("Downloading video... ⏳")

    try:
        # Use yt-dlp to download directly to a temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        ydl_opts = {
            "format": "mp4/best",
            "outtmpl": tmp_path,
            "quiet": True,
            "noplaylist": True,
            "merge_output_format": "mp4",
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://www.tiktok.com/",
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Fix metadata (move moov atom to start)
        tmp_fixed_path = tmp_path + "_fixed.mp4"
        subprocess.run([
            "ffmpeg",
            "-i", tmp_path,
            "-c", "copy",
            "-movflags", "+faststart",
            tmp_fixed_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Read fixed file into memory
        with open(tmp_fixed_path, "rb") as f:
            buffer_fixed = io.BytesIO(f.read())
        buffer_fixed.seek(0)

        # Dynamic caption with bot username
        bot_username = context.bot.username
        caption = f"Downloaded by @{bot_username}"

        await update.message.reply_video(
            video=InputFile(buffer_fixed, filename="tiktok.mp4"),
            caption=caption
        )

        # Cleanup
        os.remove(tmp_path)
        os.remove(tmp_fixed_path)

    except yt_dlp.utils.DownloadError:
        await update.message.reply_text(
            "❌ Unable to download this video. It may be private, removed, or region-locked."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to process video: {e}")


# Run bot
def run_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
    app_bot.run_polling()


if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    run_bot()
