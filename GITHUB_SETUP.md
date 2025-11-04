# 🚀 GitHub Setup Guide - NeuroFlow macOS

이 가이드는 NeuroFlow macOS 버전을 GitHub에 push하는 방법을 설명합니다.

---

## 📋 준비사항

1. **GitHub 계정**: https://github.com/HyukJang1
2. **Git 설치 확인**:
   ```bash
   git --version
   ```
   설치되지 않았다면:
   ```bash
   xcode-select --install
   ```

---

## 🔧 Step 1: Git 저장소 초기화

```bash
cd /Users/joon/Desktop/의료저널/Neuroflow_mac

# Git 저장소 초기화
git init

# 사용자 정보 설정 (처음 한 번만)
git config user.name "Hyuk Jang"
git config user.email "your-email@example.com"
```

---

## 📝 Step 2: 파일 추가 및 커밋

```bash
# 모든 파일 추가 (.gitignore에 의해 제외된 파일은 자동 제외)
git add .

# 초기 커밋
git commit -m "Initial commit: NeuroFlow macOS version

Features:
- One-click CT Perfusion analysis
- Interactive web viewer with overlay controls
- Apple design UI with beautiful color scheme
- Advanced stroke metrics (HIR, PRR, CBV Index)
- Smart brain masking with background removal
- PENUMBRA series overlay exclusion
- RGB to scalar conversion for Siemens CT Perfusion
"
```

---

## 🌐 Step 3: GitHub 저장소 연결

### Option A: 기존 저장소에 push (권장)

```bash
# 원격 저장소 추가
git remote add origin https://github.com/HyukJang1/ct-perfusion-auto.git

# 기존 브랜치 확인
git branch -M main

# Push (기존 내용 덮어쓰기 - 주의!)
git push -f origin main
```

### Option B: 새 브랜치로 push

```bash
# 원격 저장소 추가
git remote add origin https://github.com/HyukJang1/ct-perfusion-auto.git

# macOS 브랜치 생성
git checkout -b macos-version

# Push
git push -u origin macos-version
```

---

## 🔄 Step 4: 이후 업데이트

```bash
# 변경사항 확인
git status

# 변경된 파일 추가
git add .

# 커밋
git commit -m "Update: [변경 내용 설명]"

# Push
git push origin main
# 또는
git push origin macos-version
```

---

## 📦 Step 5: Release 생성 (선택사항)

GitHub 웹사이트에서:

1. **Releases** 탭 클릭
2. **"Create a new release"** 클릭
3. **Tag version**: `v1.0.0-macos`
4. **Release title**: `NeuroFlow v1.0.0 - macOS Edition`
5. **Description**:
   ```markdown
   ## 🧠 NeuroFlow v1.0.0 - macOS Edition
   
   ### ✨ Features
   - One-click CT Perfusion analysis
   - Interactive web viewer with overlay controls
   - Apple design UI
   - Advanced stroke metrics
   - Smart brain masking
   
   ### 📦 Installation
   ```bash
   git clone https://github.com/HyukJang1/ct-perfusion-auto.git
   cd ct-perfusion-auto
   pip3 install -r requirements.txt
   python3 ct_perfusion_viewer.py
   ```
   
   ### 🖥️ System Requirements
   - macOS 10.15+
   - Python 3.8+
   - 8GB RAM
   ```

6. **"Publish release"** 클릭

---

## 🏷️ Step 6: README 업데이트

GitHub 저장소의 메인 README를 macOS 버전으로 교체:

```bash
# 기존 README 백업
git mv README.md README_OLD.md

# macOS README를 메인 README로 설정
git mv README_MAC.md README.md

# 커밋 및 push
git add .
git commit -m "Update README for macOS version"
git push origin main
```

---

## 📊 Step 7: GitHub Actions 설정 (선택사항)

자동 테스트를 위한 워크플로우 생성:

```bash
mkdir -p .github/workflows
```

`.github/workflows/test.yml` 파일 생성:

```yaml
name: Test NeuroFlow

on: [push, pull_request]

jobs:
  test:
    runs-on: macos-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Test imports
      run: |
        python -c "import PyQt5; import pydicom; import numpy; print('✅ All imports successful')"
```

---

## 🔐 보안 주의사항

### ⚠️ 절대 커밋하지 말 것:

1. **환자 데이터**:
   - DICOM 파일 (*.dcm)
   - 분석 결과 (analysis_results/)
   - 환자 식별 정보

2. **개인 정보**:
   - API 키
   - 비밀번호
   - 이메일 주소

3. **대용량 파일**:
   - 이미지 파일 (*.png, *.jpg)
   - 빌드 파일

### ✅ .gitignore 확인:

```bash
# .gitignore가 제대로 작동하는지 확인
git status

# 다음 항목들이 "Untracked files"에 나타나지 않아야 함:
# - analysis_results/
# - *.dcm
# - .DS_Store
```

---

## 🎯 권장 브랜치 전략

### Main Branch
- 안정적인 릴리스 버전
- 철저히 테스트된 코드만 merge

### Development Branch
```bash
git checkout -b develop
# 개발 작업 수행
git push -u origin develop
```

### Feature Branches
```bash
git checkout -b feature/new-metric
# 새 기능 개발
git push -u origin feature/new-metric
```

---

## 📞 문제 해결

### Issue 1: "Permission denied (publickey)"

**Solution**: SSH 키 설정
```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
cat ~/.ssh/id_ed25519.pub
# GitHub Settings → SSH Keys에 추가
```

### Issue 2: "Large files detected"

**Solution**: Git LFS 사용
```bash
brew install git-lfs
git lfs install
git lfs track "*.png"
git add .gitattributes
```

### Issue 3: "Merge conflict"

**Solution**: 충돌 해결
```bash
git pull origin main
# 충돌 파일 수동 편집
git add .
git commit -m "Resolve merge conflict"
git push origin main
```

---

## ✅ 체크리스트

Push 전 확인사항:

- [ ] .gitignore 파일 확인
- [ ] 환자 데이터 제외 확인
- [ ] README.md 업데이트
- [ ] requirements.txt 최신화
- [ ] 테스트 코드 실행
- [ ] 커밋 메시지 작성
- [ ] 브랜치 확인

---

## 🎉 완료!

이제 GitHub 저장소에서 다음을 확인할 수 있습니다:

1. **코드**: 모든 Python 스크립트
2. **문서**: README, QUICKSTART, VALIDATION
3. **설정**: requirements.txt, .gitignore
4. **릴리스**: 버전 태그 및 릴리스 노트

저장소 URL: https://github.com/HyukJang1/ct-perfusion-auto
