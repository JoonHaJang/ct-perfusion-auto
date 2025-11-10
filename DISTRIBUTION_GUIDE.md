# NeuroFlow 배포 가이드

## 1. 배포 패키지 준비

### Windows 버전
```
📦 NeuroFlow_Windows_v1.0.zip
└── NeuroFlow_App/
    ├── NeuroFlow_App.exe
    ├── README.txt
    ├── INSTALLATION_GUIDE.pdf (선택사항)
    └── _internal/ (137개 파일)
```

### 압축 방법
1. `dist_new/NeuroFlow_App` 폴더 전체를 선택
2. 마우스 우클릭 → "압축" 또는 "Send to → Compressed folder"
3. 파일명: `NeuroFlow_Windows_v1.0.zip`

## 2. Google Drive 업로드

### 폴더 구조
```
Google Drive/
└── NeuroFlow/
    ├── Windows/
    │   └── NeuroFlow_Windows_v1.0.zip
    ├── Mac/
    │   └── NeuroFlow_Mac_v1.0.zip (향후)
    └── Documentation/
        ├── User_Manual.pdf
        └── Quick_Start_Guide.pdf
```

### 공유 설정
1. **제한된 공유** (추천):
   - 특정 이메일 주소만 접근 가능
   - "Viewer" 권한 부여
   - 다운로드 허용

2. **링크 공유**:
   - "Anyone with the link can view"
   - 링크를 아는 사람만 다운로드 가능

## 3. 사용자 안내 문서

### 이메일 템플릿
```
Subject: NeuroFlow CT Perfusion Analysis Tool - Download Link

안녕하세요,

NeuroFlow CT Perfusion Analysis Tool을 공유합니다.

📥 다운로드 링크: [Google Drive Link]

📋 시스템 요구사항:
- Windows 10/11 (64-bit)
- Python 3.8 이상 (필수!)
- 8GB RAM (16GB 권장)

🔧 설치 방법:
1. Python 설치: https://python.org/downloads
   ⚠️ 설치 시 "Add Python to PATH" 체크 필수!
2. zip 파일 다운로드 및 압축 해제
3. NeuroFlow_App.exe 실행

📖 사용 방법:
1. "Select Folder" → 환자 DICOM 폴더 선택
2. "Start Analysis" → 분석 시작
3. 결과 확인 및 "View Results" 클릭

문의사항이 있으시면 연락 주세요.

감사합니다.
```

## 4. 버전 관리

### 파일명 규칙
```
NeuroFlow_Windows_v1.0.zip      # 첫 릴리즈
NeuroFlow_Windows_v1.1.zip      # 버그 수정
NeuroFlow_Windows_v2.0.zip      # 주요 기능 추가
```

### 변경 이력 (CHANGELOG.txt)
```
v1.0 (2024-11-10)
- Initial release
- Siemens CT Perfusion analysis
- Corrected CBV Index calculation
- TAC extraction from Penumbra images
- Interactive 3D web viewer

v1.1 (TBD)
- Bug fixes
- Performance improvements
```

## 5. 배포 체크리스트

### 배포 전 확인사항
- [ ] 테스트 데이터로 정상 작동 확인
- [ ] README.txt 내용 확인
- [ ] Python 요구사항 명시
- [ ] 압축 파일 크기 확인 (예상: ~200MB)
- [ ] 압축 해제 후 실행 테스트
- [ ] 다른 PC에서 테스트 (가능하면)

### Google Drive 업로드 후
- [ ] 다운로드 링크 테스트
- [ ] 권한 설정 확인
- [ ] 파일 크기 및 이름 확인
- [ ] 사용자에게 안내 이메일 발송

## 6. 대안 배포 방법

### GitHub Releases (추천)
- 버전 관리 용이
- 자동 다운로드 통계
- 무료 (파일 크기 제한: 2GB)

### OneDrive / Dropbox
- Google Drive와 유사
- 기관 계정 사용 가능

### 기관 내부 서버
- 보안성 높음
- 접근 제어 용이

## 7. 라이선스 및 면책

### LICENSE.txt 추가 (선택사항)
```
MIT License

Copyright (c) 2024 NeuroFlow Development Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

[...]

DISCLAIMER: This software is provided for research and clinical decision 
support purposes only. It should not be used as the sole basis for clinical 
decisions. Always verify results with clinical judgment.
```

## 8. 사용자 피드백 수집

### 피드백 양식 (Google Forms)
- 설치 과정 난이도
- 분석 결과 정확도
- 사용 편의성
- 개선 요청사항
- 버그 리포트
