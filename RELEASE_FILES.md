# GitHub Release 파일 목록

## ✅ 필수 파일 (반드시 포함)

### 1. 메인 프로그램
- `ct_perfusion_viewer_windows.py` - Windows용 GUI 프로그램 ⭐
- `ct_perfusion_viewer.py` - Mac용 GUI 프로그램

### 2. 스크립트 폴더 (scripts/)
- `extract_metrics_from_dicom.py` - 메트릭 추출 ⭐
- `generate_dicom_viewer.py` - 웹 뷰어 생성 ⭐
- `extract_tac_from_penumbra.py` - TAC 추출
- `compute_metrics.py` - 메트릭 계산
- `convert_dicom_to_nifti.py` - NIfTI 변환
- `generate_web_viewer_data.py` - 웹 데이터 생성

### 3. 마스크 폴더 (pvt_masks/)
- `sss_mask_template.npy` - SSS 마스크
- `torcula_mask_template.npy` - Torcula 마스크

### 4. 설정 파일
- `requirements.txt` - Python 패키지 의존성 ⭐
- `.gitignore` - Git 제외 파일 목록
- `README.md` - 프로젝트 설명 ⭐

### 5. 빌드 스크립트 (선택)
- `build_windows.bat` - Windows 빌드 스크립트
- `NeuroFlow.spec` - PyInstaller 설정 (있다면)

### 6. 문서
- `CHANGELOG.txt` - 버전 변경 이력
- `INSTALLATION_GUIDE.txt` - 설치 가이드 (dist_new에서 복사)
- `LICENSE` - 라이선스 파일 (MIT)

---

## ❌ 제외 파일 (GitHub에 올리지 않음)

### 데이터 폴더
- `analysis_results/` - 분석 결과 (환자 데이터)
- `Research/` - 연구 데이터
- `CTP_MT/` - 환자 데이터
- `data/` - 모든 데이터 폴더

### 빌드 결과물
- `build/` - 빌드 임시 파일
- `build_new/` - 빌드 임시 파일
- `dist/` - 배포 파일
- `dist_new/` - 배포 파일
- `*.zip` - 압축 파일

### 테스트 파일
- `test_*.py` - 테스트 스크립트
- `check_*.py` - 검증 스크립트
- `debug_*.py` - 디버그 스크립트
- `compare_*.py` - 비교 스크립트

### 임시 파일
- `__pycache__/` - Python 캐시
- `*.pyc` - 컴파일된 Python
- `*.log` - 로그 파일
- `.DS_Store` - macOS 파일

---

## 📦 최종 GitHub 구조

```
ct-perfusion-auto/
│
├── README.md                           ⭐ 프로젝트 설명
├── requirements.txt                    ⭐ 패키지 의존성
├── LICENSE                             ⭐ MIT 라이선스
├── .gitignore                          ⭐ Git 제외 목록
├── CHANGELOG.txt                       버전 이력
│
├── ct_perfusion_viewer_windows.py      ⭐ Windows GUI
├── ct_perfusion_viewer.py              ⭐ Mac GUI
│
├── scripts/                            ⭐ 분석 스크립트
│   ├── extract_metrics_from_dicom.py
│   ├── generate_dicom_viewer.py
│   ├── extract_tac_from_penumbra.py
│   ├── compute_metrics.py
│   ├── convert_dicom_to_nifti.py
│   └── generate_web_viewer_data.py
│
├── pvt_masks/                          ⭐ 마스크 템플릿
│   ├── sss_mask_template.npy
│   └── torcula_mask_template.npy
│
└── docs/                               (선택) 문서
    ├── INSTALLATION.md
    └── USAGE.md
```

---

## 🚀 사용자 설치 방법 (README에 명시)

```bash
# 1. 저장소 클론
git clone https://github.com/HyukJang1/ct-perfusion-auto.git
cd ct-perfusion-auto

# 2. Python 패키지 설치
pip install -r requirements.txt

# 3. 실행
python ct_perfusion_viewer_windows.py  # Windows
python ct_perfusion_viewer.py          # Mac
```

---

## 📝 체크리스트

업로드 전 확인:
- [ ] 모든 환자 데이터 제거 확인
- [ ] .gitignore 설정 확인
- [ ] requirements.txt 업데이트
- [ ] README.md 작성 완료
- [ ] LICENSE 파일 추가
- [ ] 빌드 결과물 제거
- [ ] 테스트 파일 제거
