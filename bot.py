import os
import io
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import tempfile
import subprocess
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

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a TikTok link and I will download HD for you!"
    )

# Rewritten download_tiktok function (from previous message)
async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "tiktok.com" not in url:
        await update.message.reply_text("Please send a valid TikTok link.")
        return

    loading_msg = await update.message.reply_text("Downloading video... ⏳")

    tmp_path = None
    tmp_fixed_path = None

    try:
        # Step 1: download video via yt-dlp to temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        ydl_opts = {
            "format": "mp4/best",
            "outtmpl": tmp_path,
            "merge_output_format": "mp4",
            "quiet": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if os.path.getsize(tmp_path) == 0:
            await update.message.reply_text("❌ Downloaded video is empty.")
            return

        # Step 2: fix duration metadata with ffmpeg
        tmp_fixed_path = tmp_path + "_fixed.mp4"
        subprocess.run([
            "ffmpeg",
            "-i", tmp_path,
            "-c", "copy",
            "-movflags", "+faststart",
            tmp_fixed_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Step 3: read file into memory
        with open(tmp_fixed_path, "rb") as f:
            buffer = io.BytesIO(f.read())
        buffer.seek(0)

        caption = "Downloaded by @Save4TiktokVideos_bot"
        await update.message.reply_video(
            video=InputFile(buffer, filename="tiktok.mp4"),
            caption=caption
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Failed to download: {e}")

    finally:
        # Clean up temp files
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if tmp_fixed_path and os.path.exists(tmp_fixed_path):
            os.remove(tmp_fixed_path)

    await loading_msg.edit_text("✅ Download complete!")

# Run bot
def run_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
    app_bot.run_polling()

if __name__ == "__main__":
    # Start health check HTTP server for Render
    threading.Thread(target=run_http_server, daemon=True).start()
    run_bot()
