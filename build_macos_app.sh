#!/bin/bash

# NeuroFlow macOS Application Builder
# This script builds a standalone .app bundle for macOS

echo "🧠 NeuroFlow - macOS Application Builder"
echo "=========================================="
echo ""

# 현재 디렉토리 확인
if [ ! -f "ct_perfusion_viewer.py" ]; then
    echo "❌ Error: ct_perfusion_viewer.py not found"
    echo "Please run this script from the Neuroflow_mac directory"
    exit 1
fi

# Python 버전 확인
echo "📍 Checking Python version..."
python3 --version

# PyInstaller 확인
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip3 install pyinstaller
fi

# 이전 빌드 정리
echo ""
echo "🧹 Cleaning previous builds..."
rm -rf build dist NeuroFlow.app

# 빌드 시작
echo ""
echo "🔨 Building NeuroFlow.app..."
echo "This may take 5-10 minutes..."
echo ""

pyinstaller --clean --noconfirm NeuroFlow_macOS.spec

# 빌드 결과 확인
if [ -d "dist/NeuroFlow.app" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📦 Application location:"
    echo "   dist/NeuroFlow.app"
    echo ""
    
    # 앱 크기 확인
    APP_SIZE=$(du -sh dist/NeuroFlow.app | cut -f1)
    echo "📊 Application size: $APP_SIZE"
    echo ""
    
    # 실행 권한 부여
    chmod +x dist/NeuroFlow.app/Contents/MacOS/NeuroFlow
    
    echo "🚀 Next steps:"
    echo "1. Test the app:"
    echo "   open dist/NeuroFlow.app"
    echo ""
    echo "2. Create DMG for distribution:"
    echo "   ./create_dmg.sh"
    echo ""
    echo "3. Or copy to Applications:"
    echo "   cp -r dist/NeuroFlow.app /Applications/"
    echo ""
else
    echo ""
    echo "❌ Build failed!"
    echo "Please check the error messages above"
    exit 1
fi
