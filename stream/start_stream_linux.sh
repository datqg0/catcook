#!/usr/bin/env bash
# ==============================================================================
# 24/7 YouTube Live Streaming Script for Oracle Cloud (OCI ARM Ubuntu/Oracle Linux)
# Starts virtual framebuffer Xvfb :99, launches Pygame at 720x1280,
# and encodes stream via FFmpeg directly to YouTube RTMPS.
# ==============================================================================

set -euo pipefail

# 1. Read Stream Key from config or environment
CONFIG_FILE="$(dirname "$0")/../config/config.json"
STREAM_KEY="${STREAM_KEY:-}"

if [ -z "$STREAM_KEY" ] && [ -f "$CONFIG_FILE" ]; then
    STREAM_KEY=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['stream'].get('stream_key', ''))")
fi

if [ -z "$STREAM_KEY" ] || [ "$STREAM_KEY" = "YOUR_YOUTUBE_STREAM_KEY_HERE" ]; then
    echo "ERROR: Please set your YouTube stream key in config/config.json or STREAM_KEY env variable!"
    exit 1
fi

echo "[Stream] Starting Xvfb virtual display on :99 (720x1280x24)..."
Xvfb :99 -screen 0 720x1280x24 -ac &
XVFB_PID=$!
export DISPLAY=:99

cleanup() {
    echo "[Stream] Stopping services..."
    kill $XVFB_PID || true
}
trap cleanup EXIT

sleep 2

echo "[Stream] Launching Cozy Midnight Diner on virtual display..."
python3 "$(dirname "$0")/../main.py" &
GAME_PID=$!

sleep 3

echo "[Stream] Starting FFmpeg encoding and pushing RTMP to YouTube..."
# High-efficiency vertical stream preset tailored for 2 OCPU ARM:
ffmpeg -hide_banner -loglevel warning \
    -f x11grab -s 720x1280 -framerate 30 -draw_mouse 0 -i :99.0 \
    -stream_loop -1 -i "$(dirname "$0")/../assets/sounds/lofi_chill.mp3" \
    -c:v libx264 -preset veryfast -b:v 3500k -maxrate 4000k -bufsize 6000k \
    -pix_fmt yuv420p -r 30 -g 60 -tune zerolatency \
    -c:a aac -b:a 128k -ar 44100 -shortest \
    -f flv "rtmp://a.rtmp.youtube.com/live2/$STREAM_KEY"

echo "[Stream] FFmpeg stream terminated."
