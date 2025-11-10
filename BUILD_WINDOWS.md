# NeuroFlow Windows Build Guide

## 개요
이 가이드는 NeuroFlow를 Windows 실행 파일(.exe)로 빌드하는 방법을 설명합니다.

## 시스템 요구사항

### 필수 요구사항
- **운영체제**: Windows 10 이상 (64-bit)
- **Python**: 3.8 ~ 3.12 (64-bit)
- **메모리**: 최소 8GB RAM
- **저장공간**: 최소 2GB 여유 공간

### Python 설치
1. [Python 공식 웹사이트](https://www.python.org/downloads/)에서 Python 다운로드
2. 설치 시 **"Add Python to PATH"** 옵션 반드시 체크
3. 설치 확인:
   ```cmd
   python --version
   pip --version
   ```

## 빌드 방법

### 방법 1: 자동 빌드 (권장)

1. **빌드 스크립트 실행**
   ```cmd
   build_windows.bat
   ```

2. **빌드 과정**
   - 의존성 패키지 자동 설치
   - 이전 빌드 파일 정리
   - PyInstaller로 실행 파일 생성
   - 약 5-10분 소요

3. **결과물 위치**
   ```
   dist/NeuroFlow/NeuroFlow.exe
   ```

### 방법 2: 수동 빌드

1. **의존성 설치**
   ```cmd
   pip install -r requirements_windows.txt
   ```

2. **이전 빌드 정리**
   ```cmd
   rmdir /s /q build
   rmdir /s /q dist
   ```

3. **PyInstaller 실행**
   ```cmd
   pyinstaller NeuroFlow_Windows.spec
   ```

## 빌드 결과물 구조

```
dist/NeuroFlow/
├── NeuroFlow.exe          # 메인 실행 파일
├── scripts/               # 분석 스크립트
│   ├── extract_metrics_from_dicom.py
│   ├── calculate_pvt_tmax.py
│   ├── generate_dicom_viewer.py
│   └── ...
├── pvt_masks/            # PVT 마스크 템플릿
├── _internal/            # Python 런타임 및 라이브러리
└── analysis_results/     # 분석 결과 저장 폴더 (자동 생성)
```

## 배포 방법

### 단일 폴더 배포
전체 `dist/NeuroFlow` 폴더를 압축하여 배포:

```cmd
# PowerShell에서 실행
Compress-Archive -Path "dist\NeuroFlow" -DestinationPath "NeuroFlow-Windows-v1.0.zip"
```

### 설치 프로그램 생성 (선택사항)
Inno Setup 또는 NSIS를 사용하여 설치 프로그램 생성 가능

## 실행 방법

### 최종 사용자용
1. `NeuroFlow.exe` 더블클릭
2. 폴더 선택 → 분석 시작
3. 결과 확인

### 개발자용 테스트
```cmd
cd dist\NeuroFlow
NeuroFlow.exe
```

## 문제 해결

### 빌드 실패

**문제**: `pyinstaller: command not found`
- **해결**: `pip install pyinstaller`

**문제**: `ModuleNotFoundError`
- **해결**: `pip install -r requirements_windows.txt` 재실행

**문제**: 메모리 부족
- **해결**: 다른 프로그램 종료 후 재시도

### 실행 파일 문제

**문제**: 실행 시 바로 종료됨
- **해결**: 
  1. 명령 프롬프트에서 실행하여 오류 메시지 확인
  2. `NeuroFlow_Windows.spec`에서 `console=True`로 변경 후 재빌드

**문제**: "Windows에서 이 앱을 실행할 수 없습니다"
- **해결**: 
  1. 64-bit Python으로 빌드했는지 확인
  2. Windows Defender 예외 추가

**문제**: 분석 스크립트를 찾을 수 없음
- **해결**: `scripts` 폴더가 `NeuroFlow.exe`와 같은 위치에 있는지 확인

## 성능 최적화

### UPX 압축 (선택사항)
실행 파일 크기 감소:

1. [UPX 다운로드](https://upx.github.io/)
2. `NeuroFlow_Windows.spec`에서 `upx=True` 확인
3. 재빌드

### 빌드 시간 단축
- SSD 사용
- 백신 프로그램 일시 비활성화
- `--clean` 옵션 제거

## 버전 관리

### 버전 번호 업데이트
`ct_perfusion_viewer_windows.py`에서:
```python
self.setWindowTitle("🧠 NeuroFlow v1.0.0 - CT Perfusion Analysis Suite")
```

### 빌드 날짜 기록
```cmd
echo Build Date: %date% %time% > dist\NeuroFlow\BUILD_INFO.txt
```

## 라이선스 및 배포

### 포함할 파일
- `LICENSE.txt` (MIT License)
- `README_WINDOWS.md` (사용자 가이드)
- `CHANGELOG.md` (변경 이력)

### 배포 체크리스트
- [ ] 테스트 완료
- [ ] 버전 번호 업데이트
- [ ] 문서 포함
- [ ] 압축 파일 생성
- [ ] 바이러스 스캔 완료

## 참고사항

### 코드 서명 (선택사항)
Windows Defender SmartScreen 경고 방지:
1. 코드 서명 인증서 구매
2. SignTool로 서명
3. 배포

### 자동 업데이트 (선택사항)
- GitHub Releases 활용
- 버전 체크 기능 추가

## 지원

### 문제 보고
- GitHub Issues
- 이메일: [your-email]

### 개발 환경
- Python 3.11.x
- PyQt5 5.15.x
- PyInstaller 5.x
