#!/bin/bash

# NeuroFlow macOS App Builder using py2app
# py2app is more reliable for PyQt5 applications on macOS

echo "🧠 NeuroFlow - macOS App Builder (py2app)"
echo "=========================================="
echo ""

# 현재 디렉토리 확인
if [ ! -f "ct_perfusion_viewer.py" ]; then
    echo "❌ Error: ct_perfusion_viewer.py not found"
    exit 1
fi

# py2app 설치 확인
if ! python3 -c "import py2app" 2>/dev/null; then
    echo "📦 Installing py2app..."
    pip3 install py2app
    echo ""
fi

# 이전 빌드 정리
echo "🧹 Cleaning previous builds..."
rm -rf build dist NeuroFlow.app

# 빌드 시작
echo ""
echo "🔨 Building NeuroFlow.app with py2app..."
echo "This may take 5-10 minutes..."
echo ""

python3 setup_py2app.py py2app

# 빌드 결과 확인
if [ -d "dist/NeuroFlow.app" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    
    # 앱 크기 확인
    APP_SIZE=$(du -sh dist/NeuroFlow.app | cut -f1)
    echo "📊 Application size: $APP_SIZE"
    echo "📍 Location: $(pwd)/dist/NeuroFlow.app"
    echo ""
    
    # 번들 구조 확인
    echo "📦 Bundle structure:"
    if [ -d "dist/NeuroFlow.app/Contents/Resources/scripts" ]; then
        echo "   ✅ scripts/ folder included"
        SCRIPT_COUNT=$(ls dist/NeuroFlow.app/Contents/Resources/scripts/*.py 2>/dev/null | wc -l)
        echo "   ✅ $SCRIPT_COUNT Python scripts found"
    else
        echo "   ⚠️  scripts/ folder not found"
    fi
    
    if [ -f "dist/NeuroFlow.app/Contents/MacOS/NeuroFlow" ]; then
        echo "   ✅ Executable found"
    fi
    
    echo ""
    echo "🚀 Next steps:"
    echo "1. Test the app:"
    echo "   open dist/NeuroFlow.app"
    echo ""
    echo "2. Test with sample data:"
    echo "   # Open the app, select DICOM folder, and run analysis"
    echo ""
    echo "3. Create DMG for distribution:"
    echo "   ./create_dmg.sh"
    echo ""
    echo "4. Or install to Applications:"
    echo "   cp -r dist/NeuroFlow.app /Applications/"
    echo ""
else
    echo ""
    echo "❌ Build failed!"
    echo ""
    echo "Common issues:"
    echo "1. Missing dependencies: pip3 install -r requirements.txt"
    echo "2. py2app not installed: pip3 install py2app"
    echo "3. Check error messages above"
    exit 1
fi
