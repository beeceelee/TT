import io
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))  # Render sets this automatically

# Minimal HTTP server (satisfies Render free Web Service port binding)
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_http_server():
    server = HTTPServer(("0.0.0.0", PORT), SimpleHandler)
    server.serve_forever()

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

        # yt-dlp options: write video directly to BytesIO
        ydl_opts = {
            "format": "mp4",
            "quiet": True,
            "noplaylist": True,
            "outtmpl": "-",  # output to stdout
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=True)
            # yt-dlp by default writes to a file, so instead we grab best URL
            video_url = result["url"]

            import urllib.request
            with urllib.request.urlopen(video_url) as response:
                buffer.write(response.read())

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

if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    run_bot()
