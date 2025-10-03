#!/usr/bin/env bash
apt-get update
apt-get install -y ffmpeg
pip install --upgrade pip
pip install -r requirements.txt
pip install https://github.com/yt-dlp/yt-dlp/releases/download/2025.09.26/yt_dlp.tar.gz
