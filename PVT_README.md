# PVT (Prolonged Venous Transit) 계산 기능

## 📋 개요

NeuroFlow에 **PVT (Prolonged Venous Transit)** 계산 기능이 추가되었습니다.

PVT는 급성 허혈성 뇌졸중 환자의 **정맥 유출 지연**을 평가하는 바이오마커로, 예후 예측에 중요한 역할을 합니다.

---

## 🔬 방법론

### 학술 근거

**Amorim et al. (2023)**의 연구 방법론을 기반으로 구현:

```
Amorim, G., Yedavalli, N., Musmar, M., Dehkharghani, T. F., Liebeskind, M. G., 
Christensen, S., Albers, G. W., Faizy, J., & Heit, J. J. (2023). 
CT perfusion to measure venous outflow in acute ischemic stroke in patients 
with a large vessel occlusion. 
Journal of NeuroInterventional Surgery, 16(4), 343-348. 
https://doi.org/10.1136/jnis-2023-020613
```

### 계산 방법

```
PVT+ = (SSS Tmax ≥ 10s) OR (Torcula Tmax ≥ 10s)
```

**측정 위치**:
1. **SSS (Superior Sagittal Sinus)**: 상시상정맥동 (표재성 정맥 배출)
   - 위치: 측뇌실 후각(occipital horns) 레벨
   
2. **Torcula (Confluence of Sinuses)**: 정맥동 합류부 (심부 정맥 배출)
   - 위치: 뇌의 후방 중앙부

**판정 기준**:
- **Tmax ≥ 10초**: PVT+ (정맥 유출 지연)
- **Tmax < 10초**: PVT- (정상 정맥 유출)

---

## 📊 임상적 의의

### 예후 예측력

| PVT 상태 | Excellent Recovery (mRS 0-1) | 90일 Median mRS |
|---------|------------------------------|-----------------|
| PVT+    | 11%                          | 4 (중증 장애)    |
| PVT-    | 39%                          | 2 (경증 장애)    |

**Adjusted OR**: 0.11 (95% CI: 0.02-0.48, p=0.006)

### PVT+ 환자의 특징

- ✅ 더 높은 NIHSS 점수 (16 vs 14)
- ✅ 더 큰 mismatch volume (118mL vs 81mL)
- ✅ 더 긴 시술 시간 (35분 vs 25분)
- ⚠️ 더 나쁜 90일 예후

---

## 🎯 NeuroFlow 통합

### 자동 계산

분석 워크플로우에 자동으로 통합:

```
1. DICOM 분석
2. Tmax map 생성
3. PVT 자동 계산 ← NEW!
4. 웹 뷰어 생성
5. 결과 표시
```

### 결과 표시

**Metrics 테이블에 3개 항목 추가**:

1. **PVT Status**: PVT+ 또는 PVT-
   - 🔴 PVT+: 빨간색 배경 (위험)
   - 🟢 PVT-: 초록색 배경 (정상)

2. **SSS Tmax**: 상시상정맥동 Tmax 값 (초)

3. **Torcula Tmax**: 정맥동 합류부 Tmax 값 (초)

---

## 💻 사용 방법

### GUI에서 사용

1. **Select Folder** - DICOM 폴더 선택
2. **Start Analysis** - 분석 시작
3. 자동으로 PVT 계산됨
4. 결과 테이블에서 PVT 상태 확인

### 명령줄에서 단독 실행

```bash
# Tmax NIfTI 파일이 있는 경우
python scripts/calculate_pvt_tmax.py analysis_results/Tmax.nii.gz pvt_result.json

# 결과 확인
cat pvt_result.json
```

---

## 📁 출력 파일

### `pvt_result.json`

```json
{
  "pvt_status": "PVT-",
  "pvt_positive": false,
  "sss_tmax_mean": 8.45,
  "sss_tmax_max": 9.12,
  "sss_positive": false,
  "torcula_tmax_mean": 7.89,
  "torcula_tmax_max": 8.67,
  "torcula_positive": false,
  "threshold": 10.0,
  "interpretation": "정상 정맥 유출 (Normal venous outflow)",
  "clinical_significance": {
    "risk_level": "LOW",
    "prognosis": "양호한 예후 예상 (Favorable prognosis)",
    "recommendation": "표준 치료 프로토콜 적용",
    "evidence": "PVT- 환자는 excellent recovery 확률 39%"
  }
}
```

---

## 🔧 기술적 세부사항

### ROI 정의

**SSS (Superior Sagittal Sinus)**:
```python
# 뇌의 상부 정중선
z_start = int(depth * 0.75)  # 상위 25%
y_center = width // 2
y_range = ±8 pixels
```

**Torcula (Confluence of Sinuses)**:
```python
# 뇌의 후방 중앙부
x_posterior = int(height * 0.75)  # 후방 25%
y_center = width // 2
z_mid = int(depth * 0.6)
roi_size = 12 pixels (구형)
```

### 필터링

- Tmax > 6초인 영역만 고려 (정맥 영역)
- Brain mask와 교집합

---

## ⚠️ 제한사항 및 향후 개선

### 현재 제한사항

1. **ROI 자동 선택**: 휴리스틱 기반 (해부학적 위치 추정)
2. **한국인 데이터 검증 필요**: 논문은 서양인 데이터 기반
3. **Threshold 고정**: 10초 (조정 가능성 검토 필요)

### 향후 개선 계획

1. **Atlas 기반 ROI**: 해부학적 atlas로 정확한 SSS/Torcula 위치 파악
2. **Deep Learning**: 자동 정맥동 segmentation
3. **한국인 데이터 검증**: 최적 threshold 재검증
4. **시각화**: SSS/Torcula ROI 표시

---

## 📚 추가 참고 문헌

### 오픈 액세스 논문

1. **van der Schaaf et al. (2006)** - AIF/VOF 측정 방법론
   - https://www.ajnr.org/content/27/1/46
   - Gamma variate fitting, partial volume correction

2. **PMC Article** - Partial Volume Effects
   - https://pmc.ncbi.nlm.nih.gov/articles/PMC7976058/

---

## 🆘 문제 해결

### PVT 계산 실패

**증상**: "⚠️ PVT calculation failed"

**원인**:
1. Tmax.nii.gz 파일이 없음
2. NIfTI 파일 형식 오류
3. 메모리 부족

**해결**:
```bash
# Tmax 파일 확인
ls -lh analysis_results/Tmax.nii.gz

# 수동 실행으로 오류 확인
python scripts/calculate_pvt_tmax.py analysis_results/Tmax.nii.gz
```

### ROI가 비어있음

**증상**: SSS/Torcula Tmax = 0.00

**원인**: ROI 위치 추정 실패

**해결**: 
- 다른 환자 데이터로 테스트
- ROI 파라미터 조정 (scripts/calculate_pvt_tmax.py)

---

## 📞 문의

PVT 계산 관련 문의사항은 신경외과 전문의와 상의하여 개선하겠습니다.

**For Research Use Only - Not for Clinical Diagnosis**
