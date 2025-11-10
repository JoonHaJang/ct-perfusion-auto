#!/bin/bash

# NeuroFlow macOS App Builder (Fixed for PyQt5 symlink issues)
# This script builds the app and fixes PyQt5 framework symlink conflicts

echo "🧠 NeuroFlow - macOS App Builder (Fixed)"
echo "=========================================="
echo ""

# 현재 디렉토리 확인
if [ ! -f "ct_perfusion_viewer.py" ]; then
    echo "❌ Error: ct_perfusion_viewer.py not found"
    exit 1
fi

# 이전 빌드 정리
echo "🧹 Cleaning previous builds..."
rm -rf build dist NeuroFlow.app

# 빌드 시작
echo ""
echo "🔨 Building NeuroFlow.app (Step 1/3)..."
pyinstaller --clean --noconfirm NeuroFlow_Bundle.spec 2>&1 | grep -E "(INFO|WARNING|ERROR)" | tail -20

# 빌드 실패 시 수동으로 심볼릭 링크 문제 해결
if [ ! -d "dist/NeuroFlow.app" ]; then
    echo ""
    echo "⚠️  Initial build failed (expected). Fixing PyQt5 symlinks..."
    echo ""
    
    # dist 폴더의 중복 심볼릭 링크 제거
    echo "🔧 Removing duplicate symlinks..."
    find dist/NeuroFlow/_internal/PyQt5/Qt5/lib -name "*.framework" -type d 2>/dev/null | while read framework; do
        if [ -L "$framework/Resources" ]; then
            rm -f "$framework/Resources"
        fi
        if [ -L "$framework/Versions/Current" ]; then
            rm -f "$framework/Versions/Current"
        fi
    done
    
    # 재빌드 (no-clean)
    echo ""
    echo "🔨 Rebuilding NeuroFlow.app (Step 2/3)..."
    pyinstaller --noconfirm NeuroFlow_Bundle.spec 2>&1 | grep -E "(INFO|WARNING|ERROR)" | tail -20
fi

# 최종 확인
if [ -d "dist/NeuroFlow.app" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    
    # 앱 크기 확인
    APP_SIZE=$(du -sh dist/NeuroFlow.app | cut -f1)
    echo "📊 Application size: $APP_SIZE"
    echo "📍 Location: $(pwd)/dist/NeuroFlow.app"
    echo ""
    
    # 실행 권한 부여
    chmod +x dist/NeuroFlow.app/Contents/MacOS/NeuroFlow
    
    # scripts 폴더 확인
    if [ -d "dist/NeuroFlow.app/Contents/MacOS/scripts" ] || [ -d "dist/NeuroFlow.app/Contents/Resources/scripts" ]; then
        echo "✅ Scripts folder included"
    else
        echo "⚠️  Warning: scripts folder not found in app bundle"
    fi
    
    echo ""
    echo "🚀 Next steps:"
    echo "1. Test the app:"
    echo "   open dist/NeuroFlow.app"
    echo ""
    echo "2. Create DMG:"
    echo "   ./create_dmg.sh"
    echo ""
    echo "3. Or copy to Applications:"
    echo "   cp -r dist/NeuroFlow.app /Applications/"
    echo ""
else
    echo ""
    echo "❌ Build failed!"
    echo ""
    echo "Trying alternative method with py2app..."
    echo "Install py2app: pip3 install py2app"
    echo "Then run: python3 setup.py py2app"
    exit 1
fi
