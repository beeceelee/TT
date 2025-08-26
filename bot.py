import os
import io
import re
import threading
import asyncio
import requests
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


# Expand vt.tiktok.com short URLs
def expand_tiktok_url(url: str) -> str:
    try:
        resp = requests.head(url, allow_redirects=True)
        return resp.url
    except Exception:
        return url


# Animated loading
async def animate_loading(message, text="Downloading video"):
    spinner = ["⏳", "⌛", "🔄", "🌀"]
    i = 0
    while True:
        try:
            await message.edit_text(f"{text} {spinner[i % len(spinner)]}")
            i += 1
            await asyncio.sleep(0.5)
        except:
            break


# Download and process TikTok video fully in-memory
def download_and_fix_video(full_url: str) -> io.BytesIO:
    # Extract direct video URL with yt-dlp
    ydl_opts = {"quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(full_url, download=False)
        video_url = info.get("url")
        if not video_url:
            return None

    # Download via ffmpeg and fix duration metadata
    process = subprocess.run(
        [
            "ffmpeg",
            "-i", video_url,
            "-c", "copy",
            "-movflags", "+faststart",
            "-f", "mp4",
            "pipe:1"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )

    if not process.stdout or len(process.stdout) == 0:
        return None

    buffer = io.BytesIO(process.stdout)
    buffer.seek(0)
    return buffer


# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me one or more TikTok links and I will download them!"
    )


async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    urls = re.findall(r'https?://[^\s]*tiktok\.com/[^\s]+', text)
    if not urls:
        await update.message.reply_text("Please send at least one valid TikTok link.")
        return

    caption = "Downloaded by @Save4TiktokVideos_bot"
    loading_msg = await update.message.reply_text("Downloading video... ⏳")
    spinner_task = asyncio.create_task(animate_loading(loading_msg))

    for url in urls:
        full_url = expand_tiktok_url(url)
        try:
            buffer = download_and_fix_video(full_url)
            if not buffer:
                await update.message.reply_text(
                    f"❌ Failed to download or process video: {full_url}"
                )
                continue

            await update.message.reply_video(
                video=InputFile(buffer, filename="tiktok.mp4"),
                caption=caption
            )

        except Exception as e:
            await update.message.reply_text(f"Failed to download a video: {e}")

    spinner_task.cancel()
    await loading_msg.edit_text("✅ Download complete!")


def run_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
    app_bot.run_polling()


if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    run_bot()
