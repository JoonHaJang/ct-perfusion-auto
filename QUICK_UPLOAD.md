# 🚀 빠른 GitHub 업로드 가이드

## ✅ 준비 완료!

`.gitignore`에 이미 다음이 설정되어 있습니다:
- `Research/` - 환자 데이터 폴더 (자동 제외)
- `analysis_results/` - 분석 결과 (자동 제외)
- `*.dcm` - DICOM 파일 (자동 제외)
- `build_new/`, `dist_new/` - 빌드 파일 (자동 제외)
- `*.zip` - 압축 파일 (자동 제외)

## 📦 업로드할 파일 (자동 선택됨)

### 메인 파일
- `ct_perfusion_viewer_windows.py` ⭐
- `ct_perfusion_viewer.py` ⭐
- `requirements.txt` ⭐
- `README.md` ⭐
- `LICENSE` ⭐
- `.gitignore` ⭐

### 폴더
- `scripts/` - 모든 분석 스크립트
- `pvt_masks/` - 마스크 템플릿

## 🎯 업로드 명령어 (3단계)

### 1단계: Git 초기화 (처음 한 번만)
```bash
cd "C:\Users\USER\Desktop\의료 저널\Neuroflow_mac"

git init
git remote add origin https://github.com/HyukJang1/ct-perfusion-auto.git
git branch -M main
```

### 2단계: 파일 추가 및 커밋
```bash
# 모든 파일 추가 (.gitignore가 자동으로 Research/ 제외)
git add .

# 상태 확인 (Research/가 제외되었는지 확인)
git status

# 커밋
git commit -m "Initial release: NeuroFlow v1.0

- Windows/Mac GUI application
- Automatic CT Perfusion analysis
- Corrected CBV Index calculation
- TAC extraction from Penumbra images
- Interactive web viewer
- Validated accuracy (MAE=0.0)"
```

### 3단계: GitHub에 푸시
```bash
git push -u origin main
```

## ✅ 완료!

이제 https://github.com/HyukJang1/ct-perfusion-auto 에서 확인하세요!

## 📝 다음 단계: Release 생성

1. GitHub 웹사이트 접속
2. "Releases" → "Create a new release"
3. Tag: `v1.0.0`
4. Title: `NeuroFlow v1.0 - Initial Release`
5. Description 작성
6. "Publish release" 클릭

끝!
