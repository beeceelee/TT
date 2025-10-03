import os
import io
import threading
import tempfile
import subprocess
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

bot = Bot(token=BOT_TOKEN)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me a TikTok video link and I’ll download it (no watermark).")

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    url = update.message.text.strip()

    # Resolve short TikTok URLs
    try:
        resp = requests.head(url, allow_redirects=True, timeout=10)
        url = resp.url
    except Exception:
        pass

    # Ignore non-TikTok messages in groups
    if chat_type in ["group", "supergroup"] and "tiktok.com" not in url:
        return

    if "tiktok.com" not in url or "/video/" not in url:
        if chat_type == "private":
            await update.message.reply_text("❌ Please send a valid TikTok video link.")
        return

    await update.message.reply_text("⏳ Downloading video...")

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": tmp_path,
            "quiet": False,
            "noplaylist": True,
            "merge_output_format": "mp4",
            "no_check_certificate": True,
            "geo_bypass": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/117.0.0.0 Safari/537.36",
                "Referer": "https://www.tiktok.com/",
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([url])
            except Exception as e:
                await update.message.reply_text(f"❌ yt-dlp error: {str(e)}")
                return

        tmp_fixed_path = tmp_path + "_fixed.mp4"
        result = subprocess.run([
            "ffmpeg", "-i", tmp_path, "-c", "copy", "-movflags", "+faststart", tmp_fixed_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0 or not os.path.exists(tmp_fixed_path):
            await update.message.reply_text(f"❌ FFmpeg error:\n{result.stderr.decode()}")
            return

        with open(tmp_fixed_path, "rb") as f:
            buffer_fixed = io.BytesIO(f.read())

        buffer_fixed.seek(0)
        caption = f"Downloaded by @{context.bot.username}"

        buttons = [
            [InlineKeyboardButton("🔁 Download Again", callback_data="again")],
            [InlineKeyboardButton("ℹ️ About", callback_data="about")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        await update.message.reply_video(
            video=InputFile(buffer_fixed, filename="tiktok.mp4"),
            caption=caption,
            reply_markup=reply_markup
        )

        os.remove(tmp_path)
        os.remove(tmp_fixed_path)

    except yt_dlp.utils.DownloadError:
        await update.message.reply_text(
            "❌ Unable to download this video. It may be private, removed, or region-locked."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to process video: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "again":
        await query.edit_message_caption(
            caption="🔁 Please send another TikTok link to download.",
            reply_markup=None,
        )
    elif query.data == "about":
        await query.edit_message_caption(
            caption="ℹ️ This bot downloads TikTok videos without watermark.\nMade with ❤️",
            reply_markup=None,
        )

def main():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
    app_bot.add_handler(CallbackQueryHandler(button_handler))

    threading.Thread(target=run_http_server, daemon=True).start()
    app_bot.run_polling()

if __name__ == "__main__":
    main()
