@echo off
echo Starting kar.py...
start cmd /c python karaoke.py

echo Waiting 30 seconds for processing...
timeout /t 30 /nobreak >nul

echo Starting playback.py...
start cmd /c python playback.py

echo All processes started.