# NeuroFlow - CT Perfusion Analyzer 설치 가이드

안녕하세요,

NeuroFlow CT Perfusion 자동 분석 프로그램을 공유합니다.

---

## 📥 다운로드

**파일**: NeuroFlow-1.0.0-macOS.zip
**링크**: [여기에 클라우드 링크 삽입]

---

## ⚙️ 설치 방법 (5분 소요)

### 1단계: 압축 해제
다운로드한 ZIP 파일을 더블클릭하여 압축 해제

### 2단계: 의존성 설치 (최초 1회만)
터미널을 열고 다음 명령어 실행:

```bash
cd NeuroFlow
pip3 install -r requirements.txt
```

**참고**: Python 3.8 이상 필요
- 확인: `python3 --version`
- 없으면 설치: https://www.python.org/downloads/

### 3단계: 실행

**방법 A** (추천): Finder에서 `NeuroFlow_Launcher.command` 더블클릭

**방법 B**: 터미널에서
```bash
./NeuroFlow_Launcher.command
```

---

## 🎯 사용 방법

1. **Select Folder** 버튼 클릭
2. DICOM 폴더 선택
3. **Start Analysis** 클릭
4. 분석 완료 후 **View Results** 클릭

**분석 시간**: 약 2-3분
**결과 저장**: `analysis_results/` 폴더

---

## 📋 시스템 요구사항

- macOS 10.15 이상
- Python 3.8 이상
- 8 GB RAM (16 GB 권장)
- 500 MB 저장 공간

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

### PyQt5 설치 실패
```bash
pip3 install --upgrade pip
pip3 install PyQt5
```

---

## 📚 추가 문서

압축 해제한 폴더 안에 다음 문서들이 있습니다:
- **START_HERE.md**: 빠른 시작 가이드
- **README.md**: 전체 기능 설명
- **QUICKSTART.md**: 사용 예제
- **VALIDATION.md**: 검증 결과

---

## 💡 주요 기능

✅ DICOM 자동 분석
✅ CBF, CBV, MTT, Tmax 계산
✅ 3D 인터랙티브 웹 뷰어
✅ 자동 리포트 생성
✅ 원클릭 실행

---

## 🆘 문의

문제가 있으면 연락주세요!

**For Research Use Only - Not for Clinical Diagnosis**
