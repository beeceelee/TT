import os
import io
import threading
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))


# --- Minimal HTTP server for Render health check ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running!")


def run_http_server():
    server = HTTPServer(("0.0.0.0", PORT), SimpleHandler)
    server.serve_forever()


# --- Telegram handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a TikTok link and I will download the video for you!"
    )


async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "tiktok.com" not in url:
        await update.message.reply_text("Please send a valid TikTok link.")
        return

    await update.message.reply_text("Downloading video... ⏳")

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ydl_opts = {
                "format": "mp4/best",
                "quiet": False,
                "noplaylist": True,
                "outtmpl": os.path.join(tmp_dir, "%(title)s.%(ext)s"),
                "merge_output_format": "mp4",
                "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Referer": "https://www.tiktok.com/",
                },
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            # Verify file exists and is not empty
            if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                await update.message.reply_text(
                    "❌ Failed: video file is empty. It may be private, removed, or region-locked."
                )
                return

            # Send to Telegram
            with open(filename, "rb") as f:
                await update.message.reply_video(
                    video=InputFile(io.BytesIO(f.read()), filename="tiktok.mp4")
                )

    except yt_dlp.utils.DownloadError:
        await update.message.reply_text(
            "❌ Unable to download this video. It may be private, removed, or region-locked."
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to download: {e}")


# --- Run bot ---
def run_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
    app_bot.run_polling()


if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    run_bot()
