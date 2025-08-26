import os
import io
import re
import threading
import requests
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
        return url  # fallback

# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me one or more TikTok links (www.tiktok.com or vt.tiktok.com) and I will download them!"
    )

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    urls = re.findall(r'https?://(?:www|vt)\.tiktok\.com/[^\s]+', text)
    if not urls:
        await update.message.reply_text("Please send at least one valid TikTok link.")
        return

    caption = "Downloaded by @Save4TiktokVideos_bot"

    for url in urls:
        full_url = expand_tiktok_url(url)  # follow redirects for vt.tiktok.com
        await update.message.reply_text(f"Downloading video: {full_url} ⏳")

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
                info = ydl.extract_info(full_url, download=False)
                video_url = info.get("url")
                if not video_url:
                    await update.message.reply_text(
                        f"❌ Unable to find video stream for {full_url}."
                    )
                    continue

                # Download video into memory
                with ydl.urlopen(video_url) as resp:
                    buffer.write(resp.read())

            if buffer.getbuffer().nbytes == 0:
                await update.message.reply_text(f"❌ Downloaded video is empty: {full_url}")
                continue

            buffer.seek(0)
            await update.message.reply_video(
                video=InputFile(buffer, filename="tiktok.mp4"),
                caption=caption
            )

        except yt_dlp.utils.DownloadError:
            await update.message.reply_text(
                f"❌ Unable to download video: {full_url} (private, removed, or region-locked)"
            )
        except Exception as e:
            await update.message.reply_text(f"Failed to download {full_url}: {e}")


# Run bot
def run_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
    app_bot.run_polling()


if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    run_bot()
