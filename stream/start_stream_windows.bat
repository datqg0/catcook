@echo off
REM ==============================================================================
REM Local Windows FFmpeg Test Stream Script
REM Captures game window or screen and pushes to YouTube RTMP
REM ==============================================================================

echo [Stream] Launching Cozy Midnight Diner locally...
start python main.py

echo.
echo To stream to YouTube from Windows, install FFmpeg and run:
echo ffmpeg -f gdigrab -framerate 30 -video_size 720x1280 -i title="Cozy Midnight Diner - 24/7 Interactive Stream" -c:v libx264 -preset veryfast -b:v 3500k -c:a aac -b:a 128k -f flv rtmp://a.rtmp.youtube.com/live2/YOUR_STREAM_KEY
echo.
pause
