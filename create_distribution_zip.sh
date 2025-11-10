#!/bin/bash

# NeuroFlow macOS Distribution ZIP Creator
# 배포용 ZIP 파일 생성

echo "📦 NeuroFlow - Distribution ZIP Creator"
echo "========================================"
echo ""

VERSION="1.0.0"
DIST_NAME="NeuroFlow-${VERSION}-macOS"
TEMP_DIR="dist_temp"

# 이전 빌드 정리
echo "🧹 Cleaning previous builds..."
rm -rf "$TEMP_DIR"
rm -f "${DIST_NAME}.zip"

# 임시 디렉토리 생성
mkdir -p "$TEMP_DIR/NeuroFlow"

# 필수 파일 복사
echo "📋 Copying files..."

# Python 파일
cp ct_perfusion_viewer.py "$TEMP_DIR/NeuroFlow/"

# Scripts 폴더
cp -r scripts "$TEMP_DIR/NeuroFlow/"

# 의존성 파일
cp requirements.txt "$TEMP_DIR/NeuroFlow/"

# 문서
cp README_MAC.md "$TEMP_DIR/NeuroFlow/README.md"
cp QUICKSTART.md "$TEMP_DIR/NeuroFlow/"
cp VALIDATION.md "$TEMP_DIR/NeuroFlow/"

# 실행 스크립트
cp NeuroFlow_Launcher.command "$TEMP_DIR/NeuroFlow/"
chmod +x "$TEMP_DIR/NeuroFlow/NeuroFlow_Launcher.command"

# 사용자 가이드 생성
cat > "$TEMP_DIR/NeuroFlow/START_HERE.md" << 'EOF'
# 🧠 NeuroFlow - CT Perfusion Analyzer

## 🚀 빠른 시작

### 1. 의존성 설치 (최초 1회만)

터미널을 열고 다음 명령어를 실행하세요:

```bash
cd NeuroFlow
pip3 install -r requirements.txt
```

### 2. 프로그램 실행

#### 방법 A: Finder에서 실행
`NeuroFlow_Launcher.command` 파일을 더블클릭

#### 방법 B: 터미널에서 실행
```bash
cd NeuroFlow
./NeuroFlow_Launcher.command
```

#### 방법 C: Python 직접 실행
```bash
cd NeuroFlow
python3 ct_perfusion_viewer.py
```

---

## 📖 사용 방법

1. **Select Folder** 버튼 클릭
2. DICOM 폴더 선택
3. **Start Analysis** 버튼 클릭
4. 분석 완료 후 **View Results** 클릭

---

## ⚙️ 시스템 요구사항

- **macOS**: 10.15 (Catalina) 이상
- **Python**: 3.8 이상
- **RAM**: 8 GB (16 GB 권장)
- **저장 공간**: 500 MB

---

## 🐛 문제 해결

### "Permission denied" 오류

```bash
chmod +x NeuroFlow_Launcher.command
```

### Python 모듈 오류

```bash
pip3 install -r requirements.txt
```

### PyQt5 설치 오류

```bash
pip3 install --upgrade pip
pip3 install PyQt5
```

---

## 📚 추가 문서

- **README.md**: 전체 기능 설명
- **QUICKSTART.md**: 빠른 시작 가이드
- **VALIDATION.md**: 검증 및 테스트

---

## 💡 팁

- 분석 시간: 약 2-3분
- 결과는 `analysis_results/` 폴더에 저장됩니다
- 웹 뷰어는 기본 브라우저에서 열립니다

---

## 🆘 지원

- GitHub: https://github.com/JoonHaJang/ct-perfusion-auto
- Issues: https://github.com/JoonHaJang/ct-perfusion-auto/issues

---

**For Research Use Only - Not for Clinical Diagnosis**
EOF

# ZIP 생성
echo "🗜️  Creating ZIP archive..."
cd "$TEMP_DIR"
zip -r "../${DIST_NAME}.zip" NeuroFlow -x "*.DS_Store" -x "__pycache__/*" -x "*.pyc"
cd ..

# 정리
rm -rf "$TEMP_DIR"

# 결과 확인
if [ -f "${DIST_NAME}.zip" ]; then
    ZIP_SIZE=$(du -sh "${DIST_NAME}.zip" | cut -f1)
    echo ""
    echo "✅ Distribution ZIP created successfully!"
    echo ""
    echo "📦 File: ${DIST_NAME}.zip"
    echo "📊 Size: $ZIP_SIZE"
    echo "📍 Location: $(pwd)/${DIST_NAME}.zip"
    echo ""
    echo "🚀 배포 준비 완료!"
    echo ""
    echo "다음 단계:"
    echo "1. ZIP 파일을 사용자에게 전달"
    echo "2. 사용자는 압축 해제 후 START_HERE.md 참고"
    echo "3. NeuroFlow_Launcher.command 실행"
    echo ""
else
    echo ""
    echo "❌ ZIP creation failed!"
    exit 1
fi
