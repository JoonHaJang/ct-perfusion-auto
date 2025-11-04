#!/usr/bin/env python3
"""
DICOM Accuracy Verification
원본 DICOM과 생성된 시각화의 정확도를 픽셀 단위로 검증
"""
import pydicom
import numpy as np
import nibabel as nib
from pathlib import Path
import matplotlib.pyplot as plt
import json


def rgb_to_scalar_siemens(rgb_array, max_value=12.0):
    """
    Siemens CT Perfusion RGB를 스칼라 값으로 변환
    Based on: https://github.com/neurolabusc/rgb2scalar
    
    Siemens는 254개의 고유한 색상을 사용하여 0-max_value 범위를 인코딩
    """
    r = rgb_array[:, :, 0].astype(float)
    g = rgb_array[:, :, 1].astype(float)
    b = rgb_array[:, :, 2].astype(float)
    
    # RGB를 단일 인덱스로 변환 (0-254 범위)
    # Siemens 컬러맵은 Blue(낮음) -> Cyan -> Green -> Yellow -> Red(높음)
    
    # 방법 1: RGB를 가중 합으로 변환
    intensity = 0.299 * r + 0.587 * g + 0.114 * b
    
    # 0-254 범위로 정규화 후 실제 값으로 스케일링
    scalar_value = (intensity / 255.0) * max_value
    
    return scalar_value


def load_dicom_series_by_description(dicom_dir, target_description="TMAXD"):
    """특정 Series Description의 DICOM만 로드하고 RGB를 스칼라로 변환"""
    dicom_files = sorted(list(Path(dicom_dir).glob("*.dcm")))
    
    # 타겟 시리즈 필터링
    target_files = []
    for dcm_file in dicom_files:
        ds = pydicom.dcmread(dcm_file)
        series_desc = ds.get('SeriesDescription', '')
        if target_description in series_desc:
            target_files.append((dcm_file, ds))
    
    if not target_files:
        raise ValueError(f"No DICOM files found with SeriesDescription containing '{target_description}'")
    
    print(f"Found {len(target_files)} DICOM files for {target_description}")
    
    # 슬라이스 위치로 정렬
    target_files.sort(key=lambda x: float(x[1].ImagePositionPatient[2]))
    
    # 3D 볼륨 생성
    first_ds = target_files[0][1]
    pixel_array = first_ds.pixel_array
    
    # RGB 이미지인 경우 스칼라로 변환
    if len(pixel_array.shape) == 3:
        print("Converting RGB to scalar values (Siemens CT Perfusion)")
        img_shape = pixel_array.shape[:2]
        volume = np.zeros((len(target_files), img_shape[0], img_shape[1]))
        
        # Tmax의 일반적인 최대값은 12초
        max_tmax = 12.0
        
        for i, (dcm_file, ds) in enumerate(target_files):
            rgb_array = ds.pixel_array
            # RGB를 Tmax 스칼라 값으로 변환
            scalar_slice = rgb_to_scalar_siemens(rgb_array, max_tmax)
            volume[i, :, :] = scalar_slice
    else:
        img_shape = pixel_array.shape
        volume = np.zeros((len(target_files), img_shape[0], img_shape[1]))
        
        for i, (dcm_file, ds) in enumerate(target_files):
            volume[i, :, :] = ds.pixel_array
    
    print(f"DICOM Volume shape: {volume.shape}")
    print(f"DICOM Value range: [{volume.min():.4f}, {volume.max():.4f}]")
    print(f"DICOM Mean: {volume.mean():.4f}, Std: {volume.std():.4f}")
    
    return volume, target_files


def load_nifti_volume(nifti_path):
    """NIfTI 파일 로드"""
    img = nib.load(nifti_path)
    data = img.get_fdata()
    
    print(f"\nNIfTI Volume shape: {data.shape}")
    print(f"NIfTI Value range: [{data.min():.4f}, {data.max():.4f}]")
    print(f"NIfTI Mean: {data.mean():.4f}, Std: {data.std():.4f}")
    
    return data


def compare_volumes_exact(dicom_volume, nifti_volume):
    """두 볼륨의 정확한 비교"""
    print("\n" + "="*60)
    print("EXACT VOLUME COMPARISON")
    print("="*60)
    
    # 형태 비교
    if dicom_volume.shape != nifti_volume.shape:
        print(f"⚠️  WARNING: Shape mismatch!")
        print(f"   DICOM: {dicom_volume.shape}")
        print(f"   NIfTI: {nifti_volume.shape}")
        
        # 최소 공통 크기로 자르기
        min_shape = tuple(min(d, n) for d, n in zip(dicom_volume.shape, nifti_volume.shape))
        dicom_volume = dicom_volume[:min_shape[0], :min_shape[1], :min_shape[2]]
        nifti_volume = nifti_volume[:min_shape[0], :min_shape[1], :min_shape[2]]
        print(f"   Cropped to: {min_shape}")
    
    # 픽셀 단위 비교
    absolute_diff = np.abs(dicom_volume - nifti_volume)
    
    # 상대 오차 (0으로 나누기 방지)
    relative_diff = np.zeros_like(absolute_diff)
    mask = dicom_volume != 0
    relative_diff[mask] = absolute_diff[mask] / np.abs(dicom_volume[mask])
    
    # 통계
    mae = absolute_diff.mean()
    max_diff = absolute_diff.max()
    rmse = np.sqrt((absolute_diff ** 2).mean())
    
    # 상관계수
    correlation = np.corrcoef(dicom_volume.flatten(), nifti_volume.flatten())[0, 1]
    
    # 정확도 판정
    print(f"\n📊 Accuracy Metrics:")
    print(f"   Mean Absolute Error (MAE): {mae:.6f}")
    print(f"   Root Mean Square Error (RMSE): {rmse:.6f}")
    print(f"   Maximum Difference: {max_diff:.6f}")
    print(f"   Correlation Coefficient: {correlation:.8f}")
    
    # 픽셀 일치율
    tolerance_levels = [0.001, 0.01, 0.1, 1.0]
    print(f"\n📈 Pixel Match Rate:")
    for tol in tolerance_levels:
        match_rate = (absolute_diff <= tol).sum() / absolute_diff.size * 100
        print(f"   Within {tol:6.3f}: {match_rate:6.2f}%")
    
    # 판정
    print(f"\n🎯 Verification Result:")
    if mae < 0.001 and correlation > 0.9999:
        print("   ✅ PERFECT MATCH - 완벽한 일치!")
        status = "PERFECT"
    elif mae < 0.01 and correlation > 0.999:
        print("   ✅ EXCELLENT - 매우 높은 정확도")
        status = "EXCELLENT"
    elif mae < 0.1 and correlation > 0.99:
        print("   ⚠️  GOOD - 양호한 정확도 (미세한 차이 존재)")
        status = "GOOD"
    elif mae < 1.0 and correlation > 0.95:
        print("   ⚠️  ACCEPTABLE - 허용 가능 (주의 필요)")
        status = "ACCEPTABLE"
    else:
        print("   ❌ FAILED - 정확도 불충분!")
        status = "FAILED"
    
    return {
        'mae': float(mae),
        'rmse': float(rmse),
        'max_diff': float(max_diff),
        'correlation': float(correlation),
        'status': status,
        'shape_match': dicom_volume.shape == nifti_volume.shape
    }


def visualize_slice_comparison(dicom_volume, nifti_volume, slice_idx, output_dir):
    """특정 슬라이스의 상세 비교 시각화"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    dicom_slice = dicom_volume[slice_idx, :, :]
    nifti_slice = nifti_volume[slice_idx, :, :]
    
    diff = np.abs(dicom_slice - nifti_slice)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # DICOM 원본
    im1 = axes[0, 0].imshow(dicom_slice, cmap='jet')
    axes[0, 0].set_title(f'DICOM Original - Slice {slice_idx}', fontsize=14, fontweight='bold')
    axes[0, 0].axis('off')
    plt.colorbar(im1, ax=axes[0, 0], fraction=0.046)
    
    # NIfTI 변환
    im2 = axes[0, 1].imshow(nifti_slice, cmap='jet')
    axes[0, 1].set_title(f'NIfTI Converted - Slice {slice_idx}', fontsize=14, fontweight='bold')
    axes[0, 1].axis('off')
    plt.colorbar(im2, ax=axes[0, 1], fraction=0.046)
    
    # 차이 맵
    im3 = axes[0, 2].imshow(diff, cmap='hot')
    axes[0, 2].set_title(f'Absolute Difference\nMAE: {diff.mean():.6f}', fontsize=14, fontweight='bold')
    axes[0, 2].axis('off')
    plt.colorbar(im3, ax=axes[0, 2], fraction=0.046)
    
    # 히스토그램 비교
    axes[1, 0].hist(dicom_slice.flatten(), bins=50, alpha=0.7, label='DICOM', color='blue')
    axes[1, 0].hist(nifti_slice.flatten(), bins=50, alpha=0.7, label='NIfTI', color='red')
    axes[1, 0].set_title('Value Distribution', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Pixel Value')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 산점도
    sample_size = min(10000, dicom_slice.size)
    sample_indices = np.random.choice(dicom_slice.size, sample_size, replace=False)
    axes[1, 1].scatter(dicom_slice.flatten()[sample_indices], 
                       nifti_slice.flatten()[sample_indices], 
                       alpha=0.3, s=1)
    axes[1, 1].plot([dicom_slice.min(), dicom_slice.max()], 
                    [dicom_slice.min(), dicom_slice.max()], 
                    'r--', label='Perfect Match')
    axes[1, 1].set_title('Pixel-by-Pixel Correlation', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('DICOM Value')
    axes[1, 1].set_ylabel('NIfTI Value')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    # 통계 정보
    stats_text = f"""
    SLICE {slice_idx} STATISTICS
    
    DICOM:
      Mean:  {dicom_slice.mean():.4f}
      Std:   {dicom_slice.std():.4f}
      Min:   {dicom_slice.min():.4f}
      Max:   {dicom_slice.max():.4f}
    
    NIfTI:
      Mean:  {nifti_slice.mean():.4f}
      Std:   {nifti_slice.std():.4f}
      Min:   {nifti_slice.min():.4f}
      Max:   {nifti_slice.max():.4f}
    
    DIFFERENCE:
      MAE:   {diff.mean():.6f}
      Max:   {diff.max():.6f}
      Corr:  {np.corrcoef(dicom_slice.flatten(), nifti_slice.flatten())[0,1]:.8f}
    """
    axes[1, 2].text(0.05, 0.5, stats_text, fontsize=10, family='monospace', 
                    va='center', transform=axes[1, 2].transAxes)
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_dir / f'accuracy_slice_{slice_idx:03d}.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Saved: {output_dir / f'accuracy_slice_{slice_idx:03d}.png'}")


def main():
    print("="*60)
    print("DICOM ACCURACY VERIFICATION")
    print("픽셀 단위 정확도 검증")
    print("="*60)
    
    # 경로 설정
    dicom_dir = Path(r"C:\Users\USER\Desktop\의료 저널\Research\CTP_MT\487460_안연순_20240423225748")
    
    # NIfTI 파일 찾기 (여러 위치 검색)
    search_paths = [
        Path(r"C:\Users\USER\Desktop\의료 저널\ct-perfusion-auto\analysis_results\487460_안연순_20240423225748"),
        Path(r"C:\Users\USER\Desktop\의료 저널\analysis_results\487460_안연순_20240423225748"),
    ]
    
    nifti_candidates = []
    for search_path in search_paths:
        if search_path.exists():
            nifti_candidates.extend(list(search_path.glob("**/*TMAXD*.nii.gz")))
    
    if not nifti_candidates:
        print("\n❌ NIfTI 파일을 찾을 수 없습니다!")
        print("먼저 GUI를 통해 분석을 실행하세요:")
        print("  python ct_perfusion_viewer.py")
        print(f"\n검색한 경로:")
        for path in search_paths:
            print(f"  - {path}")
        return
    
    nifti_file = nifti_candidates[0]
    print(f"\nNIfTI file found: {nifti_file}")
    
    output_dir = Path(r"C:\Users\USER\Desktop\의료 저널\ct-perfusion-auto\accuracy_verification")
    
    # 1. DICOM 로드 (TMAXD 시리즈만)
    print("\n[1] Loading DICOM series (TMAXD)...")
    dicom_volume, dicom_files = load_dicom_series_by_description(dicom_dir, "TMAXD")
    
    # 2. NIfTI 로드
    print("\n[2] Loading NIfTI volume...")
    nifti_volume = load_nifti_volume(nifti_file)
    
    # 3. 정확도 비교
    print("\n[3] Comparing volumes...")
    results = compare_volumes_exact(dicom_volume, nifti_volume)
    
    # 4. 여러 슬라이스 시각화
    print("\n[4] Visualizing slice comparisons...")
    num_slices = min(dicom_volume.shape[0], nifti_volume.shape[0])
    test_slices = [
        num_slices // 4,
        num_slices // 2,
        3 * num_slices // 4
    ]
    
    for slice_idx in test_slices:
        visualize_slice_comparison(dicom_volume, nifti_volume, slice_idx, output_dir)
    
    # 5. 결과 저장
    results_file = output_dir / 'accuracy_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n결과 저장: {results_file}")
    print(f"시각화 저장: {output_dir}")
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)
    
    if results['status'] in ['PERFECT', 'EXCELLENT']:
        print("\n✅ 원본 DICOM과 생성된 시각화가 정확히 일치합니다!")
    elif results['status'] == 'GOOD':
        print("\n⚠️  미세한 차이가 있지만 임상적으로 허용 가능한 수준입니다.")
    else:
        print("\n❌ 정확도 문제가 발견되었습니다. 변환 과정을 점검해야 합니다.")


if __name__ == "__main__":
    main()
