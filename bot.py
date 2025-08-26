import io
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

# Minimal HTTP server for Render
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

        ydl_opts = {
            "format": "mp4",
            "quiet": True,
            "noplaylist": True,
            "outtmpl": "-",  # stdout
            "merge_output_format": "mp4",  # ensure proper mp4
            "postprocessors": [{
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4"
            }],
        }

        # Custom sink to write into BytesIO instead of a file
        class MyLogger:
            def debug(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): print(msg)

        def my_hook(d):
            if d["status"] == "finished":
                print("Download complete.")

        ydl_opts["logger"] = MyLogger()
        ydl_opts["progress_hooks"] = [my_hook]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # After download, yt-dlp will create a proper mp4 file on disk
            filename = ydl.prepare_filename(info)
            with open(filename, "rb") as f:
                buffer.write(f.read())

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
