import tempfile
import subprocess
import io
import os
from telegram import InputFile, Update
from telegram.ext import ContextTypes

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

        import yt_dlp
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

        caption = "Downloaded by:@Save4TiktokVideos_bot"
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
