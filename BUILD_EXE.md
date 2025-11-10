# 🚀 실행파일 빌드 가이드

## 📋 준비사항

### 1. PyInstaller 설치
```bash
pip install pyinstaller
```

### 2. 필수 패키지 설치
```bash
pip install -r requirements.txt
```

---

## 🔨 빌드 방법

### 방법 1: spec 파일 사용 (권장)
```bash
pyinstaller build_exe.spec
```

### 방법 2: 직접 명령어
```bash
# 폴더 형태 (권장 - 빠름)
pyinstaller --onedir --windowed --name="CTPerfusion" ct_perfusion_viewer.py

# 단일 파일 (느림, 크기 큼)
pyinstaller --onefile --windowed --name="CTPerfusion" ct_perfusion_viewer.py
```

---

## 📁 빌드 결과

```
dist/
└── CTPerfusion/
    ├── CTPerfusion.exe          # 실행 파일
    ├── scripts/                 # 분석 스크립트
    ├── ctperf/                  # 핵심 모듈
    └── [Python 런타임 + 라이브러리]
```

---

## 🎯 배포 패키지 만들기

### 1. 필요한 파일만 복사
```bash
# 새 폴더 생성
mkdir CTPerfusion_v1.0

# 실행 파일 복사
xcopy /E /I dist\CTPerfusion CTPerfusion_v1.0

# README 추가
copy README_USER.txt CTPerfusion_v1.0\
```

### 2. 압축
```bash
# 7-Zip 사용
7z a -tzip CTPerfusion_v1.0.zip CTPerfusion_v1.0\
```

---

## 📝 사용자용 README (README_USER.txt)

```
===========================================
CT Perfusion 원스탑 분석기 v1.0
===========================================

[사용 방법]
1. CTPerfusion.exe 실행
2. "폴더 선택" 버튼 클릭
3. DICOM 폴더 선택
4. "분석 시작" 버튼 클릭
5. 완료 후 "웹 뷰어 열기" 버튼 클릭

[시스템 요구사항]
- Windows 10 이상
- 메모리: 8GB 이상 권장
- 디스크: 500MB 이상 여유 공간

[결과 저장 위치]
- 실행 파일과 같은 폴더의 analysis_results/

[문의]
- 이메일: support@example.com
===========================================
```

---

## ⚠️ 주의사항

### 1. 빌드 시간
- 첫 빌드: 5-10분 소요
- 재빌드: 2-3분 소요

### 2. 파일 크기
- 폴더 형태: ~200-250 MB
- 압축 후: ~80-100 MB

### 3. 바이러스 백신 경고
- PyInstaller로 만든 실행파일은 일부 백신에서 오탐지 가능
- 디지털 서명 추가 권장 (선택사항)

### 4. 테스트
```bash
# 빌드 후 반드시 테스트
cd dist\CTPerfusion
CTPerfusion.exe
```

---

## 🐛 문제 해결

### 1. "Failed to execute script" 오류
```bash
# 콘솔 모드로 빌드하여 오류 확인
pyinstaller --onedir --console --name="CTPerfusion_debug" ct_perfusion_viewer.py
```

### 2. 모듈을 찾을 수 없음
```bash
# hiddenimports에 추가
# build_exe.spec 파일의 hiddenimports 리스트에 모듈명 추가
```

### 3. 실행 파일이 너무 큼
```bash
# UPX 압축 사용 (이미 적용됨)
# 또는 불필요한 패키지 제외
```

---

## 📊 빌드 최적화

### 1. 빌드 캐시 삭제
```bash
rmdir /S /Q build
rmdir /S /Q dist
```

### 2. spec 파일 수정
- `excludes`에 불필요한 패키지 추가
- `datas`에 필요한 파일만 포함

### 3. 가상환경 사용 (권장)
```bash
# 깨끗한 환경에서 빌드
python -m venv venv_build
venv_build\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller build_exe.spec
```

---

## ✅ 배포 체크리스트

- [ ] 빌드 완료
- [ ] 실행 파일 테스트
- [ ] 다른 PC에서 테스트
- [ ] README_USER.txt 작성
- [ ] 압축 파일 생성
- [ ] 버전 번호 확인
- [ ] 배포!

---

**버전**: 1.0.0  
**최종 업데이트**: 2024-10-27
