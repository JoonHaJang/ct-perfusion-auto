#!/usr/bin/env python3
"""
Siemens CT Perfusion DICOM에서 직접 지표 추출
RGB → Scalar 변환 후 Infarct Core / Penumbra 계산
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pydicom
from collections import defaultdict


def rgb_to_scalar_siemens_time(r, g, b):
    """
    Siemens CT Perfusion RGB를 스칼라 값으로 변환 (Time 계열: Tmax, MTT, TTP)
    Based on: https://github.com/neurolabusc/rgb2scalar
    
    Siemens uses a segmented non-linear color scheme with 254 distinct values.
    This function implements the exact reverse mapping from RGB to scalar intensity.
    
    Args:
        r, g, b: Red, Green, Blue channels (0-255)
    
    Returns:
        Scalar intensity (0-254 range, needs to be scaled to actual units)
    """
    # Initialize output
    s = np.zeros_like(r, dtype=float)
    
    # Segment 1: Blue > 0, Green <= 64 (indices 1-63)
    # Blue ramps up while green increases slowly
    mask1 = (g <= 64) & (b > 0)
    s[mask1] = (-r[mask1] + g[mask1] + b[mask1] + 4) * 0.245
    
    # Segment 2: Blue > 0, Green > 64 (indices 64-127)
    # Transition from blue to cyan to green
    mask2 = (g > 64) & (b > 0)
    s[mask2] = ((-r[mask2] + g[mask2] - b[mask2]) * 0.125786164) + 95.3
    
    # Segment 3: Blue = 0, Green > 252 (indices 128-191)
    # Red ramps up while green stays high
    mask3 = (g > 252) & (b == 0)
    s[mask3] = (r[mask3] * 0.252) + 127.75
    
    # Segment 4: Blue = 0, R > 252 (indices 192-254)
    # Green decays while red stays high
    mask4 = (r > 252) & (b == 0)
    s[mask4] = ((255 - g[mask4]) * 0.247) + 191.75
    
    # Set background pixels to 0 (including noisy black pixels)
    # RGB 합이 10 미만인 픽셀은 배경으로 간주 (노이즈 제거)
    background_mask = (r + g + b) < 10
    s[background_mask] = 0
    
    # Clamp negative values
    s[s < 0] = 0
    
    return s


def rgb_to_scalar_siemens_flow(r, g, b):
    """
    Siemens CT Perfusion RGB를 스칼라 값으로 변환 (Flow/Volume 계열: CBF, CBV)
    Based on: https://github.com/neurolabusc/rgb2scalar
    
    Args:
        r, g, b: Red, Green, Blue channels (0-255)
    
    Returns:
        Scalar intensity (0-254 range, needs to be scaled to actual units)
    """
    # Initialize output
    s = np.zeros_like(r, dtype=float)
    
    # Segment 1: indices 1-22
    # Red and blue ramp up together
    mask1 = (g <= 1)
    s[mask1] = (r[mask1] + b[mask1] - 122) * (22.0 / 68.0)
    
    # Segment 2: indices 23-42
    # Complex transition region
    mask2 = (r > g) & (b > g)
    s[mask2] = ((-r[mask2] + b[mask2] + g[mask2] - 4) * (19.0 / 122.0)) + 23
    
    # Segment 3: indices 42-78
    # Green equals red
    mask3 = (g == r)
    s[mask3] = ((b[mask3] - 130) * (35.0 / 123.0)) + 43
    
    # Segment 4: indices 79-158
    # Green dominates
    mask4 = (g > r) & (b > 0)
    s[mask4] = ((r[mask4] + g[mask4] - b[mask4] + 124) * (79.0 / 503.0)) + 79
    
    # Segment 5: indices 159-229
    # Blue drops to zero
    mask5 = (b < 1)
    s[mask5] = ((r[mask5] - 128) * (70.0 / 126.0)) + 159
    
    # Segment 6: indices 230-254
    # Final high intensity region
    mask6 = (r > g) & (r > b)
    s[mask6] = ((-r[mask6] - g[mask6] + b[mask6] + 495) * (24.0 / 270.0)) + 230
    
    # Set background pixels to 0 (including noisy black pixels)
    # RGB 합이 10 미만인 픽셀은 배경으로 간주 (노이즈 제거)
    background_mask = (r + g + b) < 10
    s[background_mask] = 0
    
    # Clamp negative values
    s[s < 0] = 0
    
    return s


def rgb_to_scalar_siemens(rgb_array, max_value=12.0, is_time_series=True):
    """
    Siemens CT Perfusion RGB를 스칼라 값으로 변환 (통합 인터페이스)
    Based on: https://github.com/neurolabusc/rgb2scalar
    
    Args:
        rgb_array: RGB image array (H x W x 3)
        max_value: Maximum value in the actual units (e.g., 12.0 for Tmax in seconds)
        is_time_series: True for Tmax/MTT/TTP, False for CBF/CBV
    
    Returns:
        Scalar array in actual units
    """
    r = rgb_array[:, :, 0].astype(float)
    g = rgb_array[:, :, 1].astype(float)
    b = rgb_array[:, :, 2].astype(float)
    
    # Apply appropriate conversion
    if is_time_series:
        scalar_0_254 = rgb_to_scalar_siemens_time(r, g, b)
    else:
        scalar_0_254 = rgb_to_scalar_siemens_flow(r, g, b)
    
    # Scale to actual units
    # Siemens uses 254 distinct colors (indices 1-254, with 0 for black)
    max_index = np.max(scalar_0_254[scalar_0_254 > 0]) if np.any(scalar_0_254 > 0) else 254.0
    
    # Scale to target range
    scalar_value = (scalar_0_254 / max_index) * max_value
    
    return scalar_value


def get_pixel_spacing_from_dicom(ds):
    """
    DICOM 메타데이터에서 실제 pixel spacing 추출
    
    Args:
        ds: pydicom Dataset
    
    Returns:
        [x_spacing, y_spacing, z_spacing] in mm
    """
    try:
        # In-plane spacing (X, Y)
        if hasattr(ds, 'PixelSpacing') and ds.PixelSpacing:
            xy_spacing = [float(ds.PixelSpacing[0]), float(ds.PixelSpacing[1])]
        elif hasattr(ds, 'ImagerPixelSpacing') and ds.ImagerPixelSpacing:
            xy_spacing = [float(ds.ImagerPixelSpacing[0]), float(ds.ImagerPixelSpacing[1])]
        else:
            print("  Warning: PixelSpacing not found, using default [0.5, 0.5] mm")
            xy_spacing = [0.5, 0.5]
        
        # Slice thickness (Z)
        if hasattr(ds, 'SliceThickness') and ds.SliceThickness:
            z_spacing = float(ds.SliceThickness)
        elif hasattr(ds, 'SpacingBetweenSlices') and ds.SpacingBetweenSlices:
            z_spacing = float(ds.SpacingBetweenSlices)
        else:
            print("  Warning: SliceThickness not found, using default 3.0 mm")
            z_spacing = 3.0
        
        return xy_spacing + [z_spacing]
    except Exception as e:
        print(f"  Error extracting pixel spacing: {e}")
        print("  Using default spacing [0.5, 0.5, 3.0] mm")
        return [0.5, 0.5, 3.0]


def load_perfusion_volume(dicom_dir, series_keyword):
    """
    특정 Perfusion 시리즈를 3D 볼륨으로 로드
    
    Args:
        dicom_dir: DICOM 디렉토리
        series_keyword: 시리즈 키워드 (예: "TMAXD", "CBVD", "CBFD")
    
    Returns:
        volume: 3D numpy array
        metadata: 시리즈 메타데이터
    """
    dicom_files = []
    
    # 해당 시리즈 파일 찾기
    for dcm_file in Path(dicom_dir).glob("*.dcm"):
        try:
            ds = pydicom.dcmread(dcm_file, stop_before_pixels=True)
            series_desc = ds.get('SeriesDescription', '')
            
            if series_keyword.upper() in series_desc.upper():
                z_pos = float(ds.ImagePositionPatient[2]) if hasattr(ds, 'ImagePositionPatient') else 0
                dicom_files.append((z_pos, dcm_file, ds))
        except:
            continue
    
    if not dicom_files:
        raise ValueError(f"No {series_keyword} series found in {dicom_dir}")
    
    # Z 위치로 정렬
    dicom_files.sort(key=lambda x: x[0])
    
    print(f"Found {len(dicom_files)} slices for {series_keyword}")
    if len(dicom_files) > 0:
        print(f"  Z-position range: {dicom_files[0][0]:.2f} (slice 0) → {dicom_files[-1][0]:.2f} (slice {len(dicom_files)-1})")
    
    # 첫 번째 슬라이스로 크기 및 spacing 확인
    first_ds = pydicom.dcmread(dicom_files[0][1])
    first_pixel = first_ds.pixel_array
    
    # Pixel spacing 추출
    pixel_spacing = get_pixel_spacing_from_dicom(first_ds)
    print(f"  Pixel spacing: {pixel_spacing[0]:.2f} x {pixel_spacing[1]:.2f} x {pixel_spacing[2]:.2f} mm")
    
    # RGB 확인
    is_rgb = len(first_pixel.shape) == 3 and first_pixel.shape[-1] == 3
    
    if is_rgb:
        # RGB → Scalar 변환
        print(f"Converting RGB to scalar for {series_keyword}...")
        
        # 최대값 및 변환 타입 결정
        max_value = 12.0  # Default for Tmax
        is_time_series = True  # Default for time-based maps
        
        if "CBV" in series_keyword.upper():
            max_value = 100.0
            is_time_series = False  # CBV uses flow/volume conversion
        elif "CBF" in series_keyword.upper():
            max_value = 100.0
            is_time_series = False  # CBF uses flow/volume conversion
        elif "MTT" in series_keyword.upper() or "TTP" in series_keyword.upper():
            max_value = 15.0
            is_time_series = True  # MTT/TTP use time series conversion
        # Tmax uses default: max_value=12.0, is_time_series=True
        
        print(f"  Using {'TIME' if is_time_series else 'FLOW/VOLUME'} series conversion (max={max_value})")
        
        volume = np.zeros((len(dicom_files), first_pixel.shape[0], first_pixel.shape[1]))
        
        for i, (z_pos, fpath, _) in enumerate(dicom_files):
            ds = pydicom.dcmread(fpath)
            rgb = ds.pixel_array
            scalar = rgb_to_scalar_siemens(rgb, max_value, is_time_series)
            volume[i, :, :] = scalar
    else:
        # 이미 스칼라
        volume = np.zeros((len(dicom_files), first_pixel.shape[0], first_pixel.shape[1]))
        
        for i, (z_pos, fpath, _) in enumerate(dicom_files):
            ds = pydicom.dcmread(fpath)
            volume[i, :, :] = ds.pixel_array
    
    # 메타데이터 (pixel_spacing 포함)
    metadata = {
        "series_description": dicom_files[0][2].get('SeriesDescription', ''),
        "series_number": dicom_files[0][2].get('SeriesNumber', 0),
        "num_slices": len(dicom_files),
        "shape": list(volume.shape),
        "value_range": [float(volume.min()), float(volume.max())],
        "mean": float(volume.mean()),
        "std": float(volume.std()),
        "pixel_spacing_mm": pixel_spacing  # 실제 DICOM에서 추출한 spacing
    }
    
    return volume, metadata


def calculate_contralateral_cbv(cbv_volume, lesion_mask):
    """대측 정상 피질(회백질) CBV 계산 (논문 기준)
    
    Args:
        cbv_volume: CBV 3D array
        lesion_mask: 병변 마스크 (hypoperfusion)
    
    Returns:
        contralateral_cbv: 대측 피질 평균 CBV
    """
    # 좌우 반전하여 대측 영역 생성
    contralateral_mask = np.flip(lesion_mask, axis=2)  # 좌우 반전
    
    # 피질(회백질) 선택: CBV가 높은 영역 (상위 40-90 percentile)
    # 백질, 뇌실 등 제외
    valid_cbv = cbv_volume[cbv_volume > 0]
    if len(valid_cbv) > 0:
        cbv_low = np.percentile(valid_cbv, 40)   # 백질 제외
        cbv_high = np.percentile(valid_cbv, 90)  # 혈관 제외
        
        # 대측 피질: 병변 반대편 + CBV 중간 범위 + 병변 없음
        cortical_mask = (cbv_volume >= cbv_low) & (cbv_volume <= cbv_high) & contralateral_mask
        
        if np.sum(cortical_mask) > 0:
            contralateral_cbv = np.mean(cbv_volume[cortical_mask])
        else:
            # 대안: 대측 전체 평균
            normal_mask = contralateral_mask & (cbv_volume > 0)
            contralateral_cbv = np.mean(cbv_volume[normal_mask]) if np.sum(normal_mask) > 0 else 1.0
    else:
        contralateral_cbv = 1.0
    
    return float(contralateral_cbv)


def compute_perfusion_metrics(tmax_volume, cbv_volume=None, cbf_volume=None, pixel_spacing=None):
    """
    Perfusion 지표 계산 (논문 기반)
    
    Args:
        tmax_volume: Tmax 3D array (seconds)
        cbv_volume: CBV 3D array (optional)
        cbf_volume: CBF 3D array (optional, for paper-based core definition)
        pixel_spacing: [x, y, z] spacing in mm
    
    Returns:
        metrics: 계산된 지표 딕셔너리
        masks: 마스크 딕셔너리
    """
    # 픽셀 크기 (DICOM에서 추출, 없으면 기본값 사용)
    if pixel_spacing is None:
        print("  ⚠️ Warning: Using default pixel spacing [0.5, 0.5, 3.0] mm")
        pixel_spacing = [0.5, 0.5, 3.0]
    
    voxel_volume_ml = (pixel_spacing[0] * pixel_spacing[1] * pixel_spacing[2]) / 1000.0
    
    # 임계값 정의 (논문 기반)
    TMAX_THRESHOLD_HYPOPERFUSION = 6.0  # seconds
    TMAX_THRESHOLD_CORE = 10.0  # seconds
    CBF_THRESHOLD_RELATIVE = 0.38  # relative CBF < 38% (논문)
    CBV_THRESHOLD_CORE = 2.0  # ml/100g (대안)
    
    # 뇌 마스크 생성 (배경 제외)
    # RGB→Scalar 변환 시 배경(RGB<10)이 이미 0으로 설정되었으므로
    # Tmax > 0 조건만으로도 배경이 제외됨
    brain_mask = tmax_volume > 0.1  # Tmax > 0.1초 (배경 및 노이즈 제외)
    
    # CBV/CBF 데이터가 있으면 추가로 활용하여 더 robust한 마스크 생성
    if cbv_volume is not None:
        cbv_brain_mask = cbv_volume > 0.5  # CBV > 0.5 ml/100g
        brain_mask = brain_mask | cbv_brain_mask  # OR 연산으로 뇌 영역 확장
    if cbf_volume is not None:
        cbf_brain_mask = cbf_volume > 0.5  # CBF > 0.5 ml/100g/min
        brain_mask = brain_mask | cbf_brain_mask  # OR 연산으로 뇌 영역 확장
    
    brain_voxels = np.sum(brain_mask)
    brain_volume_ml = brain_voxels * voxel_volume_ml
    print(f"Brain mask: {brain_voxels} voxels ({brain_volume_ml:.1f} ml)")
    print(f"  Background removed: RGB < 10 → Scalar = 0")
    
    # 마스크 생성 (뇌 영역 내에서만)
    hypoperfusion_mask = brain_mask & (tmax_volume >= TMAX_THRESHOLD_HYPOPERFUSION)
    core_mask_tmax = brain_mask & (tmax_volume >= TMAX_THRESHOLD_CORE)
    
    # Infarct Core 정의 (논문: relative CBF < 38%)
    # ⚠️ Core는 반드시 Hypoperfusion의 부분집합이어야 함!
    if cbf_volume is not None:
        # 대측 정상 CBF 계산
        contralateral_cbf_mask = np.flip(hypoperfusion_mask, axis=2)
        normal_cbf_mask = contralateral_cbf_mask & (cbf_volume > 0)
        
        if np.sum(normal_cbf_mask) > 0:
            normal_cbf = np.mean(cbf_volume[normal_cbf_mask])
            # Relative CBF < 38% AND Tmax ≥6s (hypoperfusion 내에서만)
            relative_cbf = cbf_volume / normal_cbf
            core_mask = hypoperfusion_mask & (relative_cbf < CBF_THRESHOLD_RELATIVE)
        else:
            # CBF 정규화 실패 시 Tmax 사용
            core_mask = core_mask_tmax
    elif cbv_volume is not None:
        # CBV 기반 Core (대안)
        # Tmax ≥10s AND CBV < 2.0 (hypoperfusion 내에서만)
        core_mask = hypoperfusion_mask & core_mask_tmax & (cbv_volume < CBV_THRESHOLD_CORE)
    else:
        # Tmax만 사용 (Tmax ≥10s, hypoperfusion 내에서만)
        core_mask = hypoperfusion_mask & core_mask_tmax
    
    penumbra_mask = hypoperfusion_mask & (~core_mask)
    
    # 부피 계산
    hypoperfusion_volume = np.sum(hypoperfusion_mask) * voxel_volume_ml
    core_volume = np.sum(core_mask) * voxel_volume_ml
    penumbra_volume = np.sum(penumbra_mask) * voxel_volume_ml
    core_volume_tmax10 = np.sum(core_mask_tmax) * voxel_volume_ml
    
    # 기본 지표
    mismatch_ratio = float(hypoperfusion_volume / core_volume) if core_volume > 0 else 0.0
    
    # === 논문 기반 고급 지표 ===
    
    # 1. HIR (Hypoperfusion Intensity Ratio)
    hir = float(core_volume_tmax10 / hypoperfusion_volume) if hypoperfusion_volume > 0 else 0.0
    
    # 2. PVT (Perfusion Volume Threshold) - Tmax >6s 절대 볼륨
    pvt = float(hypoperfusion_volume)
    
    # 3. PRR (Penumbral Rescue Ratio) - 구제 가능 조직 비율
    # PRR = Penumbra Volume / Hypoperfusion Volume (논문 정의)
    prr = float(penumbra_volume / hypoperfusion_volume) if hypoperfusion_volume > 0 else 0.0
    
    # 4. CBV Index 계산 (CBV가 있을 때만)
    corrected_cbv_index = None
    conventional_cbv_index = None
    contralateral_cbv = None
    
    if cbv_volume is not None:
        # 대측 정상 피질 CBV
        contralateral_cbv = calculate_contralateral_cbv(cbv_volume, hypoperfusion_mask)
        
        # Corrected CBV Index: Tmax >6s 영역 내 평균 CBV / 대측 CBV
        lesion_cbv_tmax_masked = cbv_volume[hypoperfusion_mask]
        if len(lesion_cbv_tmax_masked) > 0 and contralateral_cbv > 0:
            mean_lesion_cbv_corrected = np.mean(lesion_cbv_tmax_masked)
            corrected_cbv_index = float(mean_lesion_cbv_corrected / contralateral_cbv)
        
        # Conventional CBV Index: 병변 영역 평균 CBV / 대측 CBV (Tmax 마스킹 없음, 논문 기준)
        # 병변 영역 = CBV가 낮은 영역 (하위 30-40 percentile)
        valid_cbv = cbv_volume[cbv_volume > 0]
        
        if len(valid_cbv) > 0:
            # CBV 낮은 영역을 병변으로 정의 (하위 35%)
            cbv_lesion_threshold = np.percentile(valid_cbv, 35)
            
            # 병변 영역: CBV가 낮고, 병변 반구에 있는 영역
            midline = cbv_volume.shape[2] // 2
            left_hypoperfusion = np.sum(hypoperfusion_mask[:, :, :midline])
            right_hypoperfusion = np.sum(hypoperfusion_mask[:, :, midline:])
            
            if left_hypoperfusion > right_hypoperfusion:
                # 왼쪽 반구가 병변
                hemisphere_mask = np.zeros_like(cbv_volume, dtype=bool)
                hemisphere_mask[:, :, :midline] = True
            else:
                # 오른쪽 반구가 병변
                hemisphere_mask = np.zeros_like(cbv_volume, dtype=bool)
                hemisphere_mask[:, :, midline:] = True
            
            # Conventional 병변: CBV 낮음 + 병변 반구
            conventional_lesion_mask = (cbv_volume > 0) & (cbv_volume <= cbv_lesion_threshold) & hemisphere_mask
            
            if np.sum(conventional_lesion_mask) > 0 and contralateral_cbv > 0:
                mean_lesion_cbv_conventional = np.mean(cbv_volume[conventional_lesion_mask])
                conventional_cbv_index = float(mean_lesion_cbv_conventional / contralateral_cbv)
            else:
                conventional_cbv_index = corrected_cbv_index
        else:
            conventional_cbv_index = corrected_cbv_index
    
    # 슬라이스별 통계
    slice_stats = []
    for i in range(tmax_volume.shape[0]):
        slice_core = np.sum(core_mask[i, :, :]) * (pixel_spacing[0] * pixel_spacing[1]) / 100.0
        slice_penumbra = np.sum(penumbra_mask[i, :, :]) * (pixel_spacing[0] * pixel_spacing[1]) / 100.0
        
        slice_stats.append({
            "slice_index": i,
            "core_area_cm2": float(slice_core),
            "penumbra_area_cm2": float(slice_penumbra),
            "total_area_cm2": float(slice_core + slice_penumbra)
        })
    
    # 측부순환 등급 예측 (Corrected CBV Index 기반)
    collateral_grade = None
    if corrected_cbv_index is not None:
        if corrected_cbv_index >= 0.70:
            collateral_grade = "Good (ASITN/SIR 3-4)"
        else:
            collateral_grade = "Poor (ASITN/SIR 0-2)"
    
    # 전체 지표
    metrics = {
        # 기본 지표
        "hypoperfusion_volume_ml": float(hypoperfusion_volume),
        "infarct_core_volume_ml": float(core_volume),
        "penumbra_volume_ml": float(penumbra_volume),
        "mismatch_ratio": mismatch_ratio,
        "mismatch_volume_ml": float(penumbra_volume),
        
        # 논문 기반 고급 지표
        "hir": hir,
        "pvt_ml": pvt,
        "prr": prr,
        "corrected_cbv_index": corrected_cbv_index,
        "conventional_cbv_index": conventional_cbv_index,
        "contralateral_cbv": contralateral_cbv,
        "collateral_grade": collateral_grade,
        
        # 메타데이터
        "thresholds": {
            "tmax_hypoperfusion_sec": TMAX_THRESHOLD_HYPOPERFUSION,
            "tmax_core_sec": TMAX_THRESHOLD_CORE,
            "cbv_core_ml_per_100g": CBV_THRESHOLD_CORE if cbv_volume is not None else None,
            "corrected_cbv_index_cutoff": 0.70
        },
        "pixel_spacing_mm": pixel_spacing,
        "voxel_volume_ml": float(voxel_volume_ml),
        "slice_statistics": slice_stats
    }
    
    masks = {
        "hypoperfusion": hypoperfusion_mask.astype(np.uint8),
        "core": core_mask.astype(np.uint8),
        "penumbra": penumbra_mask.astype(np.uint8)
    }
    
    return metrics, masks


def main():
    parser = argparse.ArgumentParser(description="Extract perfusion metrics from Siemens DICOM")
    parser.add_argument("--dicom_dir", required=True, help="DICOM directory")
    parser.add_argument("--output_dir", required=True, help="Output directory")
    parser.add_argument("--patient_name", help="Patient name (optional)")
    parser.add_argument("--save_nifti", action="store_true", help="Save NIfTI files for visualization")
    args = parser.parse_args()
    
    dicom_dir = Path(args.dicom_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("SIEMENS CT PERFUSION METRICS EXTRACTION")
    print("="*60)
    print(f"DICOM Dir: {dicom_dir}")
    print(f"Output Dir: {output_dir}")
    
    # 1. Tmax 로드
    print("\n[1/3] Loading Tmax volume...")
    tmax_volume, tmax_metadata = load_perfusion_volume(dicom_dir, "TMAXD")
    print(f"  Shape: {tmax_volume.shape}")
    print(f"  Range: [{tmax_volume.min():.2f}, {tmax_volume.max():.2f}] seconds")
    
    # 2. CBV 로드 (선택적)
    cbv_volume = None
    cbv_metadata = None
    try:
        print("\n[2/4] Loading CBV volume...")
        cbv_volume, cbv_metadata = load_perfusion_volume(dicom_dir, "CBVD")
        print(f"  Shape: {cbv_volume.shape}")
        print(f"  Range: [{cbv_volume.min():.2f}, {cbv_volume.max():.2f}]")
    except ValueError as e:
        print(f"  CBV not found: {e}")
    
    # 3. CBF 로드 (선택적, 논문의 Core 정의에 사용)
    cbf_volume = None
    cbf_metadata = None
    try:
        print("\n[3/4] Loading CBF volume...")
        cbf_volume, cbf_metadata = load_perfusion_volume(dicom_dir, "CBFD")
        print(f"  Shape: {cbf_volume.shape}")
        print(f"  Range: [{cbf_volume.min():.2f}, {cbf_volume.max():.2f}]")
    except ValueError as e:
        print(f"  CBF not found: {e}")
        print("  Will use Tmax/CBV for core detection")
    
    # 4. 지표 계산 (실제 pixel spacing 사용)
    print("\n[4/4] Computing perfusion metrics...")
    pixel_spacing = tmax_metadata.get('pixel_spacing_mm', [0.5, 0.5, 3.0])
    print(f"  Using pixel spacing: {pixel_spacing[0]:.2f} x {pixel_spacing[1]:.2f} x {pixel_spacing[2]:.2f} mm")
    metrics, masks = compute_perfusion_metrics(tmax_volume, cbv_volume, cbf_volume=cbf_volume, pixel_spacing=pixel_spacing)
    
    # 결과 출력
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Hypoperfusion Volume: {metrics['hypoperfusion_volume_ml']:.2f} ml")
    print(f"Infarct Core Volume:  {metrics['infarct_core_volume_ml']:.2f} ml")
    print(f"Penumbra Volume:      {metrics['penumbra_volume_ml']:.2f} ml")
    print(f"Mismatch Ratio:       {metrics['mismatch_ratio']:.2f}")
    
    # 저장
    print("\n" + "="*60)
    print("SAVING RESULTS")
    print("="*60)
    
    # JSON 저장
    result = {
        "patient_info": {
            "dicom_dir": str(dicom_dir),
            "patient_name": args.patient_name or dicom_dir.name
        },
        "tmax_metadata": tmax_metadata,
        "cbv_metadata": cbv_metadata,
        "metrics": metrics
    }
    
    json_path = output_dir / "perfusion_metrics.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[OK] Metrics saved: {json_path}")
    
    # 마스크 저장 (NPZ 형식)
    masks_path = output_dir / "masks.npz"
    np.savez_compressed(masks_path, **masks)
    print(f"[OK] Masks saved: {masks_path}")
    
    # NIfTI 저장 (웹 뷰어용)
    if args.save_nifti:
        print("\n[4/4] Saving NIfTI files for web viewer...")
        import nibabel as nib
        
        nifti_dir = output_dir / "nifti"
        nifti_dir.mkdir(exist_ok=True)
        
        # Affine matrix (기본값)
        affine = np.eye(4)
        affine[0, 0] = 0.5  # x spacing
        affine[1, 1] = 0.5  # y spacing
        affine[2, 2] = 3.0  # z spacing
        
        # Tmax NIfTI
        tmax_nifti = nib.Nifti1Image(tmax_volume, affine)
        tmax_path = nifti_dir / "tmax.nii.gz"
        nib.save(tmax_nifti, tmax_path)
        print(f"[OK] Tmax NIfTI: {tmax_path}")
        
        # CBV NIfTI (if available)
        if cbv_volume is not None:
            cbv_nifti = nib.Nifti1Image(cbv_volume, affine)
            cbv_path = nifti_dir / "cbv.nii.gz"
            nib.save(cbv_nifti, cbv_path)
            print(f"[OK] CBV NIfTI: {cbv_path}")
        
        # Mask NIfTI files
        for mask_name, mask_data in masks.items():
            mask_nifti = nib.Nifti1Image(mask_data.astype(np.uint8), affine)
            mask_path = nifti_dir / f"{mask_name}_mask.nii.gz"
            nib.save(mask_nifti, mask_path)
            print(f"[OK] {mask_name.capitalize()} mask: {mask_path}")
    
    print("\n[OK] Extraction complete!")


if __name__ == "__main__":
    main()
