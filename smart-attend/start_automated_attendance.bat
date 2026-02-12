@echo off
REM Automated Attendance System Startup Script
REM This script starts the automated attendance scheduler

echo ========================================
echo 🎓 Automated Attendance System
echo ========================================
echo Starting automated attendance scheduler...
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python and add it to your PATH
    pause
    exit /b 1
)

REM Start the automated attendance scheduler
echo 🚀 Starting scheduler...
python automated_attendance_scheduler.py

echo.
echo Scheduler stopped.
pause