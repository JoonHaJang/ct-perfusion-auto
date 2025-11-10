# 🧠 NeuroFlow - CT Perfusion Analyzer

**macOS용 뇌졸중 CT Perfusion 분석 프로그램**

---

## 📥 설치 방법 (3분)

### 1️⃣ 다운로드 & 압축 해제
- ZIP 파일 다운로드
- 더블클릭하여 압축 해제
- `NeuroFlow` 폴더 확인

### 2️⃣ Python 패키지 설치
터미널을 열고 다음 명령어 실행:

```bash
cd NeuroFlow
pip3 install -r requirements.txt
```

**설치 시간**: 약 2-3분

### 3️⃣ 실행
`NeuroFlow_Launcher.command` 파일을 **더블클릭**

> ⚠️ 첫 실행 시 "확인되지 않은 개발자" 경고가 나올 수 있습니다.
> → **우클릭 → 열기**를 선택하세요.

---

## 🚀 사용 방법

### 기본 워크플로우

1. **폴더 선택**: "Select Folder" 버튼 클릭
2. **분석 시작**: "Start Analysis" 버튼 클릭
3. **결과 확인**: 
   - 좌측: 분석 메트릭 (CBV, CBF, MTT, Tmax, PVT 등)
   - 우측: 웹 뷰어 자동 열림

### 분석 결과

#### 📊 Perfusion Metrics
- **CBV** (Cerebral Blood Volume): 뇌혈류량
- **CBF** (Cerebral Blood Flow): 뇌혈류속도
- **MTT** (Mean Transit Time): 평균 통과 시간
- **Tmax**: 최대 도달 시간
- **Hypoperfusion Volume**: 저관류 부피 (Tmax > 6초)

#### 🧠 PVT (Prolonged Venous Transit)
- **정맥동 혈류 지연** 평가
- **SSS Tmax**: Superior Sagittal Sinus 평균 Tmax
- **Torcula Tmax**: Confluence of Sinuses 평균 Tmax
- **PVT Status**: PVT+ (지연 있음) / PVT- (정상)
- **Threshold 조정**: 5-15초 (기본값: 10초)

#### 🌐 웹 뷰어
- **인터랙티브 시각화**: 슬라이스별 탐색
- **오버레이 토글**:
  - 🟢 Hypoperfusion (Tmax ≥ 6s)
  - 🔴 Core (Tmax ≥ 10s & CBV < 2.0)
  - 🟡 Penumbra (구제 가능 영역)
  - 🟡 SSS ROI (정맥동 영역)
  - 🔵 Torcula ROI (정맥동 영역)
- **색상/투명도 조절**: 각 오버레이별 커스터마이징

---

## 📁 결과 파일 구조

```
analysis_results/
└── [환자명_날짜]/
    ├── perfusion_metrics.json    # 분석 메트릭
    ├── pvt_result.json           # PVT 결과
    ├── masks.npz                 # 오버레이 마스크
    ├── nifti/                    # NIfTI 파일
    │   ├── tmax.nii.gz
    │   ├── cbv.nii.gz
    │   └── ...
    ├── pvt_masks/                # PVT ROI 마스크
    │   ├── sss_roi.nii.gz
    │   ├── torcula_roi.nii.gz
    │   └── ...
    └── viewer/                   # 웹 뷰어
        └── viewer.html
```

---

## ⚙️ 시스템 요구사항

### 필수
- **OS**: macOS 10.15 (Catalina) 이상
- **Python**: 3.8 이상
- **RAM**: 8GB 이상 권장
- **저장공간**: 500MB 이상

### Python 패키지
- PyQt5 >= 5.15.0
- pydicom >= 2.3.0
- numpy >= 1.21.0
- Pillow >= 9.0.0
- scipy >= 1.7.0
- nibabel >= 3.2.0

---

## 🔧 문제 해결

### Python이 설치되지 않은 경우
```bash
# Homebrew 설치 (없는 경우)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 설치
brew install python@3.11
```

### 패키지 설치 오류
```bash
# pip 업그레이드
pip3 install --upgrade pip

# 패키지 재설치
pip3 install -r requirements.txt --force-reinstall
```

### 실행 권한 오류
```bash
chmod +x NeuroFlow_Launcher.command
```

### 웹 뷰어가 열리지 않는 경우
- 수동으로 열기: `analysis_results/[환자명]/viewer/viewer.html`
- 브라우저에서 직접 열기

---

## 📖 참고 문헌

### PVT (Prolonged Venous Transit)
- **Amorim et al. (2023)**: "Prolonged Venous Transit on CT Perfusion Predicts Poor Outcomes in Acute Ischemic Stroke"
- **Threshold**: Tmax ≥ 10초 (기본값)
- **ROI**: SSS (Superior Sagittal Sinus), Torcula (Confluence of Sinuses)

### Perfusion Thresholds
- **Hypoperfusion**: Tmax > 6초
- **Core**: Tmax ≥ 10초 & CBV < 2.0 ml/100g
- **Penumbra**: Hypoperfusion - Core

---

## 📞 문의

문제가 있거나 질문이 있으시면 연락주세요!

**Version**: 2.0 (PVT 통합)  
**Last Updated**: 2025-11-06
