import os
import io
import threading
import tempfile
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
@@ -42,13 +40,10 @@ async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Downloading video... ")

    try:
        # Use yt-dlp to download directly to a temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        buffer = io.BytesIO()  # in-memory buffer

        ydl_opts = {
            "format": "mp4/best",
            "outtmpl": tmp_path,
            "quiet": True,
            "noplaylist": True,
            "merge_output_format": "mp4",
@@ -59,42 +54,38 @@ async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Fix metadata (move moov atom to start)
        tmp_fixed_path = tmp_path + "_fixed.mp4"
        subprocess.run([
            "ffmpeg",
            "-i", tmp_path,
            "-c", "copy",
            "-movflags", "+faststart",
            tmp_fixed_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Read fixed file into memory
        with open(tmp_fixed_path, "rb") as f:
            buffer_fixed = io.BytesIO(f.read())
        buffer_fixed.seek(0)

        # Dynamic caption with bot username
            info = ydl.extract_info(url, download=False)
            video_url = info.get("url")
            if not video_url:
                await update.message.reply_text(
                    " Unable to find video stream. It may be private or removed."
                )
                return

            with ydl.urlopen(video_url) as resp:
                buffer.write(resp.read())

        if buffer.getbuffer().nbytes == 0:
            await update.message.reply_text(" Downloaded video is empty.")
            return

        buffer.seek(0)

        # Dynamically fetch bot username
        bot_username = context.bot.username
        caption = f"Downloaded by @{bot_username}"

        await update.message.reply_video(
            video=InputFile(buffer_fixed, filename="tiktok.mp4"),
            video=InputFile(buffer, filename="tiktok.mp4"),
            caption=caption
        )

        # Cleanup
        os.remove(tmp_path)
        os.remove(tmp_fixed_path)

    except yt_dlp.utils.DownloadError:
        await update.message.reply_text(
            " Unable to download this video. It may be private, removed, or region-locked."
        )
    except Exception as e:
        await update.message.reply_text(f" Failed to process video: {e}")
        await update.message.reply_text(f"Failed to download: {e}")


# Run bot
