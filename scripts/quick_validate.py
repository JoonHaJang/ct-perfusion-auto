#!/usr/bin/env python3
"""
Quick DICOM Validation - 참조 이미지와 DICOM 비교
"""
import pydicom
import numpy as np
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.cm as cm


def load_dicom_info(dicom_dir):
    """DICOM 파일 정보 확인"""
    dicom_files = sorted(list(Path(dicom_dir).glob("*.dcm")))
    
    print("="*60)
    print("DICOM FILES ANALYSIS")
    print("="*60)
    print(f"Total DICOM files: {len(dicom_files)}")
    
    # 첫 번째 파일 분석
    first_ds = pydicom.dcmread(dicom_files[0])
    
    print(f"\nPatient Name: {first_ds.get('PatientName', 'N/A')}")
    print(f"Study Date: {first_ds.get('StudyDate', 'N/A')}")
    print(f"Series Description: {first_ds.get('SeriesDescription', 'N/A')}")
    print(f"Modality: {first_ds.get('Modality', 'N/A')}")
    print(f"Image Type: {first_ds.get('ImageType', 'N/A')}")
    
    # 이미지 크기
    print(f"\nImage Size: {first_ds.Rows} x {first_ds.Columns}")
    print(f"Pixel Spacing: {first_ds.get('PixelSpacing', 'N/A')}")
    print(f"Slice Thickness: {first_ds.get('SliceThickness', 'N/A')}")
    
    # 여러 시리즈 확인
    series_descriptions = set()
    for dcm_file in dicom_files[:50]:  # 처음 50개만 확인
        ds = pydicom.dcmread(dcm_file)
        series_desc = ds.get('SeriesDescription', 'Unknown')
        series_descriptions.add(series_desc)
    
    print(f"\nFound {len(series_descriptions)} different series:")
    for desc in series_descriptions:
        print(f"  - {desc}")
    
    return dicom_files


def visualize_dicom_sample(dicom_files, output_dir):
    """DICOM 샘플 시각화"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("VISUALIZING DICOM SAMPLES")
    print("="*60)
    
    # 여러 슬라이스 시각화
    indices = [0, len(dicom_files)//4, len(dicom_files)//2, 3*len(dicom_files)//4, len(dicom_files)-1]
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for i, idx in enumerate(indices):
        if idx < len(dicom_files):
            ds = pydicom.dcmread(dicom_files[idx])
            img = ds.pixel_array
            
            # 정규화
            img_norm = (img - img.min()) / (img.max() - img.min() + 1e-8)
            
            axes[i].imshow(img_norm, cmap='gray')
            axes[i].set_title(f'Slice {idx}\n{ds.get("SeriesDescription", "Unknown")}')
            axes[i].axis('off')
            
            print(f"Slice {idx}: Shape={img.shape}, Range=[{img.min():.2f}, {img.max():.2f}]")
    
    # 통계
    stats_text = f"""
    DICOM Statistics:
    - Total files: {len(dicom_files)}
    - Image size: {ds.Rows}x{ds.Columns}
    - Pixel spacing: {ds.get('PixelSpacing', 'N/A')}
    """
    axes[5].text(0.1, 0.5, stats_text, fontsize=12, family='monospace')
    axes[5].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'dicom_samples.png', dpi=150, bbox_inches='tight')
    print(f"\nSaved: {output_dir / 'dicom_samples.png'}")
    plt.close()


def compare_with_reference(dicom_files, reference_dir, output_dir):
    """참조 이미지와 비교"""
    reference_dir = Path(reference_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ref_images = sorted(list(reference_dir.glob("*.png")))
    
    print("\n" + "="*60)
    print("COMPARING WITH REFERENCE IMAGES")
    print("="*60)
    print(f"Found {len(ref_images)} reference images")
    
    # 중간 슬라이스 선택
    mid_idx = len(dicom_files) // 2
    
    # DICOM 로드
    ds = pydicom.dcmread(dicom_files[mid_idx])
    dicom_img = ds.pixel_array
    dicom_norm = (dicom_img - dicom_img.min()) / (dicom_img.max() - dicom_img.min() + 1e-8)
    
    # 참조 이미지 (중간 것 선택)
    ref_img_path = ref_images[len(ref_images)//2]
    ref_img = Image.open(ref_img_path)
    ref_array = np.array(ref_img.convert('L')) / 255.0
    
    # 비교 시각화
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    axes[0].imshow(dicom_norm, cmap='gray')
    axes[0].set_title(f'DICOM Slice {mid_idx}\\n{ds.get("SeriesDescription", "Unknown")}')
    axes[0].axis('off')
    
    axes[1].imshow(ref_array, cmap='gray')
    axes[1].set_title(f'Reference Image\\n{ref_img_path.name}')
    axes[1].axis('off')
    
    # 정보
    info_text = f"""
    DICOM Info:
    - File: {dicom_files[mid_idx].name}
    - Series: {ds.get('SeriesDescription', 'Unknown')}
    - Size: {dicom_img.shape}
    - Range: [{dicom_img.min():.2f}, {dicom_img.max():.2f}]
    
    Reference Info:
    - File: {ref_img_path.name}
    - Size: {ref_img.size}
    - Array shape: {ref_array.shape}
    
    Note:
    참조 이미지는 외부 뷰어에서 캡처한 것으로
    우리가 생성한 시각화와 비교하여
    정확도를 검증해야 합니다.
    """
    axes[2].text(0.05, 0.5, info_text, fontsize=11, family='monospace', va='center')
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'reference_comparison.png', dpi=150, bbox_inches='tight')
    print(f"\nSaved: {output_dir / 'reference_comparison.png'}")
    plt.close()


def main():
    print("="*60)
    print("CT PERFUSION QUICK VALIDATION")
    print("="*60)
    
    # 경로 설정
    dicom_dir = r"C:\Users\USER\Desktop\의료 저널\Research\CTP_MT\487460_안연순_20240423225748"
    reference_dir = r"C:\Users\USER\Desktop\의료 저널\ct-perfusion-auto\참조"
    output_dir = r"C:\Users\USER\Desktop\의료 저널\ct-perfusion-auto\validation_results"
    
    # DICOM 분석
    dicom_files = load_dicom_info(dicom_dir)
    
    # DICOM 샘플 시각화
    visualize_dicom_sample(dicom_files, output_dir)
    
    # 참조 이미지와 비교
    compare_with_reference(dicom_files, reference_dir, output_dir)
    
    print("\n" + "="*60)
    print("VALIDATION COMPLETE")
    print("="*60)
    print(f"\n결과 확인: {output_dir}")
    print("\n다음 단계:")
    print("1. GUI를 통해 전체 분석 실행")
    print("2. 생성된 NIfTI 파일과 시각화 확인")
    print("3. 참조 이미지와 정확도 비교")


if __name__ == "__main__":
    main()
