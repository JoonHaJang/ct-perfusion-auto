@echo off
echo ========================================
echo NeuroFlow Windows Build Script
echo ========================================
echo.

echo [1/3] Cleaning previous build...
if exist dist_new rmdir /s /q dist_new
if exist build_new rmdir /s /q build_new
if exist NeuroFlow_App.spec del /f /q NeuroFlow_App.spec
echo Done.

echo.
echo [2/3] Building with PyInstaller...
pyinstaller --clean --noconfirm --onedir --windowed ^
    --name NeuroFlow_App ^
    --distpath dist_new ^
    --workpath build_new ^
    --add-data "scripts;scripts" ^
    --add-data "pvt_masks;pvt_masks" ^
    ct_perfusion_viewer_windows.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Creating README...
echo NeuroFlow - CT Perfusion Analysis Suite > dist_new\NeuroFlow_App\README.txt
echo Version: 1.0 >> dist_new\NeuroFlow_App\README.txt
echo. >> dist_new\NeuroFlow_App\README.txt
echo Double-click NeuroFlow_App.exe to run >> dist_new\NeuroFlow_App\README.txt

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: dist_new\NeuroFlow_App\NeuroFlow_App.exe
echo.
echo To distribute:
echo 1. Zip the entire "dist_new\NeuroFlow_App" folder
echo 2. Share the zip file with users
echo.
pause
