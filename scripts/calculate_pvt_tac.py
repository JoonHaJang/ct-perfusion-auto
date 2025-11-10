#!/usr/bin/env python3
"""
PVT (Prolonged Venous Transit) Calculator - TAC-based Method

Calculates PVT from 4D CT Perfusion data using Time-Attenuation Curves:
PVT = VOF peak time - AIF peak time

Where:
- AIF (Arterial Input Function): Contrast peak time in cerebral artery (MCA/ICA)
- VOF (Venous Output Function): Contrast peak time in venous sinus (SSS)

Clinical Interpretation:
- < 5.0 sec: Normal venous outflow
- 5.0-6.0 sec: Mild delay (may not be clinically significant)
- > 6.0 sec: Significant delay (risk of infarct progression)
- > 7.0 sec: Severe venous congestion (poor prognosis)
"""

import numpy as np
import pydicom
from pathlib import Path
import json
from scipy import ndimage
from scipy.signal import find_peaks
import sys
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


class PVTCalculatorTAC:
    """TAC 기반 PVT 계산기"""
    
    def __init__(self, baseline_end_time=8.0):
        """
        Args:
            baseline_end_time: Baseline 구간 끝 시간 (초), 기본값 8.0
        """
        self.baseline_end_time = baseline_end_time
        
    def load_4d_perfusion(self, dicom_dir):
        """
        4D CT Perfusion DICOM 로드
        
        Returns:
            data_4d: (time, z, y, x) 4D array
            time_points: 시간 배열 (초)
        """
        dicom_dir = Path(dicom_dir)
        dicom_files = sorted(dicom_dir.glob("*.dcm"))
        
        if len(dicom_files) == 0:
            raise ValueError(f"No DICOM files found in {dicom_dir}")
        
        print(f"Found {len(dicom_files)} DICOM files")
        
        # 첫 파일로 메타데이터 확인
        first_ds = pydicom.dcmread(dicom_files[0])
        
        # 시간 정보 추출 시도
        time_points = []
        data_list = []
        img_shape = None
        
        for dcm_file in dicom_files:
            try:
                ds = pydicom.dcmread(dcm_file)
                
                # 픽셀 데이터 추출
                if hasattr(ds, 'pixel_array'):
                    img = ds.pixel_array.astype(float)
                    
                    # 첫 이미지 크기 저장
                    if img_shape is None:
                        img_shape = img.shape
                    
                    # 크기가 다른 이미지는 건너뛰기 (perfusion map일 수 있음)
                    if img.shape != img_shape:
                        continue
                    
                    # Rescale
                    if hasattr(ds, 'RescaleSlope') and hasattr(ds, 'RescaleIntercept'):
                        img = img * float(ds.RescaleSlope) + float(ds.RescaleIntercept)
                    
                    data_list.append(img)
                    
                    # 시간 정보 (Acquisition Time 또는 Content Time)
                    if hasattr(ds, 'AcquisitionTime'):
                        time_str = ds.AcquisitionTime
                        # HHMMSS.ffffff 형식
                        hours = float(time_str[0:2])
                        minutes = float(time_str[2:4])
                        seconds = float(time_str[4:])
                        time_sec = hours * 3600 + minutes * 60 + seconds
                        time_points.append(time_sec)
                    else:
                        # 시간 정보 없으면 인덱스 사용
                        time_points.append(len(time_points) * 1.5)  # 1.5초 간격 가정
                        
            except Exception as e:
                print(f"Warning: Failed to read {dcm_file}: {e}")
                continue
        
        if len(data_list) == 0:
            raise ValueError("No valid DICOM images loaded")
        
        print(f"Loaded {len(data_list)} images with shape {img_shape}")
        
        # 4D 배열로 변환
        data_4d = np.array(data_list)
        time_points = np.array(time_points)
        
        # 시간을 0부터 시작하도록 정규화
        time_points = time_points - time_points[0]
        
        print(f"Loaded 4D data: {data_4d.shape}")
        print(f"Time range: {time_points[0]:.1f} - {time_points[-1]:.1f} sec")
        print(f"Number of time points: {len(time_points)}")
        
        return data_4d, time_points
    
    def extract_tac(self, data_4d, time_points, roi_mask):
        """
        ROI에서 Time-Attenuation Curve 추출
        
        Args:
            data_4d: (time, z, y, x) 4D array
            time_points: 시간 배열
            roi_mask: (z, y, x) ROI 마스크
            
        Returns:
            tac: Time-Attenuation Curve (ΔHU)
            time_points: 시간 배열
        """
        # 각 시간 지점에서 ROI 평균 HU 계산
        hu_avg = []
        for t in range(data_4d.shape[0]):
            frame = data_4d[t]
            roi_values = frame[roi_mask]
            hu_avg.append(np.mean(roi_values))
        
        hu_avg = np.array(hu_avg)
        
        # Baseline HU 계산 (조영제 주입 전)
        baseline_indices = time_points <= self.baseline_end_time
        if np.sum(baseline_indices) > 0:
            hu_baseline = np.mean(hu_avg[baseline_indices])
        else:
            hu_baseline = hu_avg[0]
        
        # ΔHU 계산
        tac = hu_avg - hu_baseline
        
        return tac, time_points
    
    def find_peak_time(self, tac, time_points, min_height=5.0):
        """
        TAC에서 peak time 찾기
        
        Args:
            tac: Time-Attenuation Curve
            time_points: 시간 배열
            min_height: 최소 peak 높이 (HU)
            
        Returns:
            peak_time: Peak 시간 (초)
            peak_value: Peak HU 값
        """
        # Peak 찾기
        peaks, properties = find_peaks(tac, height=min_height, distance=3)
        
        if len(peaks) == 0:
            # Peak 없으면 최대값 사용
            peak_idx = np.argmax(tac)
            peak_time = time_points[peak_idx]
            peak_value = tac[peak_idx]
        else:
            # 가장 높은 peak 선택
            highest_peak_idx = peaks[np.argmax(properties['peak_heights'])]
            peak_time = time_points[highest_peak_idx]
            peak_value = tac[highest_peak_idx]
        
        return float(peak_time), float(peak_value)
    
    def define_aif_roi(self, data_4d):
        """
        AIF ROI 정의 (MCA 영역)
        
        중간 슬라이스의 좌우 측면 영역 (Sylvian fissure 근처)
        """
        # 평균 이미지 생성 (시간 축 평균)
        mean_img = np.mean(data_4d, axis=0)
        
        # 뇌 마스크 생성
        brain_mask = mean_img > np.percentile(mean_img, 20)
        brain_mask = ndimage.binary_fill_holes(brain_mask)
        
        # 중간 슬라이스 선택
        z_mid = mean_img.shape[0] // 2
        z_range = slice(max(0, z_mid-2), min(mean_img.shape[0], z_mid+3))
        
        # 좌우 측면 영역 (MCA 위치)
        y_center = mean_img.shape[1] // 2
        x_center = mean_img.shape[2] // 2
        
        # 좌측 MCA ROI
        roi_left = np.zeros_like(mean_img, dtype=bool)
        roi_left[z_range, 
                 y_center-15:y_center+15,
                 x_center-40:x_center-20] = True
        roi_left = roi_left & brain_mask
        
        # 우측 MCA ROI
        roi_right = np.zeros_like(mean_img, dtype=bool)
        roi_right[z_range,
                  y_center-15:y_center+15,
                  x_center+20:x_center+40] = True
        roi_right = roi_right & brain_mask
        
        # 둘 중 더 큰 ROI 선택
        if np.sum(roi_left) > np.sum(roi_right):
            aif_roi = roi_left
        else:
            aif_roi = roi_right
        
        print(f"AIF ROI size: {np.sum(aif_roi)} voxels")
        
        return aif_roi
    
    def define_vof_roi(self, data_4d):
        """
        VOF ROI 정의 (SSS - Superior Sagittal Sinus)
        
        상부 정중선 영역
        """
        # 평균 이미지 생성
        mean_img = np.mean(data_4d, axis=0)
        
        # 뇌 마스크 생성
        brain_mask = mean_img > np.percentile(mean_img, 20)
        brain_mask = ndimage.binary_fill_holes(brain_mask)
        
        # 상부 슬라이스 (상위 30%)
        z_start = int(mean_img.shape[0] * 0.7)
        z_range = slice(z_start, mean_img.shape[0])
        
        # 정중선 (좌우 중앙)
        x_center = mean_img.shape[2] // 2
        
        # SSS ROI (정중선 상부)
        vof_roi = np.zeros_like(mean_img, dtype=bool)
        vof_roi[z_range,
                :,
                x_center-10:x_center+10] = True
        vof_roi = vof_roi & brain_mask
        
        print(f"VOF ROI size: {np.sum(vof_roi)} voxels")
        
        return vof_roi
    
    def calculate_pvt(self, dicom_dir, save_tac=False, output_dir=None):
        """
        4D CT Perfusion에서 PVT 계산
        
        Args:
            dicom_dir: DICOM 폴더 경로
            save_tac: TAC 곡선 저장 여부
            output_dir: 출력 폴더 (save_tac=True일 때)
            
        Returns:
            dict: PVT 계산 결과
        """
        # 1. 4D 데이터 로드
        print("Loading 4D CT Perfusion data...")
        data_4d, time_points = self.load_4d_perfusion(dicom_dir)
        
        # 2. ROI 정의
        print("\nDefining ROIs...")
        aif_roi = self.define_aif_roi(data_4d)
        vof_roi = self.define_vof_roi(data_4d)
        
        # 3. TAC 추출
        print("\nExtracting Time-Attenuation Curves...")
        aif_tac, aif_time = self.extract_tac(data_4d, time_points, aif_roi)
        vof_tac, vof_time = self.extract_tac(data_4d, time_points, vof_roi)
        
        # 4. Peak time 찾기
        print("\nFinding peak times...")
        aif_peak_time, aif_peak_value = self.find_peak_time(aif_tac, aif_time)
        vof_peak_time, vof_peak_value = self.find_peak_time(vof_tac, vof_time)
        
        print(f"AIF peak: {aif_peak_time:.2f} sec ({aif_peak_value:.1f} HU)")
        print(f"VOF peak: {vof_peak_time:.2f} sec ({vof_peak_value:.1f} HU)")
        
        # 5. PVT 계산
        pvt = vof_peak_time - aif_peak_time
        
        print(f"\nPVT = {pvt:.2f} sec")
        
        # 6. 임상 해석
        interpretation = self._interpret_pvt(pvt)
        clinical_sig = self._get_clinical_significance(pvt)
        
        result = {
            'pvt_seconds': float(pvt),
            'aif_peak_time': float(aif_peak_time),
            'aif_peak_value': float(aif_peak_value),
            'vof_peak_time': float(vof_peak_time),
            'vof_peak_value': float(vof_peak_value),
            'interpretation': interpretation,
            'clinical_significance': clinical_sig,
            'method': 'TAC-based (AIF-VOF peak time difference)'
        }
        
        # 7. TAC 저장 (선택사항)
        if save_tac and output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # TAC 데이터 JSON 저장
            tac_data = {
                'time_points': time_points.tolist(),
                'aif_tac': aif_tac.tolist(),
                'vof_tac': vof_tac.tolist(),
                'aif_peak_time': float(aif_peak_time),
                'aif_peak_value': float(aif_peak_value),
                'vof_peak_time': float(vof_peak_time),
                'vof_peak_value': float(vof_peak_value),
                'pvt_seconds': float(pvt)
            }
            
            json_path = output_dir / 'tac_curves.json'
            with open(json_path, 'w') as f:
                json.dump(tac_data, f, indent=2)
            
            print(f"\nTAC curves data saved to: {json_path}")
            
            # TAC 그래프 PNG 생성
            png_path = output_dir / 'tac_curves.png'
            self._plot_tac_curves(
                time_points, aif_tac, vof_tac,
                aif_peak_time, vof_peak_time, pvt,
                png_path
            )
            print(f"TAC curves plot saved to: {png_path}")
        
        return result
    
    def _plot_tac_curves(self, time_points, aif_tac, vof_tac, 
                         aif_peak_time, vof_peak_time, pvt, output_path):
        """
        TAC 곡선 그래프 생성 (이미지와 동일한 스타일)
        
        Args:
            time_points: 시간 배열
            aif_tac: AIF TAC 데이터
            vof_tac: VOF TAC 데이터
            aif_peak_time: AIF peak 시간
            vof_peak_time: VOF peak 시간
            pvt: PVT 값
            output_path: 출력 파일 경로
        """
        plt.figure(figsize=(10, 6), facecolor='#2b2b2b')
        ax = plt.gca()
        ax.set_facecolor('#2b2b2b')
        
        # AIF 곡선 (분홍색)
        plt.plot(time_points, aif_tac, 'o-', color='#ff69b4', 
                linewidth=2, markersize=4, label='AIF (Arterial Input)', alpha=0.8)
        
        # VOF 곡선 (노란색)
        plt.plot(time_points, vof_tac, 's-', color='#ffd700', 
                linewidth=2, markersize=4, label='VOF (Venous Output)', alpha=0.8)
        
        # Peak 지점 표시
        aif_peak_idx = np.argmin(np.abs(time_points - aif_peak_time))
        vof_peak_idx = np.argmin(np.abs(time_points - vof_peak_time))
        
        plt.plot(aif_peak_time, aif_tac[aif_peak_idx], 'o', 
                color='#ff1493', markersize=10, label=f'AIF Peak ({aif_peak_time:.1f}s)')
        plt.plot(vof_peak_time, vof_tac[vof_peak_idx], 's', 
                color='#ffa500', markersize=10, label=f'VOF Peak ({vof_peak_time:.1f}s)')
        
        # Peak time에 수직선 그리기
        plt.axvline(x=aif_peak_time, color='#ff69b4', linestyle='--', alpha=0.5)
        plt.axvline(x=vof_peak_time, color='#ffd700', linestyle='--', alpha=0.5)
        
        # PVT 구간 표시
        y_min, y_max = ax.get_ylim()
        plt.fill_betweenx([y_min, y_max], aif_peak_time, vof_peak_time, 
                         color='cyan', alpha=0.2, label=f'PVT = {pvt:.2f}s')
        
        # 그리드
        plt.grid(True, color='#404040', linestyle='-', linewidth=0.5, alpha=0.3)
        
        # 레이블 및 제목
        plt.xlabel('Time (sec)', fontsize=12, color='white')
        plt.ylabel('ΔHU (Hounsfield Units)', fontsize=12, color='white')
        plt.title('Time-Attenuation Curves (TAC)\nPVT Analysis', 
                 fontsize=14, fontweight='bold', color='white', pad=20)
        
        # 범례
        legend = plt.legend(loc='upper right', fontsize=10, framealpha=0.9)
        legend.get_frame().set_facecolor('#3b3b3b')
        for text in legend.get_texts():
            text.set_color('white')
        
        # 축 색상
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['right'].set_color('white')
        ax.tick_params(colors='white')
        
        # PVT 결과 텍스트 추가
        pvt_text = f'PVT = {pvt:.2f} sec'
        if pvt < 5.0:
            status = 'Normal'
            color = '#00ff00'
        elif pvt < 6.0:
            status = 'Mild Delay'
            color = '#ffff00'
        elif pvt < 7.0:
            status = 'Significant Delay'
            color = '#ff8c00'
        else:
            status = 'Severe Congestion'
            color = '#ff0000'
        
        plt.text(0.02, 0.98, f'{pvt_text}\n{status}', 
                transform=ax.transAxes, fontsize=12, fontweight='bold',
                verticalalignment='top', color=color,
                bbox=dict(boxstyle='round', facecolor='#3b3b3b', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, facecolor='#2b2b2b')
        plt.close()
    
    def _interpret_pvt(self, pvt):
        """PVT 값 해석"""
        if pvt < 5.0:
            return "정상 정맥 유출 (Normal venous outflow)"
        elif pvt < 6.0:
            return "경도 정맥 유출 지연 (Mild venous outflow delay)"
        elif pvt < 7.0:
            return "의미 있는 정맥 유출 지연 (Significant venous outflow delay)"
        else:
            return "심각한 정맥 울혈 (Severe venous congestion)"
    
    def _get_clinical_significance(self, pvt):
        """임상적 의의"""
        if pvt < 5.0:
            return {
                'risk_level': 'LOW',
                'prognosis': '양호한 예후 예상',
                'recommendation': '표준 치료 프로토콜 적용',
                'warning': None
            }
        elif pvt < 6.0:
            return {
                'risk_level': 'MODERATE',
                'prognosis': '경도 지연, 임상적 의미 불명확',
                'recommendation': '모니터링 권장',
                'warning': None
            }
        elif pvt < 7.0:
            return {
                'risk_level': 'HIGH',
                'prognosis': 'Infarct progression 위험',
                'recommendation': '적극적 모니터링 및 치료 고려',
                'warning': '정맥 유출 장애 가능성'
            }
        else:
            return {
                'risk_level': 'VERY HIGH',
                'prognosis': '예후 불량 가능성 높음',
                'recommendation': '즉각적인 치료 고려, 집중 모니터링',
                'warning': '심각한 정맥 울혈, 뇌부종 및 microcirculatory failure 위험'
            }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate PVT from 4D CT Perfusion')
    parser.add_argument('dicom_dir', help='Path to DICOM folder')
    parser.add_argument('output_json', help='Path to output JSON file')
    parser.add_argument('--save-tac', action='store_true', help='Save TAC curves')
    parser.add_argument('--baseline', type=float, default=8.0,
                        help='Baseline end time in seconds (default: 8.0)')
    
    args = parser.parse_args()
    
    # PVT 계산
    calculator = PVTCalculatorTAC(baseline_end_time=args.baseline)
    
    output_dir = Path(args.output_json).parent if args.save_tac else None
    result = calculator.calculate_pvt(args.dicom_dir, save_tac=args.save_tac, output_dir=output_dir)
    
    # 결과 출력
    print("\n" + "="*60)
    print("PVT Analysis Results (TAC-based Method)")
    print("="*60)
    print(f"PVT: {result['pvt_seconds']:.2f} seconds")
    print(f"\nAIF (Arterial Input):")
    print(f"  - Peak time: {result['aif_peak_time']:.2f} sec")
    print(f"  - Peak value: {result['aif_peak_value']:.1f} HU")
    print(f"\nVOF (Venous Output):")
    print(f"  - Peak time: {result['vof_peak_time']:.2f} sec")
    print(f"  - Peak value: {result['vof_peak_value']:.1f} HU")
    print(f"\nInterpretation: {result['interpretation']}")
    print(f"\nClinical Significance:")
    print(f"  - Risk Level: {result['clinical_significance']['risk_level']}")
    print(f"  - Prognosis: {result['clinical_significance']['prognosis']}")
    print(f"  - Recommendation: {result['clinical_significance']['recommendation']}")
    if result['clinical_significance']['warning']:
        print(f"  - ⚠️ Warning: {result['clinical_significance']['warning']}")
    print("="*60 + "\n")
    
    # JSON 저장
    with open(args.output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {args.output_json}")


if __name__ == '__main__':
    main()
