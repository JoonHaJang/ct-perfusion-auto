@echo off
REM NeuroFlow Windows Distribution Package Creator
REM Creates a ready-to-distribute ZIP file

echo ========================================
echo NeuroFlow Distribution Package Creator
echo ========================================
echo.

REM Check if dist folder exists
if not exist "dist\NeuroFlow" (
    echo ERROR: dist\NeuroFlow folder not found
    echo Please run build_windows.bat first
    pause
    exit /b 1
)

echo [1/5] Creating distribution folder...
if exist "distribution" rmdir /s /q distribution
mkdir distribution
mkdir "distribution\NeuroFlow"

echo.
echo [2/5] Copying executable and dependencies...
xcopy "dist\NeuroFlow\*" "distribution\NeuroFlow\" /E /I /Y >nul

echo.
echo [3/5] Adding documentation...
copy "README_WINDOWS.md" "distribution\NeuroFlow\README.md" >nul
copy "BUILD_WINDOWS.md" "distribution\NeuroFlow\BUILD_GUIDE.md" >nul
copy "QUICKSTART_WINDOWS.md" "distribution\NeuroFlow\QUICKSTART.md" >nul

REM Create LICENSE if it doesn't exist
if not exist "LICENSE.txt" (
    echo MIT License > "distribution\NeuroFlow\LICENSE.txt"
    echo. >> "distribution\NeuroFlow\LICENSE.txt"
    echo Copyright (c) 2024 NeuroFlow Development Team >> "distribution\NeuroFlow\LICENSE.txt"
)

echo.
echo [4/5] Creating version info...
echo NeuroFlow Windows Distribution > "distribution\NeuroFlow\VERSION.txt"
echo Version: 1.0.0 >> "distribution\NeuroFlow\VERSION.txt"
echo Build Date: %date% %time% >> "distribution\NeuroFlow\VERSION.txt"
echo Platform: Windows 10/11 (64-bit) >> "distribution\NeuroFlow\VERSION.txt"

echo.
echo [5/5] Creating ZIP archive...
powershell -Command "Compress-Archive -Path 'distribution\NeuroFlow' -DestinationPath 'NeuroFlow-Windows-v1.0.zip' -Force"

if exist "NeuroFlow-Windows-v1.0.zip" (
    echo.
    echo ========================================
    echo Distribution package created successfully!
    echo ========================================
    echo.
    echo Package: NeuroFlow-Windows-v1.0.zip
    for %%A in ("NeuroFlow-Windows-v1.0.zip") do echo Size: %%~zA bytes
    echo.
    echo Contents:
    echo - NeuroFlow.exe (Main executable)
    echo - scripts/ (Analysis scripts)
    echo - pvt_masks/ (PVT templates)
    echo - README.md (User guide)
    echo - BUILD_GUIDE.md (Build instructions)
    echo - QUICKSTART.md (Quick start guide)
    echo - LICENSE.txt (MIT License)
    echo - VERSION.txt (Version info)
    echo.
    echo Ready for distribution!
    echo.
) else (
    echo ERROR: Failed to create ZIP archive
    pause
    exit /b 1
)

pause
