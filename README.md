# 🧠 NeuroFlow: CT Perfusion Auto-Analysis (Open Source)

**파이썬 기반 자동 CT Perfusion 분석 GUI 도구**

DICOM 폴더를 선택하면 자동으로 주요 perfusion 지표와 인터랙티브 웹 뷰어를 생성합니다.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green.svg)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac-lightgrey.svg)](https://github.com/JoonHaJang/ct-perfusion-auto)

---

## 🎯 주요 기능

### ✨ 핵심 특징
- 🚀 **원클릭 분석**: DICOM 폴더 선택 → 자동 분석 → 결과 확인
- 📊 **임상 지표 자동 계산**: Hypoperfusion, Core, Penumbra, Mismatch Ratio 등
- 🎨 **인터랙티브 웹 뷰어**: 모든 Perfusion 맵을 브라우저에서 확인
- 🔬 **검증된 정확도**: RGB → Scalar 변환 정확도 100% (MAE=0.0)
- 💻 **크로스 플랫폼**: Windows, Mac, Linux 지원

### 📈 계산 지표
| 지표 | 설명 | 임상적 의미 |
|------|------|-------------|
| **Hypoperfusion Volume** | Tmax >6s 영역 | 전체 허혈 영역 |
| **Infarct Core Volume** | CBF <38% (relative) | 이미 손상된 조직 (회복 불가) |
| **Penumbra Volume** | Hypoperfusion - Core | 구제 가능한 조직 (치료 목표) |
| **Mismatch Ratio** | Hypoperfusion / Core | 혈전 제거술 적응증 판단 |
| **Corrected CBV Index** | CBV(lesion) / CBV(contralateral) | 혈류 지연 보정 CBV 비율 |
| **Conventional CBV Index** | 병변 CBV / 대측 CBV | 전통적 CBV 비율 |

---

## 🚀 Quick Start

### 1. 설치

```bash
# 저장소 클론
git clone https://github.com/JoonHaJang/ct-perfusion-auto.git
cd ct-perfusion-auto

# 패키지 설치
pip install -r requirements.txt
```

⚠️ **필수 요구사항**: Python 3.8 이상

**requirements.txt**:
```txt
PyQt5>=5.15.0          # GUI 프레임워크
pydicom>=2.3.0         # DICOM 파일 읽기
numpy>=1.21.0,<2.0     # 수치 계산
Pillow>=9.0.0          # 이미지 변환
scipy>=1.7.0           # 윤곽선 검출
nibabel>=3.2.0         # NIfTI 파일 저장
```

### 2. 실행

#### **Windows 사용자**

```bash
python ct_perfusion_viewer_windows.py
```

#### **Mac 사용자**

```bash
python ct_perfusion_viewer_mac.py
```

#### **GUI 사용 방법**
1. 📁 "Select Folder" 버튼 클릭 → DICOM 폴더 선택
2. 🚀 "Start Analysis" 버튼 클릭 → 자동 분석 시작 (약 1-2분)
3. 📊 분석 결과 테이블에서 지표 확인
4. 🌐 "View Results" 버튼 클릭 → 웹 뷰어에서 Perfusion 맵 확인
5. 📈 "View Graph" 버튼 클릭 → TAC 그래프 확인 (있는 경우)

### 3. 출력 결과

**저장 위치**: `_internal/analysis_results/[환자명]/`

- **NIfTI 맵**: `cbf.nii.gz`, `cbv.nii.gz`, `mtt.nii.gz`, `tmax.nii.gz`
- **마스크**: `masks.npz` (hypoperfusion, core, penumbra)
- **메트릭**: `perfusion_metrics.json`
- **웹 뷰어**: `viewer/viewer.html` (인터랙티브 3D 뷰어)
- **TAC 그래프**: `tac_extracted/penumbra_original_*.png` (있는 경우)

---

## 📁 프로젝트 구조

### **핵심 파일**
```
ct-perfusion-auto/
│
├── ct_perfusion_viewer_windows.py      ← Windows GUI 프로그램 ⭐
├── ct_perfusion_viewer_mac.py          ← Mac GUI 프로그램 ⭐
├── requirements.txt                    ← Python 패키지 의존성
│
└── scripts/
    ├── extract_metrics_from_dicom.py   ← Perfusion 지표 계산
    ├── generate_dicom_viewer.py        ← HTML 웹 뷰어 생성
    ├── extract_tac_from_penumbra.py    ← TAC 추출
    └── [기타 분석 스크립트]
```

### **전체 구조**
```
ct-perfusion-auto/
│
├── ct_perfusion_viewer.py              # 메인 GUI 프로그램
├── requirements.txt                    # Python 패키지 의존성
├── README.md                           # 프로젝트 문서
│
├── scripts/                            # 핵심 스크립트
│   ├── extract_metrics_from_dicom.py   # 지표 계산
│   ├── generate_dicom_viewer.py        # 웹 뷰어 생성
│   └── [기타 유틸리티 스크립트]
│
├── accuracy_verification/              # 정확도 검증 결과
│   ├── accuracy_results.json           # MAE=0.0, RMSE=0.0
│   └── accuracy_slice_*.png            # 슬라이스별 비교 이미지
│
├── data_extraction/                    # 데이터 추출 비교
│   └── extraction_comparison_*.png     # RGB vs Scalar 비교
│
├── validation_results/                 # 전체 파이프라인 검증
│   ├── dicom_samples.png               # DICOM 샘플
│   └── reference_comparison.png        # 참조 데이터 비교
│
└── src/ctperf/                         # 재사용 가능한 라이브러리 (선택적)
    ├── io/loaders.py                   # DICOM 로더
    └── roi/mip_yellow_roi.py           # ROI 추출
```

---

## 📊 출력 결과

### **1. 지표 JSON 파일**
```json
{
  "metrics": {
    "hypoperfusion_volume_ml": 348.1,
    "infarct_core_volume_ml": 8.0,
    "penumbra_volume_ml": 340.1,
    "mismatch_ratio": 43.51,
    "corrected_cbv_index": 0.85,
    "conventional_cbv_index": 0.72
  },
  "tmax_metadata": {
    "max_value": 12.0,
    "slice_thickness_mm": 3.0,
    "pixel_spacing_mm": [0.5, 0.5]
  }
}
```

### **2. 마스크 파일 (NPZ)**
```python
masks.npz:
  - hypoperfusion: (33, 512, 512) boolean array
  - core: (33, 512, 512) boolean array
  - penumbra: (33, 512, 512) boolean array
```

### **3. 웹 뷰어 (HTML)**
```
viewer/
├── viewer.html                 # 메인 뷰어 (브라우저에서 열기)
└── [embedded base64 images]    # 모든 이미지 포함
```

**웹 뷰어 기능:**
- 📊 **모든 Perfusion 맵 표시**: CBFD, CBVD, MTTD, TMAXD, TTPM, PENUMBRA
- 🎨 **오버레이 토글**: Tmax >6s, Core, Penumbra 마스크 ON/OFF
- 🖱️ **인터랙티브 탐색**: 마우스 휠로 슬라이스 이동
- 📸 **썸네일 네비게이션**: 빠른 슬라이스 선택
- 📈 **지표 요약**: 상단에 핵심 지표 표시

![Web Viewer Screenshot](docs/images/web_viewer_screenshot.png)

---

## 🔬 검증 및 정확도

### **1. RGB → Scalar 변환 정확도**

**검증 방법:** `scripts/verify_accuracy.py`

```bash
python scripts/verify_accuracy.py \
    --dicom_dir "path/to/patient" \
    --output_dir "accuracy_verification"
```

**결과:**
```json
{
  "mae": 0.0,                    ← 평균 절대 오차: 0
  "rmse": 0.0,                   ← 제곱근 평균 제곱 오차: 0
  "max_diff": 0.0,               ← 최대 오차: 0
  "correlation": 0.9999999999,   ← 상관계수: 1.0
  "status": "PERFECT"            ← 완벽한 변환!
}
```

**해석:** RGB 이미지에서 원본 스칼라 값을 **100% 정확하게 복원**합니다.

---

### **2. 데이터 추출 비교**

**검증 방법:** `scripts/extract_real_data.py`

```bash
python scripts/extract_real_data.py \
    --dicom_dir "path/to/patient" \
    --output_dir "data_extraction"
```

**비교 내용:**
- ✅ **방법 1**: 가중 평균 (0.299R + 0.587G + 0.114B) - **채택**
- 📊 **방법 2**: Jet colormap 역변환 (R - B)
- 📊 **방법 3**: HSV Hue 기반 변환

**결과:** 방법 1이 가장 정확하며, 논문 기준과 일치합니다.

---

### **3. 전체 파이프라인 검증**

**검증 방법:** `scripts/validate_visualization.py`

```bash
python scripts/validate_visualization.py \
    --dicom_dir "path/to/patient" \
    --output_dir "validation_results"
```

**검증 항목:**
- ✅ DICOM 로딩
- ✅ RGB → Scalar 변환
- ✅ 지표 계산
- ✅ 마스크 생성
- ✅ 웹 뷰어 생성

---

## 🧪 추가 검증 도구

### **마스크 확인**
```bash
python check_masks.py
```
- Hypoperfusion, Core, Penumbra 마스크 확인
- 볼륨 계산 검증

### **오버레이 확인**
```bash
python check_overlays.py
```
- 웹 뷰어의 오버레이 데이터 확인
- 각 시리즈별 오버레이 존재 여부

### **슬라이스 간격 확인**
```bash
python check_slice_spacing.py
```
- 슬라이스 간격 (보통 3mm) 확인
- Z 위치 정렬 검증

---

## 📖 사용 예시

### **예시 1: 단일 환자 분석**

```bash
# GUI 실행
python ct_perfusion_viewer.py

# 1. "폴더 선택" 버튼 클릭
# 2. DICOM 폴더 선택: C:\Data\Patient_001
# 3. "분석 시작" 버튼 클릭
# 4. 결과 확인 (약 2-3분 소요)
# 5. "웹 뷰어 열기" 버튼 클릭
```

---

### **예시 2: 배치 처리**

```python
import subprocess
from pathlib import Path

patients = [
    "C:/Data/Patient_001",
    "C:/Data/Patient_002",
    "C:/Data/Patient_003"
]

for patient_dir in patients:
    output_dir = f"results/{Path(patient_dir).name}"
    
    # 지표 계산
    subprocess.run([
        "python", "scripts/extract_metrics_from_dicom.py",
        "--dicom_dir", patient_dir,
        "--output_dir", output_dir,
        "--patient_name", Path(patient_dir).name
    ])
    
    # 웹 뷰어 생성
    subprocess.run([
        "python", "scripts/generate_dicom_viewer.py",
        "--dicom_dir", patient_dir,
        "--metrics", f"{output_dir}/perfusion_metrics.json",
        "--output_dir", f"{output_dir}/viewer"
    ])
```

---

## 🧠 임상적 의미

### **Penumbra (반음영) 이해**

```
┌─────────────────────────────────────┐
│  뇌졸중 발생 시 조직 상태           │
├─────────────────────────────────────┤
│                                     │
│  ⬛ Core (경색 핵심)                │
│     - 이미 죽은 조직                │
│     - 회복 불가능                   │
│     - CBF < 38% (relative)         │
│                                     │
│  🔵 Penumbra (반음영)              │
│     - 손상 위험이 있지만            │
│     - 아직 살아있는 조직            │
│     - 치료로 구제 가능!             │
│     - Tmax >6s & CBF ≥38%          │
│                                     │
│  ⚫ Tmax >6s (전체 허혈)            │
│     - Core + Penumbra              │
│     - 혈류 지연 영역                │
│                                     │
└─────────────────────────────────────┘
```

### **Mismatch Ratio**

```
Mismatch Ratio = Hypoperfusion / Core

> 1.8: 혈전 제거술 적응증 (DEFUSE3, DAWN 기준)
> 2.6: 높은 구제 가능성
< 1.2: 구제 가능한 조직 적음
```

### **CBV Index (Corrected)**

```
CBV Index = CBV(Tmax >6s 영역) / CBV(대측 정상)

> 0.7: 양호한 측부 순환
< 0.4: 불량한 측부 순환 (예후 불량)
```

---

## 🔧 고급 사용법

### **1. 커스텀 임계값 설정**

`scripts/extract_metrics_from_dicom.py` 수정:

```python
# Line 170-174
TMAX_THRESHOLD_HYPOPERFUSION = 6.0   # 기본: 6초
TMAX_THRESHOLD_CORE = 10.0           # 기본: 10초
CBF_THRESHOLD_RELATIVE = 0.38        # 기본: 38%
CBV_THRESHOLD_CORE = 2.0             # 기본: 2.0 ml/100g
```

---

### **2. 오버레이 색상 변경**

`scripts/generate_dicom_viewer.py` 수정:

```python
# Line 61-72
if color == 'green':
    fill_color = [0, 255, 0, int(255 * alpha)]      # 녹색
elif color == 'red':
    fill_color = [0, 0, 0, int(255 * alpha)]        # 검은색 (Core)
elif color == 'yellow':
    fill_color = [0, 255, 255, int(255 * alpha)]    # 시안 (Penumbra)
```

---

### **3. Mac/Linux 호환성**

현재 코드는 Windows 인코딩(`cp949`)을 사용합니다. Mac/Linux에서 실행 시:

```python
# ct_perfusion_viewer.py Line 66, 98 수정
import platform

encoding = 'cp949' if platform.system() == 'Windows' else 'utf-8'
proc = subprocess.run(cmd, capture_output=True, text=True, 
                     encoding=encoding, errors='ignore')
```

---

## 🐛 문제 해결

### **문제 1: "지표 추출 실패"**

**원인:** DICOM 파일 형식 불일치

**해결:**
```bash
# DICOM 파일 확인
python scripts/inspect_dicom.py --dicom_dir "path/to/dicom"

# 시리즈 설명 확인
# 예상: TMAXD, CBVD, CBFD 등
```

---

### **문제 2: "웹 뷰어 생성 실패"**

**원인:** 마스크 파일 누락

**해결:**
```bash
# 마스크 파일 확인
ls analysis_results/masks.npz

# 없으면 다시 분석
python scripts/extract_metrics_from_dicom.py \
    --dicom_dir "path/to/dicom" \
    --output_dir "analysis_results"
```

---

### **문제 3: "오버레이가 보이지 않음"**

**원인:** 브라우저 캐시

**해결:**
```bash
# 1. 브라우저 캐시 삭제 (Ctrl+Shift+Delete)
# 2. viewer 폴더 삭제 후 재생성
rm -rf analysis_results/viewer
python scripts/generate_dicom_viewer.py ...
```

---

## 📚 참고 문헌

### **논문 기준**
- **DEFUSE3**: Albers et al., NEJM 2018 - Tmax >6s, Mismatch Ratio
- **DAWN**: Nogueira et al., NEJM 2018 - Core volume, Clinical mismatch
- **CRISP**: Campbell et al., Lancet Neurology 2019 - CBV Index

### **기술 참고**
- **RGB → Scalar 변환**: [neurolabusc/rgb2scalar](https://github.com/neurolabusc/rgb2scalar)
- **DICOM 처리**: [pydicom documentation](https://pydicom.github.io/)
- **Siemens CT Perfusion**: syngo.CT Neuro Perfusion

---

## 🤝 기여

이 프로젝트는 임상 연구용으로 개발되었습니다. 버그 리포트, 기능 제안, Pull Request를 환영합니다!

### **개발 환경 설정**
```bash
git clone https://github.com/yourusername/ct-perfusion-auto.git
cd ct-perfusion-auto
pip install -r requirements.txt
python ct_perfusion_viewer.py
```

---

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

---

## 👨‍⚕️ 저자 및 연락처

**개발자:** HyukJang1, JoonHaJang  
**소속:** Korean tertiary center  
**이메일:** parkoct@catholic.ac.kr

## 🖥️ GUI Applications

### 소스코드 기반 실행 (권장)

#### Windows:
```bash
git clone https://github.com/JoonHaJang/ct-perfusion-auto.git
cd ct-perfusion-auto
pip install -r requirements.txt
python ct_perfusion_viewer_windows.py
```

#### Mac:
```bash
git clone https://github.com/JoonHaJang/ct-perfusion-auto.git
cd ct-perfusion-auto
pip install -r requirements.txt
python ct_perfusion_viewer_mac.py
```

⚠️ **중요**: PC환경에 Python 3.8 이상이 설치되어 있어야 합니다

---

## 🙏 감사의 말

- 신경외과 의사분들의 임상 피드백
- DICOM 표준 및 오픈소스 커뮤니티
- PyQt5, pydicom, numpy 개발자들

---

## 📊 통계

- **코드 라인 수**: ~3,000 lines
- **지원 DICOM 시리즈**: 6개 (CBFD, CBVD, MTTD, TMAXD, TTPM, PENUMBRA)
- **계산 지표**: 6개 (Hypoperfusion, Core, Penumbra, Mismatch Ratio, CBV Index 등)
- **검증 정확도**: 100% (MAE=0.0, RMSE=0.0)

---

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요!**
