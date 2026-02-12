@echo off
REM Face Recognition Attendance System Launcher
REM This script provides an easy way to start the management center

echo ===========================================
echo  Face Recognition Attendance System
echo ===========================================
echo.

cd /d "%~dp0"

echo Starting Management Center...
echo.

python main.py

echo.
echo Management Center closed.
pause