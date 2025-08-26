#!/usr/bin/env bash
apt-get update
apt-get install -y ffmpeg
pip install -U yt-dlp
pip install -r requirements.txt
