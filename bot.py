import os
import io
import tempfile
import subprocess
from flask import Flask, request
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import yt_dlp

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)


# Start command
def start(update, context):
    update.message.reply_text("👋 Send me a TikTok link and I’ll download it (no watermark).")


# TikTok downloader
def download_tiktok(update, context):
    chat_type = update.message.chat.type
    url = update.message.text.strip()

    # Group check: ignore if not TikTok link
    if chat_type in ["group", "supergroup"] and "tiktok.com" not in url:
        return

    # URL validation
    if "tiktok.com" not in url or "/video/" not in url:
        if chat_type == "private":
            update.message.reply_text("❌ Please send a valid TikTok video link.")
        return

    update.message.reply_text("⏳ Downloading video...")

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        ydl_opts = {
            "format": "mp4[bv*+ba]/mp4",
            "quiet": False,  # debug logs
            "noplaylist": True,
            "merge_output_format": "mp4",
            "outtmpl": tmp_path,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/117.0.0.0 Safari/537.36",
                "Referer": "https://www.tiktok.com/",
            },
            # "cookiesfrombrowser": ("chrome",),  # optional for private videos
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
            except Exception as e:
                update.message.reply_text(f"❌ yt-dlp error: {str(e)}")
                return

        if not os.path.exists(tmp_path):
            update.message.reply_text(f"❌ Download failed: {tmp_path} not found.")
            return

        tmp_fixed_path = tmp_path + "_fixed.mp4"

        result = subprocess.run([
            "ffmpeg",
            "-i", tmp_path,
            "-c", "copy",
            "-movflags", "+faststart",
            tmp_fixed_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            update.message.reply_text(f"❌ FFmpeg failed:\n{result.stderr.decode()}")
            return

        if not os.path.exists(tmp_fixed_path):
            update.message.reply_text(f"❌ Fixed video not created: {tmp_fixed_path}")
            return

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

        update.message.reply_video(
            video=InputFile(buffer_fixed, filename="tiktok.mp4"),
            caption=caption,
            reply_markup=reply_markup
        )

        os.remove(tmp_path)
        os.remove(tmp_fixed_path)

    except Exception as e:
        update.message.reply_text(f"❌ Failed to process video: {e}")


# Inline button handler
def button_handler(update, context):
    query = update.callback_query
    query.answer()

    if query.data == "again":
        query.edit_message_caption(
            caption="🔁 Please send another TikTok link to download.",
            reply_markup=None,
        )
    elif query.data == "about":
        query.edit_message_caption(
            caption="ℹ️ This bot downloads TikTok videos without watermark.\nMade with ❤️",
            reply_markup=None,
        )


dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
dispatcher.add_handler(CallbackQueryHandler(button_handler))


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok", 200


@app.route("/")
def index():
    return "🤖 Bot is running!", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
