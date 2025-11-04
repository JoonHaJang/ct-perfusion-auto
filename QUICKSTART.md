# 🚀 빠른 시작 가이드

CT Perfusion Auto-Analyzer를 5분 안에 시작하는 방법입니다.

---

## ⚡ 3단계로 시작하기

### **1단계: 설치** (1분)

```bash
# 저장소 이동
cd ct-perfusion-auto

# 패키지 설치
pip install PyQt5 pydicom numpy Pillow scipy
```

### **2단계: 실행** (10초)

```bash
# GUI 실행
python ct_perfusion_viewer.py
```

### **3단계: 분석** (2-3분)

1. **"폴더 선택"** 버튼 클릭
2. DICOM 폴더 선택
3. **"분석 시작"** 버튼 클릭
4. 결과 확인!

---

## 📊 결과 확인

### **지표 테이블**
```
┌─────────────────────────────────────┐
│  Hypoperfusion:  348.1 ml           │
│  Infarct Core:   8.0 ml             │
│  Penumbra:       340.1 ml           │
│  Mismatch Ratio: 43.51              │
│  CBV Index:      0.85               │
└─────────────────────────────────────┘
```

### **웹 뷰어**
- **"웹 뷰어 열기"** 버튼 클릭
- 브라우저에서 모든 Perfusion 맵 확인
- 오버레이 토글로 마스크 ON/OFF

---

## 🎨 웹 뷰어 사용법

### **기본 조작**
- 🖱️ **마우스 휠**: 슬라이스 이동
- 🖱️ **썸네일 클릭**: 특정 슬라이스로 이동
- 🔘 **오버레이 버튼**: 마스크 ON/OFF

### **오버레이 색상**
- ⚫ **Tmax >6s**: 짙은 회색 (전체 허혈)
- ⬛ **Core**: 검은색 (이미 손상)
- 🔵 **Penumbra**: 시안 (구제 가능)

---

## 📁 출력 파일

```
analysis_results/
├── perfusion_metrics.json      ← 지표 JSON
├── masks.npz                    ← 마스크 파일
└── viewer/
    └── viewer.html              ← 웹 뷰어 (브라우저에서 열기)
```

---

## 🐛 문제 해결

### **"지표 추출 실패"**
→ DICOM 폴더 경로 확인

### **"웹 뷰어 생성 실패"**
→ `viewer` 폴더 삭제 후 재실행

### **"오버레이가 보이지 않음"**
→ 브라우저 캐시 삭제 (Ctrl+Shift+Delete)

---

## 📚 더 알아보기

- **상세 문서**: [README.md](README.md)
- **검증 문서**: [VALIDATION.md](VALIDATION.md)
- **문제 해결**: [README.md#문제-해결](README.md#-문제-해결)

---

**🎉 이제 CT Perfusion 분석을 시작하세요!**
