# NeuroFlow - CT Perfusion Analysis Suite (Windows)

## 소개
NeuroFlow는 급성 뇌졸중 환자의 CT Perfusion 데이터를 자동으로 분석하여 혈전제거술 적응증을 평가하는 의사결정 지원 도구입니다.

## 주요 기능

### 🚀 원클릭 자동 분석
- DICOM 폴더 선택만으로 자동 분석
- Siemens CT Perfusion RGB 데이터 자동 변환
- 8초 이내 정량 메트릭 추출

### 📊 임상 검증된 메트릭
- **Infarct Core Volume** (Tmax ≥10s & CBV <2.0)
- **Penumbra Volume** (Tmax ≥6s & CBV ≥2.0)
- **Mismatch Ratio** (혈전제거술 적응증 평가)
- **Corrected CBV Index** (측부순환 평가, AUC 0.83)
- **PVT (Prolonged Venous Transit)** (정맥 배출 지연)

### 🌐 인터랙티브 웹 뷰어
- 3D 뇌 렌더링 (Three.js)
- 슬라이스별 Tmax/CBV 오버레이
- Core/Penumbra 시각화
- 브라우저 기반 (별도 설치 불필요)

### 🏥 임상 활용
- 응급실 의사결정 지원
- 기관별 치료 가이드라인 수립
- 다기관 연구 데이터 표준화

## 시스템 요구사항

### 최소 사양
- **OS**: Windows 10 이상 (64-bit)
- **RAM**: 8GB
- **저장공간**: 2GB 여유 공간
- **화면**: 1920x1080 이상 권장

### 권장 사양
- **OS**: Windows 11
- **RAM**: 16GB 이상
- **CPU**: Intel i5 이상 또는 동급
- **저장공간**: SSD 권장

## 설치 방법

### 방법 1: 실행 파일 (권장)
1. `NeuroFlow-Windows.zip` 다운로드
2. 압축 해제
3. `NeuroFlow.exe` 실행

### 방법 2: Python 소스 코드
```cmd
# 1. 저장소 클론
git clone https://github.com/yourusername/neuroflow.git
cd neuroflow

# 2. 의존성 설치
pip install -r requirements_windows.txt

# 3. 실행
python ct_perfusion_viewer_windows.py
```

## 사용 방법

### 1단계: 폴더 선택
1. **"📁 Select Folder"** 버튼 클릭
2. 환자의 DICOM 폴더 선택
   - Siemens CT Perfusion 데이터 필요
   - Tmax, CBV, CBF 맵 포함 필수

### 2단계: PVT Threshold 설정 (선택사항)
- 기본값: 10.0초
- 범위: 5.0 ~ 15.0초
- 정맥 배출 지연 판단 기준

### 3단계: 분석 시작
1. **"🚀 Start Analysis"** 버튼 클릭
2. 진행 상황 실시간 표시
3. 약 30초 ~ 1분 소요

### 4단계: 결과 확인

#### 메트릭 테이블
- Hypoperfusion Volume (Tmax ≥6s)
- Infarct Core Volume
- Penumbra Volume
- Mismatch Ratio
- Corrected CBV Index
- PVT Status

#### 웹 뷰어
1. **"🌐 View Results"** 버튼 클릭
2. 브라우저에서 3D 뷰어 자동 열림
3. 슬라이스 탐색 및 오버레이 확인

#### 결과 폴더
1. **"📂 Result Folder"** 버튼 클릭
2. 분석 결과 파일 확인:
   - `perfusion_metrics.json`: 정량 메트릭
   - `nifti/`: NIfTI 파일 (Tmax, CBV, CBF)
   - `viewer/`: 웹 뷰어 HTML
   - `pvt_result.json`: PVT 분석 결과

## 임상 해석 가이드

### Mismatch Ratio
- **≥1.8**: 혈전제거술 적응증 ✅
- **<1.8**: 약물치료 고려 ⚠️

### Corrected CBV Index
- **≥0.42**: Good collateral (측부순환 양호)
- **<0.42**: Poor collateral (측부순환 불량)

### PVT (Prolonged Venous Transit)
- **PVT+**: 정맥 배출 지연 (예후 불량 가능성)
- **PVT-**: 정상 정맥 배출

### Core Volume
- **<70ml**: 혈전제거술 고려 가능
- **≥70ml**: 대량 경색 (신중한 판단 필요)

## 문제 해결

### 실행 오류

**문제**: "이 앱을 실행할 수 없습니다"
- **원인**: Windows Defender SmartScreen
- **해결**: "추가 정보" → "실행" 클릭

**문제**: 실행 시 바로 종료
- **원인**: 필수 파일 누락
- **해결**: 전체 폴더 압축 해제 확인

### 분석 오류

**문제**: "DICOM 파일을 찾을 수 없습니다"
- **원인**: 잘못된 폴더 선택
- **해결**: Siemens CT Perfusion DICOM 폴더 선택

**문제**: "RGB 변환 실패"
- **원인**: 지원하지 않는 DICOM 형식
- **해결**: Siemens CT Perfusion 데이터 확인

**문제**: "메트릭 추출 실패"
- **원인**: 불완전한 데이터
- **해결**: Tmax, CBV, CBF 맵 모두 포함 확인

### 웹 뷰어 오류

**문제**: 웹 뷰어가 열리지 않음
- **원인**: 브라우저 설정
- **해결**: 
  1. 결과 폴더 열기
  2. `viewer/viewer.html` 수동으로 열기

**문제**: 3D 렌더링 안 됨
- **원인**: WebGL 미지원
- **해결**: 최신 브라우저 사용 (Chrome, Edge 권장)

## 데이터 보안

### 개인정보 보호
- 모든 분석은 **로컬에서만** 수행
- 인터넷 연결 불필요
- 데이터 외부 전송 없음

### DICOM 익명화 권장
- 배포 전 환자 정보 제거
- DICOM 태그 익명화 도구 사용

## 성능 최적화

### 분석 속도 향상
- SSD 사용
- 백그라운드 프로그램 최소화
- 충분한 RAM 확보

### 대용량 데이터
- 환자당 약 100-200MB DICOM
- 결과 파일 약 50-100MB
- 정기적인 결과 폴더 정리 권장

## 업데이트

### 자동 업데이트 확인
- 현재 버전: v1.0.0
- GitHub Releases 확인

### 수동 업데이트
1. 새 버전 다운로드
2. 기존 폴더 백업
3. 새 파일로 교체

## 라이선스
MIT License - 무료 사용 가능 (상업적 사용 포함)

## 인용

### 논문 인용
```
[JNIS 2025 논문 정보 추가 예정]
```

### 소프트웨어 인용
```
NeuroFlow: CT Perfusion Analysis Suite
Version 1.0.0
https://github.com/yourusername/neuroflow
```

## 지원 및 문의

### 기술 지원
- GitHub Issues: [링크]
- 이메일: [your-email]

### 임상 문의
- 연구 협력 문의 환영
- 다기관 검증 연구 참여 가능

## 면책 조항

⚠️ **중요**: NeuroFlow는 의사결정 **지원** 도구입니다.
- 최종 임상 판단은 의사의 책임
- FDA/MFDS 승인 의료기기 아님
- 연구 및 교육 목적으로 사용

## 감사의 말

### 개발
- [개발팀 정보]

### 임상 검증
- [병원/기관 정보]

### 오픈소스 라이브러리
- PyQt5, pydicom, nibabel, numpy, scipy, Pillow

---

**NeuroFlow** - Making stroke treatment decisions transparent and data-driven
