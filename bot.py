import os
import io
import threading
import tempfile
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a TikTok link and I will download HD for you!"
    )

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    url = update.message.text.strip()

    # In groups: ignore if not TikTok link
    if chat_type in ["group", "supergroup"] and "tiktok.com" not in url:
        return

    if "tiktok.com" not in url:
        if chat_type == "private":
            await update.message.reply_text("❌ Please send a valid TikTok link.")
        return

    await update.message.reply_text("Downloading video... ⏳")

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        ydl_opts = {
            "format": "mp4/best",
            "outtmpl": tmp_path,
            "quiet": True,
            "noplaylist": True,
            "merge_output_format": "mp4",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        tmp_fixed_path = tmp_path + "_fixed.mp4"
        subprocess.run([
            "ffmpeg",
            "-i", tmp_path,
            "-c", "copy",
            "-movflags", "+faststart",
            tmp_fixed_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        with open(tmp_fixed_path, "rb") as f:
            buffer_fixed = io.BytesIO(f.read())
        buffer_fixed.seek(0)

        bot_username = context.bot.username
        caption = f"Downloaded by @{bot_username}"

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

def run_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    run_bot()
