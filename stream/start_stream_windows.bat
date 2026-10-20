@echo off
REM ==============================================================================
REM Cozy Midnight Diner - Windows FFmpeg Livestream Script
REM Captures game window + desktop audio and pushes to YouTube RTMP
REM ==============================================================================

echo ============================================================
echo   COZY MIDNIGHT DINER - YouTube 24/7 Stream Launcher
echo ============================================================
echo.

REM 1. Read stream key from config.json
for /f "usebackq tokens=*" %%A in (`python -c "import json; print(json.load(open('config/config.json'))['stream'].get('stream_key',''))"`) do set STREAM_KEY=%%A

if "%STREAM_KEY%"=="" (
    echo [ERROR] Stream key not found in config/config.json!
    echo Please edit config/config.json and set your YouTube stream_key.
    pause
    exit /b 1
)

if "%STREAM_KEY%"=="YOUR_YOUTUBE_STREAM_KEY_HERE" (
    echo [ERROR] Stream key is still the placeholder!
    echo Please edit config/config.json and set your real YouTube stream_key.
    pause
    exit /b 1
)

echo [Stream] Stream Key loaded from config.json
echo.

REM 2. Launch the game in background
echo [Stream] Starting Cozy Midnight Diner game...
start /B python main.py

echo [Stream] Waiting 5 seconds for game window to initialize...
timeout /t 5 /nobreak >nul

REM 3. Start FFmpeg capture and stream
echo [Stream] Starting FFmpeg capture to YouTube RTMPS...
echo [Stream] Press Ctrl+C to stop streaming.
echo.

ffmpeg -hide_banner -loglevel warning ^
  -f gdigrab -framerate 30 -video_size 720x1280 ^
  -i title="Cozy Midnight Diner - 24/7 Interactive Stream" ^
  -c:v libx264 -preset veryfast -b:v 3500k -maxrate 4000k -bufsize 6000k ^
  -pix_fmt yuv420p -r 30 -g 60 -tune zerolatency ^
  -c:a aac -b:a 128k -ar 44100 ^
  -f flv "rtmp://a.rtmp.youtube.com/live2/%STREAM_KEY%"

echo.
echo [Stream] FFmpeg stream terminated.
pause
