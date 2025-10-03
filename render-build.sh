#!/usr/bin/env bash

# Update packages
apt-get update

# Install ffmpeg
apt-get install -y ffmpeg

# Upgrade pip
pip install --upgrade pip

# Install yt-dlp globally
pip install -U yt-dlp

# Install Python requirements
pip install -r requirements.txt
