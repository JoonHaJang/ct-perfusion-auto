#!/usr/bin/env python3
"""
Penumbra 이미지에서 TAC 그래프 디지타이징

이미지 처리로 그래프 곡선을 추출하여 TAC 데이터 재생산
"""

import numpy as np
import pydicom
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image
import json
from scipy import ndimage
from scipy.signal import savgol_filter

def load_penumbra_slice(dicom_dir, slice_idx=None):
    """
    특정 슬라이스의 Penumbra 이미지 로드
    
    여러 Penumbra 시리즈가 있을 경우 가장 큰 시리즈 사용
    """
    dicom_files = sorted(Path(dicom_dir).glob("*.dcm"))
    
    # Penumbra 시리즈별로 그룹화
    penumbra_series = {}
    for f in dicom_files:
        try:
            ds = pydicom.dcmread(f)
            series_desc = ds.get('SeriesDescription', '')
            if 'PENUMBRA' in series_desc.upper():
                if series_desc not in penumbra_series:
                    penumbra_series[series_desc] = []
                penumbra_series[series_desc].append(f)
        except:
            continue
    
    if not penumbra_series:
        raise ValueError("No Penumbra images found")
    
    # 가장 큰 시리즈 선택
    largest_series = max(penumbra_series.items(), key=lambda x: len(x[1]))
    series_name, penumbra_files = largest_series
    penumbra_files = sorted(penumbra_files)
    
    print(f"Found {len(penumbra_series)} Penumbra series:")
    for series, files in penumbra_series.items():
        print(f"  - {series}: {len(files)} files")
    print(f"Using largest series: {series_name} ({len(penumbra_files)} files)")
    
    # 슬라이스 인덱스 결정
    if slice_idx is None or slice_idx >= len(penumbra_files):
        slice_idx = len(penumbra_files) - 1  # 마지막 슬라이스
    
    print(f"Loading Penumbra slice {slice_idx}: {penumbra_files[slice_idx].name}")
    ds = pydicom.dcmread(penumbra_files[slice_idx])
    img = ds.pixel_array
    
    return img, penumbra_files[slice_idx].name

def extract_graph_region(img):
    """
    그래프 영역 추출
    
    일반적으로 상단 1/3 영역에 그래프가 있음
    """
    h, w, c = img.shape
    
    # 상단 영역 (그래프 위치)
    graph_h = h // 3
    graph_region = img[:graph_h, :, :]
    
    return graph_region

def detect_curve_pixels(graph_region, color_range):
    """
    특정 색상 범위의 픽셀 검출
    
    Args:
        graph_region: RGB 이미지
        color_range: (R_min, R_max, G_min, G_max, B_min, B_max)
    """
    r_min, r_max, g_min, g_max, b_min, b_max = color_range
    
    r = graph_region[:, :, 0]
    g = graph_region[:, :, 1]
    b = graph_region[:, :, 2]
    
    mask = (
        (r >= r_min) & (r <= r_max) &
        (g >= g_min) & (g <= g_max) &
        (b >= b_min) & (b <= b_max)
    )
    
    return mask

def extract_curve_coordinates(mask):
    """
    마스크에서 곡선 좌표 추출
    
    각 X 좌표에서 Y 좌표의 중앙값 사용
    """
    h, w = mask.shape
    curve_points = []
    
    for x in range(w):
        y_coords = np.where(mask[:, x])[0]
        if len(y_coords) > 0:
            y_center = int(np.median(y_coords))
            curve_points.append((x, y_center))
    
    if len(curve_points) == 0:
        return None
    
    curve_points = np.array(curve_points)
    return curve_points

def pixel_to_graph_coords(curve_points, graph_region_shape, 
                          x_range=(0, 60), y_range=(-5, 15)):
    """
    픽셀 좌표를 그래프 좌표로 변환
    
    Args:
        curve_points: (N, 2) array of (x_pixel, y_pixel)
        graph_region_shape: (height, width)
        x_range: (x_min, x_max) in seconds
        y_range: (y_min, y_max) in HU
    """
    h, w = graph_region_shape[:2]
    
    # X: 픽셀 → 시간 (초)
    x_pixels = curve_points[:, 0]
    x_values = x_range[0] + (x_pixels / w) * (x_range[1] - x_range[0])
    
    # Y: 픽셀 → HU (이미지는 위에서 아래로, 그래프는 아래에서 위로)
    y_pixels = curve_points[:, 1]
    y_values = y_range[1] - (y_pixels / h) * (y_range[1] - y_range[0])
    
    return x_values, y_values

def digitize_tac_curves(img, slice_name):
    """
    Penumbra 이미지에서 TAC 곡선 디지타이징
    """
    print("\n" + "="*60)
    print(f"Digitizing TAC curves from: {slice_name}")
    print("="*60)
    
    # 1. 그래프 영역 추출
    graph_region = extract_graph_region(img)
    print(f"\nGraph region shape: {graph_region.shape}")
    
    # 2. 색상 범위 정의
    # 분홍색 (Rest) - 밝은 분홍/마젠타
    pink_range = (150, 255, 0, 150, 100, 255)
    
    # 노란색 (TAR) - 밝은 노랑
    yellow_range = (150, 255, 150, 255, 0, 150)
    
    # 3. 곡선 픽셀 검출
    print("\nDetecting curve pixels...")
    pink_mask = detect_curve_pixels(graph_region, pink_range)
    yellow_mask = detect_curve_pixels(graph_region, yellow_range)
    
    print(f"  Pink pixels: {np.sum(pink_mask)}")
    print(f"  Yellow pixels: {np.sum(yellow_mask)}")
    
    # 4. 곡선 좌표 추출
    print("\nExtracting curve coordinates...")
    pink_curve = extract_curve_coordinates(pink_mask)
    yellow_curve = extract_curve_coordinates(yellow_mask)
    
    if pink_curve is None or yellow_curve is None:
        print("ERROR: Failed to extract curves!")
        return None
    
    print(f"  Pink curve points: {len(pink_curve)}")
    print(f"  Yellow curve points: {len(yellow_curve)}")
    
    # 5. 픽셀 → 그래프 좌표 변환
    print("\nConverting to graph coordinates...")
    pink_time, pink_hu = pixel_to_graph_coords(pink_curve, graph_region.shape)
    yellow_time, yellow_hu = pixel_to_graph_coords(yellow_curve, graph_region.shape)
    
    # 6. 스무딩 (노이즈 제거)
    if len(pink_hu) > 10:
        pink_hu = savgol_filter(pink_hu, window_length=11, polyorder=3)
    if len(yellow_hu) > 10:
        yellow_hu = savgol_filter(yellow_hu, window_length=11, polyorder=3)
    
    # 7. Peak 찾기
    pink_peak_idx = np.argmax(pink_hu)
    yellow_peak_idx = np.argmax(yellow_hu)
    
    pink_peak_time = pink_time[pink_peak_idx]
    pink_peak_hu = pink_hu[pink_peak_idx]
    
    yellow_peak_time = yellow_time[yellow_peak_idx]
    yellow_peak_hu = yellow_hu[yellow_peak_idx]
    
    print("\n" + "="*60)
    print("TAC ANALYSIS RESULTS")
    print("="*60)
    print(f"\nRest (Pink) Curve:")
    print(f"  Peak time: {pink_peak_time:.1f} sec")
    print(f"  Peak ΔHU: {pink_peak_hu:.1f} HU")
    
    print(f"\nTAR (Yellow) Curve:")
    print(f"  Peak time: {yellow_peak_time:.1f} sec")
    print(f"  Peak ΔHU: {yellow_peak_hu:.1f} HU")
    
    print(f"\nPeak Time Difference:")
    print(f"  TAR - Rest = {yellow_peak_time - pink_peak_time:.1f} sec")
    
    result = {
        'slice_name': slice_name,
        'rest_curve': {
            'time': pink_time.tolist(),
            'delta_hu': pink_hu.tolist(),
            'peak_time': float(pink_peak_time),
            'peak_hu': float(pink_peak_hu)
        },
        'tar_curve': {
            'time': yellow_time.tolist(),
            'delta_hu': yellow_hu.tolist(),
            'peak_time': float(yellow_peak_time),
            'peak_hu': float(yellow_peak_hu)
        },
        'peak_time_difference': float(yellow_peak_time - pink_peak_time)
    }
    
    return result, graph_region, pink_mask, yellow_mask

def plot_results(img, graph_region, pink_mask, yellow_mask, result, output_path):
    """결과 시각화"""
    fig = plt.figure(figsize=(16, 10))
    
    # 원본 Penumbra 이미지
    ax1 = plt.subplot(2, 3, 1)
    ax1.imshow(img)
    ax1.set_title('Original Penumbra Image', fontsize=12, fontweight='bold')
    ax1.axis('off')
    
    # 그래프 영역
    ax2 = plt.subplot(2, 3, 2)
    ax2.imshow(graph_region)
    ax2.set_title('Graph Region (Extracted)', fontsize=12, fontweight='bold')
    ax2.axis('off')
    
    # 검출된 곡선 픽셀
    ax3 = plt.subplot(2, 3, 3)
    overlay = graph_region.copy()
    overlay[pink_mask] = [255, 0, 255]  # 분홍색 강조
    overlay[yellow_mask] = [255, 255, 0]  # 노란색 강조
    ax3.imshow(overlay)
    ax3.set_title('Detected Curve Pixels', fontsize=12, fontweight='bold')
    ax3.axis('off')
    
    # 재생산된 TAC 곡선
    ax4 = plt.subplot(2, 1, 2)
    
    rest_time = result['rest_curve']['time']
    rest_hu = result['rest_curve']['delta_hu']
    tar_time = result['tar_curve']['time']
    tar_hu = result['tar_curve']['delta_hu']
    
    ax4.plot(rest_time, rest_hu, 'o-', color='#ff69b4', 
            linewidth=2, markersize=3, label='Rest', alpha=0.8)
    ax4.plot(tar_time, tar_hu, 's-', color='#ffd700', 
            linewidth=2, markersize=3, label='TAR', alpha=0.8)
    
    # Peak 표시
    ax4.plot(result['rest_curve']['peak_time'], result['rest_curve']['peak_hu'], 
            'o', color='#ff1493', markersize=10, label=f"Rest Peak ({result['rest_curve']['peak_time']:.1f}s)")
    ax4.plot(result['tar_curve']['peak_time'], result['tar_curve']['peak_hu'], 
            's', color='#ffa500', markersize=10, label=f"TAR Peak ({result['tar_curve']['peak_time']:.1f}s)")
    
    ax4.axvline(x=result['rest_curve']['peak_time'], color='#ff69b4', linestyle='--', alpha=0.5)
    ax4.axvline(x=result['tar_curve']['peak_time'], color='#ffd700', linestyle='--', alpha=0.5)
    
    ax4.set_xlabel('Time (sec)', fontsize=12)
    ax4.set_ylabel('ΔHU (Hounsfield Units)', fontsize=12)
    ax4.set_title('Reconstructed Time-Attenuation Curves (TAC)', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='upper right', fontsize=10)
    ax4.set_xlim(0, 60)
    ax4.set_ylim(-5, 15)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\nPlot saved to: {output_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract TAC from Penumbra image')
    parser.add_argument('dicom_dir', help='DICOM folder')
    parser.add_argument('output_dir', help='Output folder')
    parser.add_argument('--slice', type=int, default=None, help='Slice index (default: last slice)')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Penumbra 이미지 로드
    img, slice_name = load_penumbra_slice(args.dicom_dir, args.slice)
    
    # 실제 사용된 슬라이스 인덱스 추출
    actual_slice_idx = slice_name.split('.')[0].split('_')[-1] if '_' in slice_name else 'last'
    
    # 2. TAC 곡선 디지타이징
    result_data = digitize_tac_curves(img, slice_name)
    
    if result_data is None:
        print("\nERROR: Failed to digitize curves")
        return
    
    result, graph_region, pink_mask, yellow_mask = result_data
    
    # 3. 결과 저장
    json_path = output_dir / f'tac_digitized_{actual_slice_idx}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {json_path}")
    
    # 4. 시각화
    plot_path = output_dir / f'tac_digitized_{actual_slice_idx}.png'
    plot_results(img, graph_region, pink_mask, yellow_mask, result, plot_path)
    
    # 5. 원본 Penumbra 이미지 저장
    original_path = output_dir / f'penumbra_original_{actual_slice_idx}.png'
    Image.fromarray(img).save(original_path)
    print(f"Original Penumbra image saved to: {original_path}")
    
    print("\n" + "="*60)
    print("DIGITIZATION COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
