#!/usr/bin/env python3
"""
PVT (Prolonged Venous Transit) Calculator - Tmax-based Method

Based on:
Amorim et al. (2023). CT perfusion to measure venous outflow in acute ischemic 
stroke in patients with a large vessel occlusion. 
Journal of NeuroInterventional Surgery, 16(4), 343-348.

Method:
- PVT+ = (SSS Tmax ≥ 10s) OR (Torcula Tmax ≥ 10s)
- SSS: Superior Sagittal Sinus (posterior, at occipital horns level)
- Torcula: Confluence of sinuses (posterior brain)
"""

import numpy as np
import nibabel as nib
from pathlib import Path
from scipy import ndimage
import json


class PVTCalculator:
    """Tmax 기반 PVT 계산기"""
    
    def __init__(self, tmax_threshold=10.0):
        """
        Args:
            tmax_threshold: PVT 양성 판정 기준 (초), 기본값 10.0
        """
        self.tmax_threshold = tmax_threshold
        
    def calculate_pvt(self, tmax_map, brain_mask=None, return_masks=False):
        """
        Tmax map에서 PVT 계산
        
        Args:
            tmax_map: 3D numpy array, Tmax 값 (초)
            brain_mask: 3D numpy array, 뇌 영역 마스크 (optional)
            return_masks: bool, ROI 마스크 반환 여부
            
        Returns:
            dict: PVT 평가 결과 (+ ROI 마스크)
        """
        if brain_mask is None:
            brain_mask = self._generate_simple_brain_mask(tmax_map)
        
        # 1. ROI 정의
        sss_roi = self._define_sss_roi(tmax_map, brain_mask)
        torcula_roi = self._define_torcula_roi(tmax_map, brain_mask)
        
        # ROI 크기 확인
        sss_roi_size = np.sum(sss_roi)
        torcula_roi_size = np.sum(torcula_roi)
        
        if sss_roi_size == 0:
            print("⚠️ Warning: SSS ROI is empty! Check brain mask or ROI definition.")
        if torcula_roi_size == 0:
            print("⚠️ Warning: Torcula ROI is empty! Check brain mask or ROI definition.")
        
        # 2. 각 ROI에서 Tmax 값 추출
        sss_tmax_values = tmax_map[sss_roi]
        torcula_tmax_values = tmax_map[torcula_roi]
        
        # 3. 통계 계산
        sss_tmax_mean = np.mean(sss_tmax_values) if len(sss_tmax_values) > 0 else 0
        sss_tmax_max = np.max(sss_tmax_values) if len(sss_tmax_values) > 0 else 0
        
        torcula_tmax_mean = np.mean(torcula_tmax_values) if len(torcula_tmax_values) > 0 else 0
        torcula_tmax_max = np.max(torcula_tmax_values) if len(torcula_tmax_values) > 0 else 0
        
        # 4. PVT 판정 (논문 방법: "영역 존재 여부")
        # PVT+ = SSS나 Torcula에 Tmax ≥ 10초인 voxel이 존재하는가?
        sss_positive = np.any(sss_tmax_values >= self.tmax_threshold) if len(sss_tmax_values) > 0 else False
        torcula_positive = np.any(torcula_tmax_values >= self.tmax_threshold) if len(torcula_tmax_values) > 0 else False
        pvt_positive = sss_positive or torcula_positive
        
        # 추가: Tmax ≥ 10초 영역의 비율 계산
        sss_positive_ratio = np.sum(sss_tmax_values >= self.tmax_threshold) / len(sss_tmax_values) if len(sss_tmax_values) > 0 else 0
        torcula_positive_ratio = np.sum(torcula_tmax_values >= self.tmax_threshold) / len(torcula_tmax_values) if len(torcula_tmax_values) > 0 else 0
        
        # 5. 임상적 해석
        interpretation = self._interpret_pvt(
            pvt_positive, sss_tmax_mean, torcula_tmax_mean
        )
        
        result = {
            'pvt_status': 'PVT+' if pvt_positive else 'PVT-',
            'pvt_positive': bool(pvt_positive),
            'sss_tmax_mean': float(sss_tmax_mean),
            'sss_tmax_max': float(sss_tmax_max),
            'sss_positive': bool(sss_positive),
            'sss_positive_ratio': float(sss_positive_ratio),
            'torcula_tmax_mean': float(torcula_tmax_mean),
            'torcula_tmax_max': float(torcula_tmax_max),
            'torcula_positive': bool(torcula_positive),
            'torcula_positive_ratio': float(torcula_positive_ratio),
            'threshold': float(self.tmax_threshold),
            'interpretation': interpretation,
            'clinical_significance': self._get_clinical_significance(pvt_positive),
            'method': 'Qualitative assessment (presence of Tmax ≥ 10s region)'
        }
        
        # ROI 마스크 추가 (시각화용)
        if return_masks:
            # Tmax >= threshold 영역
            sss_positive_mask = sss_roi & (tmax_map >= self.tmax_threshold)
            torcula_positive_mask = torcula_roi & (tmax_map >= self.tmax_threshold)
            
            result['masks'] = {
                'sss_roi': sss_roi,
                'torcula_roi': torcula_roi,
                'sss_positive_mask': sss_positive_mask,
                'torcula_positive_mask': torcula_positive_mask
            }
        
        return result
    
    def _define_sss_roi(self, tmax_map, brain_mask):
        """
        Superior Sagittal Sinus ROI 정의
        
        위치: Posterior SSS at the level of occipital horns of lateral ventricles
        - 뇌의 상부 정중선
        - Z축 기준 상위 25% 영역
        """
        # Brain mask 좌표 추출
        brain_coords = np.where(brain_mask)
        if len(brain_coords[0]) == 0:
            print("⚠️ Warning: Brain mask is empty!")
            return np.zeros_like(tmax_map, dtype=bool)
        
        # 각 축의 범위와 중심
        axis_mins = [coords.min() for coords in brain_coords]
        axis_maxs = [coords.max() for coords in brain_coords]
        axis_centers = [(mn + mx) // 2 for mn, mx in zip(axis_mins, axis_maxs)]
        
        # 가장 작은 차원이 슬라이스 축
        slice_axis = np.argmin(tmax_map.shape)
        
        # SSS ROI: 상부 정중선
        # - 슬라이스 축: 상위 40%
        # - 가장 큰 축 (보통 좌우): 중앙 ±15 픽셀
        # - 나머지 축: 전체
        sss_roi = np.zeros_like(tmax_map, dtype=bool)
        
        # 축별로 범위 설정
        ranges = []
        for i in range(3):
            if i == slice_axis:
                # 슬라이스 축: 상위 40%
                start = axis_mins[i] + int((axis_maxs[i] - axis_mins[i]) * 0.6)
                end = axis_maxs[i] + 1
            elif tmax_map.shape[i] == max(tmax_map.shape):
                # 가장 큰 축 (좌우): 중앙
                start = max(0, axis_centers[i] - 15)
                end = min(tmax_map.shape[i], axis_centers[i] + 15)
            else:
                # 나머지 축: 전체
                start = 0
                end = tmax_map.shape[i]
            ranges.append((start, end))
        
        # ROI 생성
        sss_roi[ranges[0][0]:ranges[0][1], 
                ranges[1][0]:ranges[1][1], 
                ranges[2][0]:ranges[2][1]] = True
        
        # Brain mask와 교집합
        sss_roi = sss_roi & brain_mask
        
        return sss_roi
    
    def _define_torcula_roi(self, tmax_map, brain_mask):
        """
        Torcula (Confluence of Sinuses) ROI 정의
        
        위치: Posterior aspect of brain, junction of SSS and straight sinus
        - 뇌의 후방 중앙부
        """
        # Brain mask 좌표 추출
        brain_coords = np.where(brain_mask)
        if len(brain_coords[0]) == 0:
            print("⚠️ Warning: Brain mask is empty for Torcula!")
            return np.zeros_like(tmax_map, dtype=bool)
        
        # 각 축의 범위와 중심
        axis_mins = [coords.min() for coords in brain_coords]
        axis_maxs = [coords.max() for coords in brain_coords]
        axis_centers = [(mn + mx) // 2 for mn, mx in zip(axis_mins, axis_maxs)]
        
        # 가장 작은 차원이 슬라이스 축
        slice_axis = np.argmin(tmax_map.shape)
        
        # Torcula ROI: 후방 중앙부
        # - 슬라이스 축: 상위 40% 중심
        # - 가장 큰 축 (좌우): 중앙
        # - 나머지 축: 중앙
        roi_size = 15
        
        # 축별로 중심 위치 설정
        centers = []
        for i in range(3):
            if i == slice_axis:
                # 슬라이스 축: 상위 40% 위치
                center = axis_mins[i] + int((axis_maxs[i] - axis_mins[i]) * 0.7)
            else:
                # 다른 축: 중앙
                center = axis_centers[i]
            centers.append(center)
        
        # 구형 ROI 생성
        torcula_roi = np.zeros_like(tmax_map, dtype=bool)
        torcula_roi[
            max(0, centers[0]-roi_size):min(tmax_map.shape[0], centers[0]+roi_size),
            max(0, centers[1]-roi_size):min(tmax_map.shape[1], centers[1]+roi_size),
            max(0, centers[2]-roi_size):min(tmax_map.shape[2], centers[2]+roi_size)
        ] = True
        
        # Brain mask와 교집합
        torcula_roi = torcula_roi & brain_mask
        
        return torcula_roi
    
    def _generate_simple_brain_mask(self, tmax_map):
        """
        개선된 뇌 마스크 생성
        - Tmax > 0인 영역 추출
        - Morphological operations로 정제
        - 작은 noise 제거
        """
        # 1. 기본 마스크 (Tmax > 0)
        brain_mask = tmax_map > 0
        
        # 2. Morphological closing (작은 구멍 채우기)
        brain_mask = ndimage.binary_closing(brain_mask, structure=np.ones((3,3,3)))
        
        # 3. 구멍 채우기
        brain_mask = ndimage.binary_fill_holes(brain_mask)
        
        # 4. 작은 noise 제거 (connected component analysis)
        labeled, num_features = ndimage.label(brain_mask)
        
        if num_features > 0:
            # 가장 큰 component만 유지 (뇌)
            component_sizes = np.bincount(labeled.ravel())
            component_sizes[0] = 0  # background 제외
            largest_component = component_sizes.argmax()
            brain_mask = labeled == largest_component
        
        return brain_mask
    
    def _interpret_pvt(self, pvt_positive, sss_tmax, torcula_tmax):
        """PVT 결과 해석"""
        if not pvt_positive:
            return "정상 정맥 유출 (Normal venous outflow)"
        
        if sss_tmax >= self.tmax_threshold and torcula_tmax >= self.tmax_threshold:
            return "표재성 및 심부 정맥 유출 지연 (Both superficial and deep venous drainage delayed)"
        elif sss_tmax >= self.tmax_threshold:
            return "표재성 정맥 유출 지연 (Superficial venous drainage delayed)"
        else:
            return "심부 정맥 유출 지연 (Deep venous drainage delayed)"
    
    def _get_clinical_significance(self, pvt_positive):
        """임상적 의의"""
        if pvt_positive:
            return {
                'risk_level': 'HIGH',
                'prognosis': '예후 불량 가능성 (Poor prognosis)',
                'recommendation': 'Infarct progression 주의, 적극적 모니터링 필요',
                'evidence': 'PVT+ 환자는 excellent recovery 확률 11% (vs PVT- 39%)'
            }
        else:
            return {
                'risk_level': 'LOW',
                'prognosis': '양호한 예후 예상 (Favorable prognosis)',
                'recommendation': '표준 치료 프로토콜 적용',
                'evidence': 'PVT- 환자는 excellent recovery 확률 39%'
            }


def load_tmax_from_nifti(nifti_path):
    """NIfTI 파일에서 Tmax map 로드"""
    img = nib.load(nifti_path)
    tmax_map = img.get_fdata()
    return tmax_map


def process_patient_pvt(tmax_nifti_path, output_json_path=None, threshold=10.0):
    """
    환자 Tmax 데이터에서 PVT 계산
    
    Args:
        tmax_nifti_path: Tmax NIfTI 파일 경로
        output_json_path: 결과 저장 경로 (optional)
        threshold: PVT threshold in seconds (default: 10.0)
        
    Returns:
        dict: PVT 계산 결과
    """
    # 1. Tmax map 로드
    print(f"Loading Tmax map from: {tmax_nifti_path}")
    tmax_img = nib.load(tmax_nifti_path)
    tmax_map = tmax_img.get_fdata()
    
    # 2. PVT 계산 (마스크 저장 안 함)
    print(f"Calculating PVT (threshold: {threshold} sec)...")
    calculator = PVTCalculator(tmax_threshold=threshold)
    result = calculator.calculate_pvt(tmax_map, return_masks=False)
    
    # 3. 결과 출력
    print("\n" + "="*60)
    print("PVT Analysis Results (Amorim et al. 2023 Method)")
    print("="*60)
    print(f"PVT Status: {result['pvt_status']}")
    print(f"\nSSS (Superior Sagittal Sinus):")
    print(f"  - Tmax ≥ 10s region present: {result['sss_positive']}")
    print(f"  - Positive voxel ratio: {result['sss_positive_ratio']*100:.1f}%")
    print(f"  - Mean Tmax: {result['sss_tmax_mean']:.2f} sec")
    print(f"  - Max Tmax: {result['sss_tmax_max']:.2f} sec")
    print(f"\nTorcula (Confluence of Sinuses):")
    print(f"  - Tmax ≥ 10s region present: {result['torcula_positive']}")
    print(f"  - Positive voxel ratio: {result['torcula_positive_ratio']*100:.1f}%")
    print(f"  - Mean Tmax: {result['torcula_tmax_mean']:.2f} sec")
    print(f"  - Max Tmax: {result['torcula_tmax_max']:.2f} sec")
    print(f"\nInterpretation: {result['interpretation']}")
    print(f"\nClinical Significance:")
    print(f"  - Risk Level: {result['clinical_significance']['risk_level']}")
    print(f"  - Prognosis: {result['clinical_significance']['prognosis']}")
    print(f"  - Recommendation: {result['clinical_significance']['recommendation']}")
    print(f"\nMethod: {result['method']}")
    print("="*60 + "\n")
    
    # 4. JSON 저장
    if output_json_path:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {output_json_path}")
    
    return result


if __name__ == '__main__':
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate PVT from Tmax map')
    parser.add_argument('tmax_path', help='Path to Tmax NIfTI file')
    parser.add_argument('output_path', nargs='?', help='Path to output JSON file')
    parser.add_argument('--threshold', type=float, default=10.0, 
                        help='PVT threshold in seconds (default: 10.0)')
    
    args = parser.parse_args()
    
    # Threshold 전달
    result = process_patient_pvt(args.tmax_path, args.output_path, threshold=args.threshold)
