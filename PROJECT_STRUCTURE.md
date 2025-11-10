# 🗂️ CT Perfusion 프로젝트 구조 분석

## ✅ 핵심 파일 (배포 필수)

### 1. 메인 실행 파일
```
ct_perfusion_viewer.py          # GUI 메인 프로그램

### 2. 핵심 스크립트 (scripts/)
```
scripts/
├── convert_dicom_to_nifti.py   # ✅ DICOM → NIfTI 변환
├── compute_metrics.py          # ✅ 관류 지표 계산
└── generate_web_viewer_data.py # ✅ 웹 뷰어 생성
```

### 3. 핵심 모듈 (src/ctperf/)
```
src/ctperf/
├── __init__.py
├── io/
│   ├── __init__.py
│   └── loaders.py              # ✅ NIfTI 로더
└── roi/
    ├── __init__.py
    └── mip_yellow_roi.py       # ⚠️ MIP 분석용 (선택)
```

### 4. 설정 파일
```
requirements.txt                # ✅ 패키지 의존성
setup.py                        # ✅ 패키지 설치 설정
```

---

## ❌ 불필요한 파일 (배포 제외)

### 개발/테스트 파일
```
RUN_ONESTOP_ANALYSIS.bat        # ❌ 커맨드라인 버전 (GUI로 대체)
ONESTOP_GUIDE.md                # ❌ 커맨드라인 가이드
```

### 사용하지 않는 스크립트
```
scripts/
├── analyze_mip_image.py        # ❌ MIP 이미지 분석 (사용 안 함)
├── one_shot_from_mip.py        # ❌ MIP 기반 파이프라인 (사용 안 함)
├── batch_process_patients.py  # ❌ 배치 처리 (GUI로 대체)
├── brain_3d_viewer.py          # ❌ 3D 뷰어 (웹 뷰어로 대체)
├── interactive_3d_viewer.py    # ❌ 인터랙티브 뷰어 (웹 뷰어로 대체)
└── perfusion_maps_viewer.py    # ❌ 관류 맵 뷰어 (웹 뷰어로 대체)
```

### 테스트/예시 데이터
```
test_output_gray/               # ❌ 테스트 출력
test_metrics_gray/              # ❌ 테스트 메트릭스
test_final/                     # ❌ 테스트 결과
analysis_results/               # ❌ 분석 결과 (사용자 생성)
patient_487460_*/               # ❌ 환자 데이터 (사용자 생성)
web_viewer_data/                # ❌ 웹 뷰어 데이터 (사용자 생성)
```

### 개발 문서
```
OUTPUT_EXAMPLES.md              # ❌ 출력 예시
QUICKSTART.md                   # ❌ 빠른 시작 (README로 통합)
VIEWER_GUIDE.md                 # ❌ 뷰어 가이드
```

### 생성된 파일
```
*.html                          # ❌ 생성된 HTML 뷰어
*.png                           # ❌ 생성된 이미지
*.nii / *.nii.gz               # ❌ 생성된 NIfTI (사용자 데이터)
```

---

## 🎯 최종 배포 구조 (실행파일용)

```
CTPerfusion_v1.0/
│
├── CTPerfusion.exe             # 실행파일 (PyInstaller로 생성)
│
├── README.txt                  # 간단한 사용 설명
│
└── [내부 번들]                  # PyInstaller가 자동 포함
    ├── ct_perfusion_viewer.py
    ├── scripts/
    │   ├── convert_dicom_to_nifti.py
    │   ├── compute_metrics.py
    │   └── generate_web_viewer_data.py
    ├── src/ctperf/
    └── [Python 런타임 + 라이브러리]
```

---

## 📦 배포 준비 작업

### 1. GUI 단순화
- ❌ 2D 슬라이스 탭 제거
- ❌ 3D 렌더링 탭 제거
- ✅ 결과 요약 + 웹 뷰어 열기만 유지

### 2. 의존성 정리
```python
# 필수 패키지만
numpy
nibabel
pydicom
matplotlib (최소한)
PyQt5
Pillow
pandas
scipy

# 제거 가능
nilearn      # ❌ 사용 안 함
plotly       # ❌ 사용 안 함
```

### 3. PyInstaller 설정
```python
# CTPerfusion.spec
a = Analysis(
    ['ct_perfusion_viewer.py'],
    pathex=['scripts', 'src'],
    datas=[
        ('scripts/*.py', 'scripts'),
        ('src/ctperf', 'ctperf')
    ],
    hiddenimports=['nibabel', 'pydicom', 'PyQt5'],
    ...
)
```

---

## 🚀 실행파일 생성 명령

```bash
# 1. PyInstaller 설치
pip install pyinstaller

# 2. 실행파일 생성 (단일 파일)
pyinstaller --onefile --windowed --name="CTPerfusion" ct_perfusion_viewer.py

# 3. 실행파일 생성 (폴더 형태, 권장)
pyinstaller --onedir --windowed --name="CTPerfusion" ct_perfusion_viewer.py
```

---

## 📊 파일 크기 예상

```
단일 파일 (.exe):     ~150-200 MB
폴더 형태 (dist/):    ~200-250 MB
압축 배포 (.zip):     ~80-100 MB
```

---

## ✅ 다음 단계

1. **GUI 단순화** (2D/3D 탭 제거)
2. **의존성 최소화** (requirements.txt 정리)
3. **PyInstaller 설정** (.spec 파일 작성)
4. **실행파일 생성 및 테스트**
5. **배포 패키지 준비** (README + exe)
