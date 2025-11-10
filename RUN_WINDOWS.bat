@echo off
REM NeuroFlow Windows Quick Launcher
REM For development and testing

echo ========================================
echo NeuroFlow Windows Launcher
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python or run the built executable
    pause
    exit /b 1
)

echo Starting NeuroFlow...
echo.

REM Run the Windows version
python ct_perfusion_viewer_windows.py

pause
