#!/usr/bin/env python3
"""
Visualization Validation Script
원본 DICOM과 생성된 시각화 비교 검증
"""
import argparse
import numpy as np
import nibabel as nib
import pydicom
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image
import json


def load_dicom_series(dicom_dir):
    """DICOM 시리즈 로드"""
    dicom_files = sorted(list(Path(dicom_dir).glob("*.dcm")))
    
    if not dicom_files:
        raise ValueError(f"No DICOM files found in {dicom_dir}")
    
    print(f"Found {len(dicom_files)} DICOM files")
    
    # 첫 번째 파일로 메타데이터 확인
    first_ds = pydicom.dcmread(dicom_files[0])
    print(f"Series Description: {first_ds.get('SeriesDescription', 'N/A')}")
    print(f"Image Type: {first_ds.get('ImageType', 'N/A')}")
    
    # 모든 슬라이스 로드
    slices = []
    for dcm_file in dicom_files:
        ds = pydicom.dcmread(dcm_file)
        slices.append(ds)
    
    # 슬라이스 위치로 정렬
    slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
    
    # 3D 배열 생성
    img_shape = slices[0].pixel_array.shape
    volume = np.zeros((len(slices), img_shape[0], img_shape[1]))
    
    for i, s in enumerate(slices):
        volume[i, :, :] = s.pixel_array
    
    print(f"Volume shape: {volume.shape}")
    print(f"Value range: [{volume.min():.2f}, {volume.max():.2f}]")
    
    return volume, slices


def load_nifti_file(nifti_path):
    """NIfTI 파일 로드"""
    img = nib.load(nifti_path)
    data = img.get_fdata()
    
    print(f"\nNIfTI file: {nifti_path.name}")
    print(f"Shape: {data.shape}")
    print(f"Value range: [{data.min():.2f}, {data.max():.2f}]")
    
    return data


def compare_slices(dicom_volume, nifti_data, slice_idx, output_dir):
    """특정 슬라이스 비교"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # DICOM 슬라이스
    dicom_slice = dicom_volume[slice_idx, :, :]
    
    # NIfTI 슬라이스
    nifti_slice = nifti_data[slice_idx, :, :]
    
    # 정규화
    dicom_norm = (dicom_slice - dicom_slice.min()) / (dicom_slice.max() - dicom_slice.min())
    nifti_norm = (nifti_slice - nifti_slice.min()) / (nifti_slice.max() - nifti_slice.min())
    
    # 비교 시각화
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # DICOM 원본
    axes[0, 0].imshow(dicom_slice, cmap='gray')
    axes[0, 0].set_title(f'DICOM Slice {slice_idx}')
    axes[0, 0].axis('off')
    
    # NIfTI 변환
    axes[0, 1].imshow(nifti_slice, cmap='gray')
    axes[0, 1].set_title(f'NIfTI Slice {slice_idx}')
    axes[0, 1].axis('off')
    
    # 차이
    diff = np.abs(dicom_norm - nifti_norm)
    axes[0, 2].imshow(diff, cmap='hot')
    axes[0, 2].set_title(f'Difference (MAE: {diff.mean():.4f})')
    axes[0, 2].axis('off')
    
    # 히스토그램
    axes[1, 0].hist(dicom_slice.flatten(), bins=50, alpha=0.7, label='DICOM')
    axes[1, 0].set_title('DICOM Histogram')
    axes[1, 0].legend()
    
    axes[1, 1].hist(nifti_slice.flatten(), bins=50, alpha=0.7, label='NIfTI', color='orange')
    axes[1, 1].set_title('NIfTI Histogram')
    axes[1, 1].legend()
    
    # 통계
    stats_text = f"""
    DICOM Stats:
    - Mean: {dicom_slice.mean():.2f}
    - Std: {dicom_slice.std():.2f}
    - Min: {dicom_slice.min():.2f}
    - Max: {dicom_slice.max():.2f}
    
    NIfTI Stats:
    - Mean: {nifti_slice.mean():.2f}
    - Std: {nifti_slice.std():.2f}
    - Min: {nifti_slice.min():.2f}
    - Max: {nifti_slice.max():.2f}
    
    Difference:
    - MAE: {diff.mean():.4f}
    - Max Diff: {diff.max():.4f}
    """
    axes[1, 2].text(0.1, 0.5, stats_text, fontsize=10, family='monospace')
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_dir / f'comparison_slice_{slice_idx:03d}.png', dpi=150)
    plt.close()
    
    # 메트릭 반환
    return {
        'slice_idx': slice_idx,
        'mae': float(diff.mean()),
        'max_diff': float(diff.max()),
        'correlation': float(np.corrcoef(dicom_slice.flatten(), nifti_slice.flatten())[0, 1])
    }


def compare_with_reference_images(nifti_data, reference_dir, output_dir):
    """참조 이미지와 비교"""
    reference_dir = Path(reference_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    reference_images = sorted(list(reference_dir.glob("*.png")))
    
    if not reference_images:
        print(f"No reference images found in {reference_dir}")
        return
    
    print(f"\nFound {len(reference_images)} reference images")
    
    # 각 참조 이미지와 비교
    for ref_img_path in reference_images[:5]:  # 처음 5개만 비교
        ref_img = Image.open(ref_img_path)
        ref_array = np.array(ref_img.convert('L'))  # 그레이스케일 변환
        
        print(f"\nReference image: {ref_img_path.name}")
        print(f"Size: {ref_img.size}")
        print(f"Array shape: {ref_array.shape}")
        
        # 시각화
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        
        axes[0].imshow(ref_array, cmap='gray')
        axes[0].set_title(f'Reference: {ref_img_path.name}')
        axes[0].axis('off')
        
        # NIfTI 중간 슬라이스 (예시)
        mid_slice = nifti_data.shape[0] // 2
        axes[1].imshow(nifti_data[mid_slice, :, :], cmap='gray')
        axes[1].set_title(f'NIfTI Slice {mid_slice}')
        axes[1].axis('off')
        
        plt.tight_layout()
        plt.savefig(output_dir / f'ref_comparison_{ref_img_path.stem}.png', dpi=150)
        plt.close()


def validate_metrics(metrics_file):
    """계산된 메트릭 검증"""
    if not Path(metrics_file).exists():
        print(f"Metrics file not found: {metrics_file}")
        return
    
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    print("\n" + "="*60)
    print("CALCULATED METRICS VALIDATION")
    print("="*60)
    
    for key, value in metrics.items():
        print(f"{key}: {value}")
    
    # 메트릭 범위 검증
    validations = []
    
    # Tmax threshold (일반적으로 6초 이상이 비정상)
    if 'tmax_threshold' in metrics:
        validations.append({
            'metric': 'Tmax > 6s',
            'value': metrics['tmax_threshold'],
            'expected': 'Should be reasonable percentage',
            'status': 'OK' if 0 <= metrics['tmax_threshold'] <= 100 else 'WARNING'
        })
    
    # Infarct core (일반적으로 작아야 함)
    if 'infarct_core_volume_voxels' in metrics:
        validations.append({
            'metric': 'Infarct Core Volume',
            'value': metrics['infarct_core_volume_voxels'],
            'expected': 'Should be smaller than penumbra',
            'status': 'OK'
        })
    
    print("\n" + "="*60)
    print("VALIDATION RESULTS")
    print("="*60)
    for v in validations:
        print(f"{v['metric']}: {v['value']} - {v['status']}")
        print(f"  Expected: {v['expected']}")


def main():
    parser = argparse.ArgumentParser(description="Validate visualization accuracy")
    parser.add_argument("--dicom_dir", required=True, help="Original DICOM directory")
    parser.add_argument("--nifti_file", required=True, help="Generated NIfTI file")
    parser.add_argument("--reference_dir", help="Reference images directory")
    parser.add_argument("--metrics_file", help="Metrics JSON file")
    parser.add_argument("--output_dir", default="validation_results", help="Output directory")
    parser.add_argument("--slices", nargs='+', type=int, help="Specific slices to compare")
    
    args = parser.parse_args()
    
    print("="*60)
    print("CT PERFUSION VISUALIZATION VALIDATION")
    print("="*60)
    
    # DICOM 로드
    print("\n[1] Loading DICOM series...")
    dicom_volume, dicom_slices = load_dicom_series(args.dicom_dir)
    
    # NIfTI 로드
    print("\n[2] Loading NIfTI file...")
    nifti_data = load_nifti_file(Path(args.nifti_file))
    
    # 슬라이스 비교
    print("\n[3] Comparing slices...")
    slices_to_compare = args.slices if args.slices else [
        dicom_volume.shape[0] // 4,
        dicom_volume.shape[0] // 2,
        3 * dicom_volume.shape[0] // 4
    ]
    
    results = []
    for slice_idx in slices_to_compare:
        if slice_idx < dicom_volume.shape[0]:
            result = compare_slices(dicom_volume, nifti_data, slice_idx, args.output_dir)
            results.append(result)
            print(f"  Slice {slice_idx}: MAE={result['mae']:.4f}, Corr={result['correlation']:.4f}")
    
    # 참조 이미지 비교
    if args.reference_dir:
        print("\n[4] Comparing with reference images...")
        compare_with_reference_images(nifti_data, args.reference_dir, args.output_dir)
    
    # 메트릭 검증
    if args.metrics_file:
        print("\n[5] Validating metrics...")
        validate_metrics(args.metrics_file)
    
    # 결과 요약
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    avg_mae = np.mean([r['mae'] for r in results])
    avg_corr = np.mean([r['correlation'] for r in results])
    
    print(f"Average MAE: {avg_mae:.4f}")
    print(f"Average Correlation: {avg_corr:.4f}")
    
    if avg_mae < 0.1 and avg_corr > 0.9:
        print("\n✅ VALIDATION PASSED - High accuracy!")
    elif avg_mae < 0.2 and avg_corr > 0.8:
        print("\n⚠️  VALIDATION WARNING - Moderate accuracy")
    else:
        print("\n❌ VALIDATION FAILED - Low accuracy")
    
    print(f"\nResults saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
