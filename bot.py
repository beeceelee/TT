async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "tiktok.com" not in url:
        await update.message.reply_text("Please send a valid TikTok link.")
        return

    await update.message.reply_text("Downloading video... ⏳")

    try:
        import tempfile, os, yt_dlp

        # Temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name

        ydl_opts = {
            "format": "mp4",
            "quiet": True,
            "noplaylist": True,
            "outtmpl": tmp_path,   # real file, not "-"
            "merge_output_format": "mp4"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([url])

        # Check file size
        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            await update.message.reply_text("❌ Failed: video file is empty.")
            return

        # Send video
        with open(tmp_path, "rb") as f:
            await update.message.reply_video(video=InputFile(f, filename="tiktok.mp4"))

        # Clean up
        os.remove(tmp_path)

    except Exception as e:
        await update.message.reply_text(f"Failed to download: {e}")
