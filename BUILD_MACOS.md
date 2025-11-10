# 🍎 NeuroFlow macOS 실행 파일 빌드 가이드

이 가이드는 NeuroFlow를 macOS용 독립 실행 파일(.app)로 빌드하는 방법을 설명합니다.

---

## 📋 준비사항

### 1. 시스템 요구사항
- **macOS**: 10.15 (Catalina) 이상
- **Python**: 3.8 이상
- **Xcode Command Line Tools**: 설치 필요

### 2. Xcode Command Line Tools 설치

```bash
xcode-select --install
```

### 3. PyInstaller 설치

```bash
pip3 install pyinstaller
```

---

## 🔨 빌드 방법

### 방법 1: 자동 빌드 스크립트 (권장)

```bash
cd /Users/joon/Desktop/의료저널/Neuroflow_mac

# .app 파일 생성
./build_macos_app.sh
```

**빌드 시간**: 약 5-10분

**결과물**: `dist/NeuroFlow.app`

### 방법 2: 수동 빌드

```bash
# 이전 빌드 정리
rm -rf build dist

# PyInstaller 실행
pyinstaller --clean --noconfirm NeuroFlow_macOS.spec

# 결과 확인
ls -lh dist/NeuroFlow.app
```

---

## 📦 DMG 파일 생성 (배포용)

### 자동 DMG 생성

```bash
./create_dmg.sh
```

**결과물**: `NeuroFlow-1.0.0-macOS.dmg`

### 수동 DMG 생성

```bash
# 임시 폴더 생성
mkdir tmp_dmg
cp -r dist/NeuroFlow.app tmp_dmg/
ln -s /Applications tmp_dmg/Applications

# DMG 생성
hdiutil create -volname "NeuroFlow" \
    -srcfolder tmp_dmg \
    -ov -format UDZO \
    NeuroFlow-1.0.0-macOS.dmg

# 정리
rm -rf tmp_dmg
```

---

## ✅ 빌드 결과 확인

### 1. .app 파일 테스트

```bash
# Finder에서 열기
open dist/NeuroFlow.app

# 또는 터미널에서 실행
dist/NeuroFlow.app/Contents/MacOS/NeuroFlow
```

### 2. 파일 크기 확인

```bash
du -sh dist/NeuroFlow.app
# 예상 크기: 약 150-250 MB
```

### 3. 번들 구조 확인

```bash
tree -L 3 dist/NeuroFlow.app
```

예상 구조:
```
NeuroFlow.app/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/
│   │   └── NeuroFlow (실행 파일)
│   ├── Resources/
│   │   └── scripts/ (Python 스크립트)
│   └── Frameworks/ (의존성 라이브러리)
```

---

## 🚀 배포 방법

### 1. 로컬 설치

```bash
# Applications 폴더에 복사
cp -r dist/NeuroFlow.app /Applications/

# Launchpad에서 실행
```

### 2. DMG 배포

```bash
# DMG 파일 생성
./create_dmg.sh

# 사용자에게 DMG 파일 전달
# 사용자는 DMG를 열고 NeuroFlow.app을 Applications로 드래그
```

### 3. GitHub Release

```bash
# GitHub Releases에 DMG 업로드
# 1. GitHub 저장소 → Releases → Create new release
# 2. Tag: v1.0.0-macos
# 3. Upload: NeuroFlow-1.0.0-macOS.dmg
```

---

## 🔐 코드 서명 (선택사항)

### Apple Developer 계정이 있는 경우

```bash
# 1. 개발자 인증서 확인
security find-identity -v -p codesigning

# 2. .spec 파일에서 codesign_identity 설정
# codesign_identity='Developer ID Application: Your Name (TEAM_ID)'

# 3. 재빌드
pyinstaller --clean NeuroFlow_macOS.spec

# 4. 서명 확인
codesign -dv --verbose=4 dist/NeuroFlow.app
```

### Notarization (공증)

```bash
# 1. DMG 생성
./create_dmg.sh

# 2. Apple에 업로드
xcrun notarytool submit NeuroFlow-1.0.0-macOS.dmg \
    --apple-id "your-email@example.com" \
    --team-id "TEAM_ID" \
    --password "app-specific-password"

# 3. 공증 완료 후 staple
xcrun stapler staple NeuroFlow-1.0.0-macOS.dmg
```

---

## 🐛 문제 해결

### Issue 1: "NeuroFlow cannot be opened"

**원인**: 서명되지 않은 앱

**해결**:
```bash
# 사용자에게 안내
# 1. 우클릭 → 열기 → 열기
# 또는
# 2. 시스템 설정 → 개인정보 보호 및 보안 → 확인 없이 열기
```

### Issue 2: 빌드 시 "ModuleNotFoundError"

**원인**: 숨겨진 import 누락

**해결**:
```python
# NeuroFlow_macOS.spec 파일에 추가
hiddenimports = [
    'missing_module_name',
]
```

### Issue 3: .app 실행 시 크래시

**원인**: 의존성 라이브러리 누락

**해결**:
```bash
# 터미널에서 실행하여 에러 확인
dist/NeuroFlow.app/Contents/MacOS/NeuroFlow

# 누락된 라이브러리 확인 후 .spec 파일에 추가
```

### Issue 4: 파일 크기가 너무 큼

**해결**:
```python
# NeuroFlow_macOS.spec에서 불필요한 모듈 제외
excludes=[
    'matplotlib',
    'pandas',
    'IPython',
    'jupyter',
    # 기타 사용하지 않는 대용량 라이브러리
]
```

---

## 📊 빌드 최적화

### 1. UPX 압축 활성화

```python
# .spec 파일에서
upx=True,
upx_exclude=[],
```

### 2. 불필요한 파일 제외

```python
# Analysis에서
excludes=[
    'matplotlib',
    'pandas',
    'tkinter',
],
```

### 3. 단일 파일 빌드 (선택사항)

```python
# EXE에서
a.scripts,
a.binaries,
a.zipfiles,
a.datas,
[],
name='NeuroFlow',
debug=False,
strip=False,
upx=True,
console=False,
```

---

## 📝 체크리스트

빌드 전:
- [ ] Python 3.8+ 설치 확인
- [ ] PyInstaller 설치 확인
- [ ] 모든 의존성 설치 확인
- [ ] scripts/ 폴더 존재 확인

빌드 후:
- [ ] .app 파일 실행 테스트
- [ ] DICOM 폴더 선택 테스트
- [ ] 분석 기능 테스트
- [ ] 웹 뷰어 열기 테스트

배포 전:
- [ ] DMG 파일 생성
- [ ] DMG 마운트 테스트
- [ ] 다른 Mac에서 설치 테스트
- [ ] README.txt 포함 확인

---

## 🎉 완료!

이제 다음 파일들이 생성되었습니다:

1. **dist/NeuroFlow.app** - macOS 실행 파일
2. **NeuroFlow-1.0.0-macOS.dmg** - 배포용 DMG

사용자는 DMG 파일을 다운로드하여 NeuroFlow.app을 Applications 폴더로 드래그하면 됩니다!
