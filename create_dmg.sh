#!/bin/bash

# NeuroFlow DMG Creator
# Creates a distributable DMG file for macOS

echo "💿 NeuroFlow - DMG Creator"
echo "=========================="
echo ""

# .app 파일 확인
if [ ! -d "dist/NeuroFlow.app" ]; then
    echo "❌ Error: NeuroFlow.app not found"
    echo "Please run ./build_macos_app.sh first"
    exit 1
fi

# 버전 정보
VERSION="1.0.0"
DMG_NAME="NeuroFlow-${VERSION}-macOS"

echo "📦 Creating DMG: ${DMG_NAME}.dmg"
echo ""

# 임시 디렉토리 생성
TMP_DIR="tmp_dmg"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

# .app 복사
echo "📋 Copying application..."
cp -r dist/NeuroFlow.app "$TMP_DIR/"

# Applications 폴더 심볼릭 링크 생성
echo "🔗 Creating Applications symlink..."
ln -s /Applications "$TMP_DIR/Applications"

# README 추가
echo "📝 Adding README..."
cat > "$TMP_DIR/README.txt" << 'EOF'
NeuroFlow - CT Perfusion Auto-Analyzer v1.0.0
==============================================

Installation:
1. Drag NeuroFlow.app to the Applications folder
2. Open NeuroFlow from Applications or Launchpad

First Run:
- macOS may show "NeuroFlow cannot be opened because it is from an unidentified developer"
- Right-click NeuroFlow.app → Open → Open
- Or: System Settings → Privacy & Security → Open Anyway

Usage:
1. Click "Select Folder" and choose your DICOM directory
2. Click "Start Analysis" and wait 2-3 minutes
3. View results in the metrics table
4. Click "View Results" to open the interactive web viewer

System Requirements:
- macOS 10.15 (Catalina) or later
- 8 GB RAM (16 GB recommended)
- 500 MB free disk space

Support:
- GitHub: https://github.com/HyukJang1/ct-perfusion-auto
- Issues: https://github.com/HyukJang1/ct-perfusion-auto/issues

For Research Use Only - Not for Clinical Diagnosis
EOF

# DMG 생성
echo "💿 Creating DMG file..."
rm -f "${DMG_NAME}.dmg"

hdiutil create -volname "NeuroFlow" \
    -srcfolder "$TMP_DIR" \
    -ov -format UDZO \
    "${DMG_NAME}.dmg"

# 정리
rm -rf "$TMP_DIR"

if [ -f "${DMG_NAME}.dmg" ]; then
    echo ""
    echo "✅ DMG created successfully!"
    echo ""
    
    # DMG 크기 확인
    DMG_SIZE=$(du -sh "${DMG_NAME}.dmg" | cut -f1)
    echo "📊 DMG size: $DMG_SIZE"
    echo "📍 Location: $(pwd)/${DMG_NAME}.dmg"
    echo ""
    
    echo "🚀 Distribution ready!"
    echo ""
    echo "Next steps:"
    echo "1. Test the DMG:"
    echo "   open ${DMG_NAME}.dmg"
    echo ""
    echo "2. Upload to GitHub Releases"
    echo "3. Share with users"
    echo ""
else
    echo ""
    echo "❌ DMG creation failed!"
    exit 1
fi
