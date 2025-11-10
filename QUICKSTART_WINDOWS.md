# NeuroFlow Windows 빠른 시작 가이드

## 🚀 5분 안에 시작하기

### 1️⃣ 실행 파일 빌드 (처음 한 번만)

```cmd
# 1. 명령 프롬프트 열기 (관리자 권한 권장)
# 2. 프로젝트 폴더로 이동
cd "C:\Users\USER\Desktop\의료 저널\Neuroflow_mac"

# 3. 빌드 스크립트 실행
build_windows.bat
```

**빌드 시간**: 약 5-10분

### 2️⃣ 실행 파일 테스트

```cmd
# dist 폴더로 이동
cd dist\NeuroFlow

# 실행
NeuroFlow.exe
```

### 3️⃣ 분석 실행

1. **📁 Select Folder** 클릭
2. CT Perfusion DICOM 폴더 선택
3. **🚀 Start Analysis** 클릭
4. 30초 대기
5. **🌐 View Results** 클릭

## 📦 배포용 패키지 생성

### PowerShell에서 실행:
```powershell
# 압축 파일 생성
Compress-Archive -Path "dist\NeuroFlow" -DestinationPath "NeuroFlow-Windows-v1.0.zip"
```

### 배포 체크리스트:
- [ ] `dist\NeuroFlow` 폴더 전체 포함
- [ ] `README_WINDOWS.md` 추가
- [ ] `LICENSE.txt` 추가
- [ ] 테스트 완료

## 🔧 문제 해결 (빠른 참조)

### 빌드 실패
```cmd
# 의존성 재설치
pip install --upgrade -r requirements_windows.txt

# 캐시 정리 후 재빌드
rmdir /s /q build dist
build_windows.bat
```

### 실행 실패
```cmd
# 콘솔 모드로 실행하여 오류 확인
cd dist\NeuroFlow
cmd /k NeuroFlow.exe
```

### 분석 실패
- Siemens CT Perfusion DICOM 폴더인지 확인
- Tmax, CBV, CBF 맵이 모두 포함되어 있는지 확인

## 📁 파일 구조

```
Neuroflow_mac/
├── ct_perfusion_viewer_windows.py  # Windows 버전 메인 파일
├── NeuroFlow_Windows.spec          # PyInstaller 설정
├── requirements_windows.txt        # Windows 의존성
├── build_windows.bat               # 빌드 스크립트
├── BUILD_WINDOWS.md                # 상세 빌드 가이드
├── README_WINDOWS.md               # 사용자 가이드
├── scripts/                        # 분석 스크립트
└── pvt_masks/                      # PVT 마스크
```

## 🎯 다음 단계

### 개발자
- `BUILD_WINDOWS.md` 읽기
- 코드 커스터마이징
- 기능 추가

### 배포자
- 압축 파일 생성
- 문서 포함
- 테스트 환경 구축

### 사용자
- `README_WINDOWS.md` 읽기
- 샘플 데이터로 테스트
- 임상 활용

## 💡 팁

### 빌드 속도 향상
- SSD 사용
- 백신 일시 비활성화
- 불필요한 프로그램 종료

### 파일 크기 감소
- UPX 압축 활성화 (이미 적용됨)
- 불필요한 라이브러리 제외

### 배포 최적화
- 7-Zip으로 압축 (더 작은 파일)
- 설치 프로그램 생성 (Inno Setup)

## 📞 지원

- **문서**: `BUILD_WINDOWS.md`, `README_WINDOWS.md`
- **이슈**: GitHub Issues
- **이메일**: [your-email]

---

**준비 완료!** 🎉 이제 NeuroFlow를 Windows에서 사용할 수 있습니다.
