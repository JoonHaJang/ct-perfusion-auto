#!/usr/bin/env python3
"""
DICOM에서 실제 Tmax 수치 데이터 추출
RGB 이미지에서 원본 값 복원 시도
"""
import pydicom
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.cm as cm


def rgb_to_value_jet_colormap(rgb_array):
    """
    Jet colormap으로 인코딩된 RGB를 원본 값으로 역변환
    
    Jet colormap:
    - Blue (0, 0, 255) = 낮은 값
    - Cyan (0, 255, 255) = 중간-낮음
    - Green (0, 255, 0) = 중간
    - Yellow (255, 255, 0) = 중간-높음
    - Red (255, 0, 0) = 높은 값
    """
    # RGB를 0-1 범위로 정규화
    r = rgb_array[:, :, 0].astype(float) / 255.0
    g = rgb_array[:, :, 1].astype(float) / 255.0
    b = rgb_array[:, :, 2].astype(float) / 255.0
    
    # Jet colormap 근사 역변환
    # 휴리스틱 방법: RGB 채널의 가중 평균
    
    # 방법 1: 단순 가중 평균
    value_simple = 0.299 * r + 0.587 * g + 0.114 * b
    
    # 방법 2: Jet colormap 특성 활용
    # Blue가 높으면 낮은 값, Red가 높으면 높은 값
    value_jet = r - b + 0.5
    value_jet = np.clip(value_jet, 0, 1)
    
    # 방법 3: 색상(Hue) 기반
    # RGB를 HSV로 변환하여 Hue 사용
    max_rgb = np.maximum(np.maximum(r, g), b)
    min_rgb = np.minimum(np.minimum(r, g), b)
    delta = max_rgb - min_rgb
    
    hue = np.zeros_like(r)
    mask = delta > 0
    
    # Red가 최대
    mask_r = (max_rgb == r) & mask
    hue[mask_r] = 60 * (((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6)
    
    # Green이 최대
    mask_g = (max_rgb == g) & mask
    hue[mask_g] = 60 * (((b[mask_g] - r[mask_g]) / delta[mask_g]) + 2)
    
    # Blue가 최대
    mask_b = (max_rgb == b) & mask
    hue[mask_b] = 60 * (((r[mask_b] - g[mask_b]) / delta[mask_b]) + 4)
    
    # Jet colormap에서 Hue 범위: 240(blue) -> 0(red)
    # 정규화: 0(낮음) -> 1(높음)
    value_hue = 1.0 - (hue / 240.0)
    value_hue = np.clip(value_hue, 0, 1)
    
    return value_simple, value_jet, value_hue


def extract_from_lookup_table(ds):
    """DICOM Lookup Table에서 원본 값 추출 시도"""
    # Palette Color Lookup Table
    if hasattr(ds, 'RedPaletteColorLookupTableData'):
        print("  Found Palette Color Lookup Table")
        return True
    
    # VOI LUT (Value of Interest)
    if hasattr(ds, 'VOILUTSequence'):
        print("  Found VOI LUT Sequence")
        return True
    
    return False


def check_private_tags_for_data(ds):
    """Private Tags에서 원본 데이터 확인"""
    print("\n🔍 Searching for original data in Private Tags...")
    
    for elem in ds:
        if elem.tag.is_private:
            # 큰 데이터 배열 찾기
            if hasattr(elem, 'value'):
                if isinstance(elem.value, bytes) and len(elem.value) > 10000:
                    print(f"  Found large private data: {elem.tag}, Size: {len(elem.value)} bytes")
                    
                    # Float 배열로 해석 시도
                    try:
                        float_array = np.frombuffer(elem.value, dtype=np.float32)
                        if len(float_array) > 100:
                            print(f"    As float32: {len(float_array)} values")
                            print(f"    Range: [{float_array.min():.4f}, {float_array.max():.4f}]")
                            return float_array
                    except:
                        pass
                    
                    # Int 배열로 해석 시도
                    try:
                        int_array = np.frombuffer(elem.value, dtype=np.int16)
                        if len(int_array) > 100:
                            print(f"    As int16: {len(int_array)} values")
                            print(f"    Range: [{int_array.min()}, {int_array.max()}]")
                    except:
                        pass
    
    return None


def compare_extraction_methods(dcm_file, output_dir):
    """여러 추출 방법 비교"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ds = pydicom.dcmread(dcm_file)
    rgb_array = ds.pixel_array
    
    print(f"\n{'='*60}")
    print(f"Analyzing: {dcm_file.name}")
    print(f"{'='*60}")
    
    # Private tags 확인
    private_data = check_private_tags_for_data(ds)
    
    # RGB 역변환
    print("\n🎨 RGB to Value Conversion...")
    value_simple, value_jet, value_hue = rgb_to_value_jet_colormap(rgb_array)
    
    # 시각화
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # 원본 RGB
    axes[0, 0].imshow(rgb_array)
    axes[0, 0].set_title('Original RGB', fontsize=14, fontweight='bold')
    axes[0, 0].axis('off')
    
    # 방법 1: 단순 가중 평균
    im1 = axes[0, 1].imshow(value_simple, cmap='jet', vmin=0, vmax=1)
    axes[0, 1].set_title('Method 1: Weighted Average', fontsize=14, fontweight='bold')
    axes[0, 1].axis('off')
    plt.colorbar(im1, ax=axes[0, 1], fraction=0.046)
    
    # 방법 2: Jet 특성 활용
    im2 = axes[0, 2].imshow(value_jet, cmap='jet', vmin=0, vmax=1)
    axes[0, 2].set_title('Method 2: R-B Difference', fontsize=14, fontweight='bold')
    axes[0, 2].axis('off')
    plt.colorbar(im2, ax=axes[0, 2], fraction=0.046)
    
    # 방법 3: Hue 기반
    im3 = axes[1, 0].imshow(value_hue, cmap='jet', vmin=0, vmax=1)
    axes[1, 0].set_title('Method 3: Hue-based', fontsize=14, fontweight='bold')
    axes[1, 0].axis('off')
    plt.colorbar(im3, ax=axes[1, 0], fraction=0.046)
    
    # 히스토그램 비교
    axes[1, 1].hist(value_simple.flatten(), bins=50, alpha=0.5, label='Method 1', color='blue')
    axes[1, 1].hist(value_jet.flatten(), bins=50, alpha=0.5, label='Method 2', color='red')
    axes[1, 1].hist(value_hue.flatten(), bins=50, alpha=0.5, label='Method 3', color='green')
    axes[1, 1].set_title('Value Distribution', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('Normalized Value (0-1)')
    axes[1, 1].set_ylabel('Frequency')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    # 통계
    stats_text = f"""
    EXTRACTION STATISTICS
    
    Method 1 (Weighted Avg):
      Mean:  {value_simple.mean():.4f}
      Std:   {value_simple.std():.4f}
      Range: [{value_simple.min():.4f}, {value_simple.max():.4f}]
    
    Method 2 (R-B Diff):
      Mean:  {value_jet.mean():.4f}
      Std:   {value_jet.std():.4f}
      Range: [{value_jet.min():.4f}, {value_jet.max():.4f}]
    
    Method 3 (Hue):
      Mean:  {value_hue.mean():.4f}
      Std:   {value_hue.std():.4f}
      Range: [{value_hue.min():.4f}, {value_hue.max():.4f}]
    
    Expected Tmax Range: 0-12 seconds
    Scaling needed: value * 12
    """
    axes[1, 2].text(0.05, 0.5, stats_text, fontsize=10, family='monospace',
                    va='center', transform=axes[1, 2].transAxes)
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_dir / f'extraction_comparison_{dcm_file.stem}.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\nSaved: {output_dir / f'extraction_comparison_{dcm_file.stem}.png'}")
    
    # 가장 적합한 방법 추천
    print(f"\n💡 Recommendation:")
    print(f"   Method 3 (Hue-based) is likely most accurate for Jet colormap")
    print(f"   Estimated Tmax range: 0 to {value_hue.max() * 12:.2f} seconds")
    
    return value_hue


def main():
    dicom_dir = Path(r"C:\Users\USER\Desktop\의료 저널\Research\CTP_MT\487460_안연순_20240423225748")
    output_dir = Path(r"C:\Users\USER\Desktop\의료 저널\ct-perfusion-auto\data_extraction")
    
    print("="*60)
    print("EXTRACTING REAL DATA FROM RGB DICOM")
    print("="*60)
    
    # TMAXD 파일 찾기
    tmaxd_files = []
    for dcm_file in dicom_dir.glob("*.dcm"):
        ds = pydicom.dcmread(dcm_file)
        if "TMAXD" in ds.get('SeriesDescription', ''):
            tmaxd_files.append(dcm_file)
    
    if not tmaxd_files:
        print("TMAXD 파일을 찾을 수 없습니다.")
        return
    
    print(f"\nFound {len(tmaxd_files)} TMAXD files")
    
    # 여러 슬라이스 분석
    test_indices = [0, len(tmaxd_files)//4, len(tmaxd_files)//2, 3*len(tmaxd_files)//4]
    
    for idx in test_indices:
        if idx < len(tmaxd_files):
            dcm_file = sorted(tmaxd_files)[idx]
            extracted_values = compare_extraction_methods(dcm_file, output_dir)
    
    print("\n" + "="*60)
    print("EXTRACTION COMPLETE")
    print("="*60)
    print(f"\n결과 확인: {output_dir}")
    print("\n다음 단계:")
    print("1. 추출된 값과 NIfTI 비교")
    print("2. 가장 정확한 추출 방법 선택")
    print("3. 전체 볼륨 재구성")


if __name__ == "__main__":
    main()
