# GitHub 업로드 가이드

## 1️⃣ 업로드 전 준비

### 파일 정리
```bash
# 현재 폴더에서 실행
cd "C:\Users\USER\Desktop\의료 저널\Neuroflow_mac"

# 빌드 파일 삭제
Remove-Item -Path "build_new", "dist_new", "build", "dist" -Recurse -Force -ErrorAction SilentlyContinue

# 압축 파일 삭제
Remove-Item -Path "*.zip" -Force -ErrorAction SilentlyContinue

# 분석 결과 삭제 (환자 데이터)
Remove-Item -Path "analysis_results" -Recurse -Force -ErrorAction SilentlyContinue
```

### .gitignore 확인
```bash
# .gitignore가 제대로 설정되었는지 확인
cat .gitignore

# 다음 항목들이 포함되어 있어야 함:
# - analysis_results/
# - Research/
# - CTP_MT/
# - data/
# - *.dcm
# - build_new/
# - dist_new/
# - *.zip
```

---

## 2️⃣ Git 초기화 및 커밋

### Git 초기화 (처음 한 번만)
```bash
# Git 초기화
git init

# GitHub 원격 저장소 연결
git remote add origin https://github.com/HyukJang1/ct-perfusion-auto.git

# 기본 브랜치를 main으로 설정
git branch -M main
```

### 파일 추가 및 커밋
```bash
# 모든 파일 추가 (.gitignore에 명시된 파일은 자동 제외)
git add .

# 커밋
git commit -m "Initial release: NeuroFlow v1.0

- Windows/Mac GUI application
- Automatic CT Perfusion analysis
- Corrected CBV Index calculation
- TAC extraction from Penumbra images
- Interactive web viewer
- Validated accuracy (MAE=0.0)"

# GitHub에 푸시
git push -u origin main
```

---

## 3️⃣ GitHub에서 Release 생성

### 웹 브라우저에서:
1. https://github.com/HyukJang1/ct-perfusion-auto 접속
2. "Releases" 클릭
3. "Create a new release" 클릭
4. Tag version: `v1.0.0`
5. Release title: `NeuroFlow v1.0 - Initial Release`
6. Description:
```markdown
# NeuroFlow v1.0 - Initial Release

## 🎉 Features
- ✅ Windows/Mac GUI application
- ✅ Automatic Siemens CT Perfusion analysis
- ✅ Corrected CBV Index (validated in JNIS 2025)
- ✅ TAC extraction from Penumbra images
- ✅ Interactive 3D web viewer
- ✅ Export to JSON/NIfTI

## 📦 Installation

### Requirements
- Python 3.8 or higher
- Required packages (see requirements.txt)

### Quick Start
```bash
git clone https://github.com/HyukJang1/ct-perfusion-auto.git
cd ct-perfusion-auto
pip install -r requirements.txt
python ct_perfusion_viewer_windows.py  # Windows
python ct_perfusion_viewer.py          # Mac
```

## 📊 Clinical Validation
- Corrected CBV Index: AUC 0.83 (N=123, JNIS 2025)
- RGB-to-Scalar conversion: MAE=0.0, RMSE=0.0

## 📝 Documentation
See README.md for detailed usage instructions.

## 🐛 Known Issues
- Requires Python installation
- Large datasets (>500 slices) may be slow

## 🔗 Links
- Paper: [JNIS 2025]
- Documentation: [README.md](README.md)
```

7. "Publish release" 클릭

---

## 4️⃣ 업로드 후 확인

### 확인 사항
- [ ] README.md가 제대로 표시되는지
- [ ] 환자 데이터가 업로드되지 않았는지
- [ ] 모든 필수 파일이 포함되었는지
- [ ] requirements.txt가 정확한지
- [ ] 라이선스 파일이 있는지

### 테스트
```bash
# 다른 폴더에서 클론하여 테스트
cd C:\Temp
git clone https://github.com/HyukJang1/ct-perfusion-auto.git
cd ct-perfusion-auto
pip install -r requirements.txt
python ct_perfusion_viewer_windows.py
```

---

## 5️⃣ 향후 업데이트

### 코드 수정 후
```bash
# 변경사항 확인
git status

# 변경된 파일 추가
git add .

# 커밋
git commit -m "Fix: [설명]"

# 푸시
git push origin main
```

### 새 버전 릴리즈
```bash
# 태그 생성
git tag -a v1.1.0 -m "Version 1.1.0"

# 태그 푸시
git push origin v1.1.0

# GitHub에서 Release 생성
```

---

## 🔒 보안 체크리스트

업로드 전 반드시 확인:
- [ ] 환자 데이터 없음 (analysis_results/, Research/, CTP_MT/)
- [ ] DICOM 파일 없음 (*.dcm)
- [ ] 개인 정보 없음 (이메일, 전화번호 등)
- [ ] API 키 없음
- [ ] 비밀번호 없음
- [ ] 내부 경로 없음 (C:\Users\USER\... 등)

---

## 📧 공유 방법

### 사용자에게 안내
```
NeuroFlow GitHub 저장소:
https://github.com/HyukJang1/ct-perfusion-auto

설치 방법:
1. Python 3.8+ 설치 (https://python.org)
2. 저장소 클론 또는 ZIP 다운로드
3. pip install -r requirements.txt
4. python ct_perfusion_viewer_windows.py 실행

문의: [이메일]
```

---

## 🎯 완료!

이제 전 세계 누구나 NeuroFlow를 사용할 수 있습니다! 🎉
