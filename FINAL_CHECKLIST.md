# 🚀 GitHub 업로드 최종 체크리스트

## ✅ 1단계: 파일 정리 (필수!)

```powershell
# PowerShell에서 실행
cd "C:\Users\USER\Desktop\의료 저널\Neuroflow_mac"

# 빌드 파일 삭제
Remove-Item -Path "build_new", "dist_new", "build", "dist" -Recurse -Force -ErrorAction SilentlyContinue

# 압축 파일 삭제
Remove-Item -Path "*.zip" -Force -ErrorAction SilentlyContinue

# 분석 결과 삭제 (환자 데이터!)
Remove-Item -Path "analysis_results" -Recurse -Force -ErrorAction SilentlyContinue

# 임시 파일 삭제
Remove-Item -Path "*.log", "*.tmp" -Force -ErrorAction SilentlyContinue
```

**확인:**
- [ ] build_new/ 폴더 삭제됨
- [ ] dist_new/ 폴더 삭제됨
- [ ] *.zip 파일 삭제됨
- [ ] analysis_results/ 폴더 삭제됨

---

## ✅ 2단계: 필수 파일 확인

### 메인 파일
- [ ] `ct_perfusion_viewer_windows.py` 존재
- [ ] `ct_perfusion_viewer.py` 존재
- [ ] `requirements.txt` 존재
- [ ] `README.md` 존재
- [ ] `LICENSE` 존재
- [ ] `.gitignore` 존재

### scripts/ 폴더
- [ ] `extract_metrics_from_dicom.py`
- [ ] `generate_dicom_viewer.py`
- [ ] `extract_tac_from_penumbra.py`
- [ ] `compute_metrics.py`
- [ ] `convert_dicom_to_nifti.py`

### pvt_masks/ 폴더
- [ ] `sss_mask_template.npy`
- [ ] `torcula_mask_template.npy`

---

## ✅ 3단계: 보안 확인 (매우 중요!)

### 환자 데이터 제거 확인
```powershell
# 다음 명령어로 환자 데이터가 없는지 확인
Get-ChildItem -Recurse -Include "*.dcm" | Measure-Object
# 결과: Count = 0 이어야 함!

Get-ChildItem -Path "analysis_results" -ErrorAction SilentlyContinue
# 결과: 폴더가 없어야 함!

Get-ChildItem -Path "Research" -ErrorAction SilentlyContinue
# 결과: 폴더가 없어야 함!
```

**확인:**
- [ ] *.dcm 파일 0개
- [ ] analysis_results/ 폴더 없음
- [ ] Research/ 폴더 없음
- [ ] CTP_MT/ 폴더 없음
- [ ] data/ 폴더 없음

### 개인정보 확인
- [ ] 이메일 주소 제거 또는 [your.email@example.com]으로 대체
- [ ] 전화번호 제거
- [ ] 내부 경로 제거 (C:\Users\USER\...)
- [ ] 환자 이름 제거

---

## ✅ 4단계: Git 업로드

### Git 초기화 (처음 한 번만)
```bash
git init
git remote add origin https://github.com/HyukJang1/ct-perfusion-auto.git
git branch -M main
```

### 파일 추가 및 커밋
```bash
# 모든 파일 추가
git add .

# 상태 확인 (환자 데이터가 포함되지 않았는지 확인!)
git status

# 커밋
git commit -m "Initial release: NeuroFlow v1.0"

# 푸시
git push -u origin main
```

**확인:**
- [ ] `git status`에서 환자 데이터 파일 없음
- [ ] 커밋 완료
- [ ] 푸시 완료

---

## ✅ 5단계: GitHub 확인

### 웹에서 확인
1. https://github.com/HyukJang1/ct-perfusion-auto 접속
2. 다음 확인:
   - [ ] README.md가 제대로 표시됨
   - [ ] 파일 목록이 정확함
   - [ ] 환자 데이터가 없음
   - [ ] .gitignore가 작동함

### 테스트 클론
```bash
# 다른 폴더에서 테스트
cd C:\Temp
git clone https://github.com/HyukJang1/ct-perfusion-auto.git
cd ct-perfusion-auto

# 패키지 설치
pip install -r requirements.txt

# 실행 테스트
python ct_perfusion_viewer_windows.py
```

**확인:**
- [ ] 클론 성공
- [ ] 패키지 설치 성공
- [ ] 프로그램 실행 성공

---

## ✅ 6단계: Release 생성

### GitHub Releases
1. Repository → Releases → "Create a new release"
2. Tag: `v1.0.0`
3. Title: `NeuroFlow v1.0 - Initial Release`
4. Description: (GIT_UPLOAD_GUIDE.md 참조)
5. "Publish release" 클릭

**확인:**
- [ ] Release 생성됨
- [ ] Tag v1.0.0 생성됨
- [ ] 다운로드 가능

---

## ✅ 7단계: 최종 확인

### 필수 체크
- [ ] 모든 환자 데이터 제거됨
- [ ] README.md 작성 완료
- [ ] LICENSE 파일 포함됨
- [ ] requirements.txt 정확함
- [ ] .gitignore 작동함
- [ ] GitHub에 푸시 완료
- [ ] Release 생성 완료

### 테스트
- [ ] 다른 PC에서 클론 테스트
- [ ] 패키지 설치 테스트
- [ ] 프로그램 실행 테스트

---

## 🎉 완료!

모든 체크리스트를 완료했다면 GitHub 업로드 성공입니다!

### 공유 링크
```
GitHub: https://github.com/HyukJang1/ct-perfusion-auto
Release: https://github.com/HyukJang1/ct-perfusion-auto/releases/tag/v1.0.0
```

### 사용자 안내
```
설치 방법:
1. Python 3.8+ 설치
2. git clone https://github.com/HyukJang1/ct-perfusion-auto.git
3. pip install -r requirements.txt
4. python ct_perfusion_viewer_windows.py
```
