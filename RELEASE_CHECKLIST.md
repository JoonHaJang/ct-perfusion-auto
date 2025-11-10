# NeuroFlow 배포 체크리스트

## 📦 배포 전 준비

### 1. 코드 및 빌드 확인
- [x] 모든 기능 정상 작동 확인
- [x] Python subprocess 경로 문제 해결
- [x] TAC 추출 기능 작동 확인
- [x] 웹 뷰어 생성 확인
- [ ] 다른 PC에서 테스트 (가능하면)

### 2. 문서 확인
- [x] README.txt 작성
- [x] INSTALLATION_GUIDE.txt 작성
- [ ] 연락처 정보 업데이트
- [ ] 버전 번호 확인

### 3. 파일 구조 확인
```
dist_new/NeuroFlow_App/
├── NeuroFlow_App.exe          ✅
├── README.txt                 ✅
├── INSTALLATION_GUIDE.txt     ✅
└── _internal/
    ├── scripts/               ✅ (15개 파일)
    ├── pvt_masks/             ✅
    └── PyQt5/                 ✅
```

## 🗜️ 압축 파일 생성

### Windows 압축
```powershell
# PowerShell에서 실행
Compress-Archive -Path "dist_new\NeuroFlow_App" -DestinationPath "NeuroFlow_Windows_v1.0.zip" -Force
```

### 압축 파일 확인
- [ ] 파일 크기: ~200-300MB
- [ ] 파일명: NeuroFlow_Windows_v1.0.zip
- [ ] 압축 해제 테스트
- [ ] 압축 해제 후 실행 테스트

## ☁️ Google Drive 업로드

### 폴더 구조 생성
```
Google Drive/
└── NeuroFlow/
    ├── Releases/
    │   └── Windows/
    │       └── v1.0/
    │           ├── NeuroFlow_Windows_v1.0.zip
    │           └── CHANGELOG.txt
    └── Documentation/
        ├── User_Manual.pdf (선택)
        └── Quick_Start.pdf (선택)
```

### 업로드 단계
1. [ ] Google Drive 접속
2. [ ] "NeuroFlow" 폴더 생성
3. [ ] 압축 파일 업로드
4. [ ] 업로드 완료 확인

### 공유 설정
1. [ ] 폴더 우클릭 → "공유"
2. [ ] 공유 방식 선택:
   - [ ] 특정 사용자 (이메일 입력)
   - [ ] 링크 공유 (Anyone with the link)
3. [ ] 권한: "Viewer" 설정
4. [ ] 다운로드 허용 확인
5. [ ] 공유 링크 복사

## 📧 사용자 안내

### 이메일 발송
- [ ] 수신자 목록 확인
- [ ] 다운로드 링크 포함
- [ ] 설치 가이드 첨부 또는 링크
- [ ] Python 설치 필수 안내
- [ ] 연락처 정보 포함

### 이메일 템플릿 사용
```
제목: NeuroFlow CT Perfusion Analysis Tool 배포

안녕하세요,

NeuroFlow CT Perfusion Analysis Tool을 배포합니다.

📥 다운로드: [Google Drive Link]
📖 설치 가이드: 압축 파일 내 INSTALLATION_GUIDE.txt 참조

⚠️ 필수 요구사항:
- Python 3.8 이상 설치 (https://python.org)
- 설치 시 "Add Python to PATH" 체크 필수

문의: [이메일/전화]

감사합니다.
```

## 🧪 배포 후 확인

### 다운로드 테스트
1. [ ] 다른 브라우저에서 링크 접속
2. [ ] 다운로드 속도 확인
3. [ ] 파일 무결성 확인

### 설치 테스트 (가능하면 다른 PC)
1. [ ] Python 미설치 상태에서 테스트
2. [ ] Python 설치 후 실행 테스트
3. [ ] 샘플 데이터로 분석 테스트
4. [ ] 모든 기능 작동 확인

### 사용자 피드백
- [ ] 설치 과정 피드백 수집
- [ ] 오류 보고 시스템 준비
- [ ] FAQ 문서 준비

## 📊 버전 관리

### CHANGELOG.txt 작성
```
NeuroFlow Changelog

v1.0 (2024-11-10)
=================
- Initial release
- Siemens CT Perfusion analysis
- Automatic segmentation (Core/Penumbra)
- Corrected CBV Index calculation
- Conventional CBV Index
- Mismatch Ratio
- HIR (Hypoperfusion Intensity Ratio)
- PRR (Penumbra Rescue Ratio)
- TAC extraction from Penumbra images
- Interactive 3D web viewer
- Export to JSON/NIfTI

Known Issues:
- Requires Python installation
- Large datasets (>500 slices) may be slow

Future Plans:
- Standalone version (no Python required)
- Mac version
- Multi-vendor support (GE, Philips)
```

## 🔐 보안 및 라이선스

### 데이터 프라이버시
- [x] 모든 처리는 로컬에서 수행
- [x] 외부 서버 전송 없음
- [ ] 사용자에게 안내

### 라이선스 (선택)
- [ ] MIT License 추가
- [ ] 면책 조항 추가
- [ ] 인용 요청 안내

## 📈 모니터링

### 배포 후 추적
- [ ] 다운로드 횟수 기록
- [ ] 사용자 피드백 수집
- [ ] 버그 리포트 관리
- [ ] 업데이트 계획 수립

## ✅ 최종 확인

배포 준비 완료 체크:
- [ ] 모든 파일 포함 확인
- [ ] 문서 완성도 확인
- [ ] 테스트 완료
- [ ] Google Drive 업로드 완료
- [ ] 공유 링크 생성 완료
- [ ] 사용자 안내 준비 완료

배포 승인: _____________ (날짜: _________)
