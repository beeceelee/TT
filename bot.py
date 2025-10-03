import os
import requests
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = "https://www.tikwm.com/api/"

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

dispatcher = Dispatcher(bot, None, workers=0, use_context=True)


# --- Handlers ---
def start(update, context):
    update.message.reply_text(
        "👋 Send me a TikTok link and I’ll download it (no watermark)."
    )


def download_tiktok(update, context):
    chat_type = update.message.chat.type
    text = update.message.text.strip()

    # If group, only process TikTok links
    if chat_type in ["group", "supergroup"] and "tiktok.com" not in text:
        return

    if "tiktok.com" not in text:
        if chat_type == "private":
            update.message.reply_text("❌ Please send a valid TikTok link.")
        return

    try:
        update.message.reply_text("⏳ Downloading TikTok video...")

        r = requests.post(API_URL, data={"url": text})
        data = r.json()

        if data.get("data"):
            video_url = data["data"]["play"]

            caption = "✅ TikTok Video (no watermark)\n\nDownloaded via: @YourBotUsername"

            buttons = [
                [InlineKeyboardButton("🔁 Download Again", callback_data="again")],
                [InlineKeyboardButton("ℹ️ About", callback_data="about")]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)

            update.message.reply_video(video=video_url, caption=caption, reply_markup=reply_markup)

        else:
            update.message.reply_text("⚠️ Couldn’t download video. Try another link.")
    except Exception as e:
        update.message.reply_text(f"⚠️ Error: {e}")


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


# --- Register handlers ---
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, download_tiktok))
dispatcher.add_handler(CallbackQueryHandler(button_handler))


# --- Flask routes ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok", 200


@app.route("/")
def index():
    return "🤖 Bot is running!", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
