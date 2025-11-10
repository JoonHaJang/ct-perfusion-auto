@echo off
echo ========================================
echo NeuroFlow Windows Build
echo ========================================
echo.

echo [1/3] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo Done.

echo.
echo [2/3] Building with PyInstaller...
pyinstaller --clean NeuroFlow.spec
if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Build completed!
echo.
echo ========================================
echo Executable: dist\NeuroFlow\NeuroFlow.exe
echo ========================================
echo.
echo To test: cd dist\NeuroFlow && NeuroFlow.exe
echo.
pause
