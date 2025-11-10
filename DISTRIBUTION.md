# 🚀 NeuroFlow macOS 배포 가이드

PyQt5 앱을 macOS .app 번들로 만드는 것은 복잡하고 불안정합니다.
대신 **ZIP 배포 방식**을 권장합니다.

---

## 📦 방법 1: ZIP 배포 (권장)

### 장점
- ✅ 안정적 - Qt 플랫폼 플러그인 문제 없음
- ✅ 간단함 - 복잡한 빌드 과정 불필요
- ✅ 업데이트 용이 - 파일만 교체하면 됨
- ✅ 디버깅 가능 - 오류 메시지 확인 가능

### 배포 파일 생성

```bash
cd /Users/joon/Desktop/의료저널/Neuroflow_mac

# 배포용 ZIP 생성
./create_distribution_zip.sh
```

### 사용자 설치 방법

1. **ZIP 다운로드 및 압축 해제**
2. **터미널에서 실행**:
   ```bash
   cd NeuroFlow
   ./NeuroFlow_Launcher.command
   ```
3. **또는 Finder에서 더블클릭**: `NeuroFlow_Launcher.command`

---

## 📦 방법 2: Automator 앱 (GUI 실행)

### .app 파일 생성 (py2app 없이)

1. **Automator 열기**
2. **새로운 문서** → **응용 프로그램** 선택
3. **"셸 스크립트 실행"** 액션 추가
4. 다음 스크립트 입력:

```bash
cd "$(dirname "$0")/../../.."
python3 ct_perfusion_viewer.py
```

5. **파일** → **저장** → `NeuroFlow.app`으로 저장

### 아이콘 추가 (선택사항)

```bash
# 아이콘 파일(.icns)을 NeuroFlow.app에 적용
# 우클릭 → 정보 가져오기 → 아이콘 드래그앤드롭
```

---

## 📦 방법 3: 독립 실행형 번들 (고급)

### Platypus 사용

```bash
# Platypus 설치
brew install --cask platypus

# GUI에서 설정:
# - Script Type: Shell
# - Script Path: NeuroFlow_Launcher.command
# - Interface: None
# - Create App Bundle
```

---

## 🎯 권장 배포 방식

### 최종 사용자용

```
NeuroFlow-1.0.0-macOS.zip
├── NeuroFlow/
│   ├── NeuroFlow_Launcher.command  ← 더블클릭하여 실행
│   ├── ct_perfusion_viewer.py
│   ├── scripts/
│   ├── requirements.txt
│   └── README.md
```

### 개발자/연구자용

```bash
# 1. 저장소 클론
git clone https://github.com/JoonHaJang/ct-perfusion-auto.git
cd ct-perfusion-auto

# 2. 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 실행
python3 ct_perfusion_viewer.py
```

---

## 🔧 배포 스크립트 생성

아래 스크립트를 실행하면 배포용 ZIP이 자동 생성됩니다:

```bash
./create_distribution_zip.sh
```

생성된 파일: `NeuroFlow-1.0.0-macOS.zip`

---

## 📝 README 포함 내용

배포 ZIP에 포함할 README:

```markdown
# NeuroFlow - CT Perfusion Analyzer

## 설치 방법

1. ZIP 압축 해제
2. 터미널 열기
3. 다음 명령어 실행:

\`\`\`bash
cd NeuroFlow
pip3 install -r requirements.txt
./NeuroFlow_Launcher.command
\`\`\`

## 또는 Finder에서

`NeuroFlow_Launcher.command` 파일을 더블클릭

## 시스템 요구사항

- macOS 10.15+
- Python 3.8+
- 8GB RAM

## 문제 해결

### "Permission denied" 오류

\`\`\`bash
chmod +x NeuroFlow_Launcher.command
\`\`\`

### 의존성 오류

\`\`\`bash
pip3 install -r requirements.txt
\`\`\`
```

---

## ✅ 결론

**py2app은 PyQt5와 호환성 문제가 있어 권장하지 않습니다.**

대신:
1. **일반 사용자**: ZIP + Launcher 스크립트
2. **기술 사용자**: Git clone + pip install
3. **GUI 필요 시**: Automator 또는 Platypus

이 방법이 훨씬 안정적이고 유지보수가 쉽습니다.
