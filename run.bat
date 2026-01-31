@echo off
echo Starting Lingo-Live...
echo.
echo NOTE: This app needs to run with the same or higher privileges
echo to capture global hotkeys from other applications.
echo.
cd /d "%~dp0"
python main.py
pause
