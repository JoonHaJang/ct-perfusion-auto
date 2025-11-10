#!/bin/bash

# NeuroFlow 배포 패키지 생성 스크립트

echo "🎁 Creating NeuroFlow distribution package..."

# 패키지 이름
PACKAGE_NAME="NeuroFlow_v2.0_macOS"
PACKAGE_DIR="${PACKAGE_NAME}"

# 기존 패키지 삭제
rm -rf "${PACKAGE_DIR}"
rm -f "${PACKAGE_NAME}.zip"

# 패키지 디렉토리 생성
mkdir -p "${PACKAGE_DIR}"
mkdir -p "${PACKAGE_DIR}/scripts"

# 필수 파일 복사
echo "📦 Copying files..."
cp ct_perfusion_viewer.py "${PACKAGE_DIR}/"
cp NeuroFlow_Launcher.command "${PACKAGE_DIR}/"
cp requirements.txt "${PACKAGE_DIR}/"
cp START_HERE.md "${PACKAGE_DIR}/"

# Scripts 복사
cp scripts/generate_dicom_viewer.py "${PACKAGE_DIR}/scripts/"
cp scripts/calculate_pvt_tmax.py "${PACKAGE_DIR}/scripts/"
cp scripts/extract_metrics_from_dicom.py "${PACKAGE_DIR}/scripts/"

# 실행 권한 설정
chmod +x "${PACKAGE_DIR}/NeuroFlow_Launcher.command"

# ZIP 생성
echo "🗜️  Creating ZIP archive..."
zip -r "${PACKAGE_NAME}.zip" "${PACKAGE_DIR}" -x "*.DS_Store" "*.pyc" "__pycache__/*"

# 정리
rm -rf "${PACKAGE_DIR}"

echo "✅ Package created: ${PACKAGE_NAME}.zip"
echo "📊 File size:"
ls -lh "${PACKAGE_NAME}.zip"

echo ""
echo "🚀 Ready to distribute!"
echo "📥 Upload to Google Drive and share the link."
