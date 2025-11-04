#!/usr/bin/env python3
"""
DICOM 원본 데이터 직접 표시 뷰어
모든 Perfusion 시리즈를 RGB 그대로 표시

v2.0: 정확한 RGB → Scalar 변환 적용 (neurolabusc/rgb2scalar 기반)
"""
import argparse
import json
from pathlib import Path
import pydicom
import numpy as np
import base64
from io import BytesIO
from PIL import Image
from collections import defaultdict


def rgb_to_scalar_siemens_time(r, g, b):
    """
    Siemens CT Perfusion RGB를 스칼라 값으로 변환 (Time 계열: Tmax, MTT, TTP)
    Based on: https://github.com/neurolabusc/rgb2scalar
    
    Siemens uses a segmented non-linear color scheme with 254 distinct values.
    This function implements the exact reverse mapping from RGB to scalar intensity.
    """
    # Initialize output
    s = np.zeros_like(r, dtype=float)
    
    # Segment 1: Blue > 0, Green <= 64 (indices 1-63)
    mask1 = (g <= 64) & (b > 0)
    s[mask1] = (-r[mask1] + g[mask1] + b[mask1] + 4) * 0.245
    
    # Segment 2: Blue > 0, Green > 64 (indices 64-127)
    mask2 = (g > 64) & (b > 0)
    s[mask2] = ((-r[mask2] + g[mask2] - b[mask2]) * 0.125786164) + 95.3
    
    # Segment 3: Blue = 0, Green > 252 (indices 128-191)
    mask3 = (g > 252) & (b == 0)
    s[mask3] = (r[mask3] * 0.252) + 127.75
    
    # Segment 4: Blue = 0, R > 252 (indices 192-254)
    mask4 = (r > 252) & (b == 0)
    s[mask4] = ((255 - g[mask4]) * 0.247) + 191.75
    
    # Set black pixels to 0
    black_mask = (r + g + b) < 1
    s[black_mask] = 0
    
    # Clamp negative values
    s[s < 0] = 0
    
    return s


def rgb_to_scalar_siemens_flow(r, g, b):
    """
    Siemens CT Perfusion RGB를 스칼라 값으로 변환 (Flow/Volume 계열: CBF, CBV)
    Based on: https://github.com/neurolabusc/rgb2scalar
    """
    # Initialize output
    s = np.zeros_like(r, dtype=float)
    
    # Segment 1: indices 1-22
    mask1 = (g <= 1)
    s[mask1] = (r[mask1] + b[mask1] - 122) * (22.0 / 68.0)
    
    # Segment 2: indices 23-42
    mask2 = (r > g) & (b > g)
    s[mask2] = ((-r[mask2] + b[mask2] + g[mask2] - 4) * (19.0 / 122.0)) + 23
    
    # Segment 3: indices 42-78
    mask3 = (g == r)
    s[mask3] = ((b[mask3] - 130) * (35.0 / 123.0)) + 43
    
    # Segment 4: indices 79-158
    mask4 = (g > r) & (b > 0)
    s[mask4] = ((r[mask4] + g[mask4] - b[mask4] + 124) * (79.0 / 503.0)) + 79
    
    # Segment 5: indices 159-229
    mask5 = (b < 1)
    s[mask5] = ((r[mask5] - 128) * (70.0 / 126.0)) + 159
    
    # Segment 6: indices 230-254
    mask6 = (r > g) & (r > b)
    s[mask6] = ((-r[mask6] - g[mask6] + b[mask6] + 495) * (24.0 / 270.0)) + 230
    
    # Set black pixels to 0
    black_mask = (r + g + b) < 1
    s[black_mask] = 0
    
    # Clamp negative values
    s[s < 0] = 0
    
    return s


def rgb_to_scalar_siemens(rgb_array, max_value, is_time_series=True):
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
    if len(rgb_array.shape) != 3 or rgb_array.shape[-1] != 3:
        return rgb_array
    
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


def apply_window_level(scalar_array, window, level):
    """Window/Level 적용하여 디스플레이 품질 향상"""
    # Window/Level 적용
    lower = level - window / 2
    upper = level + window / 2
    
    # 정규화
    normalized = np.clip((scalar_array - lower) / (upper - lower), 0, 1)
    
    # 8-bit 변환 (고품질)
    display_array = (normalized * 255).astype(np.uint8)
    
    return display_array


def create_overlay_mask(mask_array, color='green', alpha=0.8, rgb_color=None):
    """
    마스크를 컬러 오버레이로 변환 (윤곽선 포함)
    
    Args:
        mask_array: 마스크 배열
        color: 기본 색상 이름 (rgb_color가 없을 때 사용)
        alpha: 투명도 (0-1)
        rgb_color: RGB 색상 [r, g, b] (0-255), 지정하면 color 무시
    """
    from scipy import ndimage
    
    overlay = np.zeros((*mask_array.shape, 4), dtype=np.uint8)
    
    # 마스크를 boolean으로 변환
    mask_bool = mask_array > 0
    
    # 윤곽선 찾기 (erosion으로 경계 검출)
    eroded = ndimage.binary_erosion(mask_bool)
    contour = mask_bool & ~eroded
    
    # RGB 색상이 지정되면 사용, 아니면 기본 색상
    if rgb_color is not None:
        r, g, b = rgb_color
        fill_color = [r, g, b, int(255 * alpha)]
        # 윤곽선은 약간 어둡게
        contour_color = [max(0, r-50), max(0, g-50), max(0, b-50), 255]
    else:
        # 기본 색상 (하위 호환성)
        if color == 'green':
            fill_color = [0, 255, 0, int(255 * alpha)]
            contour_color = [0, 200, 0, 255]
        elif color == 'red':
            fill_color = [255, 0, 0, int(255 * alpha)]
            contour_color = [200, 0, 0, 255]
        elif color == 'yellow':
            fill_color = [255, 255, 0, int(255 * alpha)]
            contour_color = [200, 200, 0, 255]
        elif color == 'cyan':
            fill_color = [0, 255, 255, int(255 * alpha)]
            contour_color = [0, 200, 200, 255]
        else:
            fill_color = [255, 255, 255, int(255 * alpha)]
            contour_color = [200, 200, 200, 255]
    
    # 채우기
    overlay[mask_bool, :] = fill_color
    
    # 윤곽선
    overlay[contour, :] = contour_color
    
    # PNG로 변환
    img = Image.fromarray(overlay, mode='RGBA')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def dicom_to_png_base64(dicom_file):
    """
    DICOM RGB 이미지를 고품질 PNG Base64로 변환 (시각화용)
    
    Note: 이 함수는 시각화 목적으로 RGB를 그대로 표시합니다.
    정량적 분석(Tmax 값 계산 등)은 extract_metrics_from_dicom.py의
    rgb_to_scalar_siemens() 함수를 사용하여 정확하게 수행됩니다.
    """
    ds = pydicom.dcmread(dicom_file)
    pixel_array = ds.pixel_array
    
    # RGB 이미지 처리 (원본 컬러 유지하면서 품질만 향상)
    # 시각화용: RGB 컬러맵을 그대로 표시하여 임상의가 익숙한 형태로 제공
    if len(pixel_array.shape) == 3 and pixel_array.shape[-1] == 3:
        # RGB 그대로 사용하되, 약간의 콘트라스트 향상
        img_array = pixel_array.astype(np.float32)
        
        # 채널별 콘트라스트 향상 (CLAHE 대신 간단한 정규화)
        for i in range(3):
            channel = img_array[:, :, i]
            if channel.max() > channel.min():
                # 1-99 percentile로 정규화 (극단값 제거)
                p1, p99 = np.percentile(channel[channel > 0], [1, 99])
                channel = np.clip((channel - p1) / (p99 - p1) * 255, 0, 255)
                img_array[:, :, i] = channel
        
        img = Image.fromarray(img_array.astype(np.uint8), mode='RGB')
    else:
        # Grayscale
        img = Image.fromarray(pixel_array.astype(np.uint8), mode='L')
        img = img.convert('RGB')
    
    # Base64 인코딩 (최소 압축)
    buffer = BytesIO()
    img.save(buffer, format='PNG', compress_level=1)  # 최소 압축으로 품질 향상
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def collect_dicom_series(dicom_dir):
    """모든 DICOM 시리즈 수집 (SeriesNumber로 구분)"""
    series_data = defaultdict(list)
    
    for dcm_file in Path(dicom_dir).glob("*.dcm"):
        try:
            ds = pydicom.dcmread(dcm_file, stop_before_pixels=True)
            series_desc = ds.get('SeriesDescription', 'Unknown')
            series_num = ds.get('SeriesNumber', 0)
            
            # Perfusion 시리즈만 선택
            if any(keyword in series_desc.upper() for keyword in ['TMAXD', 'CBVD', 'CBFD', 'MTTD', 'TTPM', 'PENUMBRA']):
                z_pos = float(ds.ImagePositionPatient[2]) if hasattr(ds, 'ImagePositionPatient') else 0
                
                # SeriesNumber와 SeriesDescription을 조합하여 고유 키 생성
                unique_key = f"{series_desc} [#{series_num}]"
                series_data[unique_key].append((z_pos, dcm_file, series_num))
        except:
            continue
    
    # 정렬
    for series_key in series_data:
        series_data[series_key].sort(key=lambda x: x[0])
    
    return series_data


def generate_html_viewer(dicom_dir, metrics_file, output_dir):
    """HTML 뷰어 생성 (오버레이 포함) - v2.0"""
    print("[DEBUG] generate_html_viewer v2.0 - WITH OVERLAYS")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Metrics 로드
    metrics_data = {}
    if Path(metrics_file).exists():
        with open(metrics_file, 'r', encoding='utf-8') as f:
            metrics_data = json.load(f)
    
    # 마스크 로드 (오버레이용)
    masks = {}
    masks_file = Path(metrics_file).parent / "masks.npz"
    if masks_file.exists():
        print(f"Loading masks from {masks_file}...")
        masks_data = np.load(masks_file)
        # NPZ 파일의 실제 키 이름 사용 (_mask 접미사 없음)
        masks = {
            'hypoperfusion': masks_data.get('hypoperfusion'),
            'core': masks_data.get('core'),
            'penumbra': masks_data.get('penumbra')
        }
        print(f"  Loaded masks: {list(masks.keys())}")
        for k, v in masks.items():
            if v is not None:
                print(f"    {k}: shape={v.shape}")
    
    # DICOM 시리즈 수집
    print("Collecting DICOM series...")
    series_data = collect_dicom_series(dicom_dir)
    
    print(f"Found {len(series_data)} series:")
    for series_desc, files in series_data.items():
        print(f"  - {series_desc}: {len(files)} slices")
    
    # 각 시리즈별 이미지 생성
    series_images = {}
    
    for series_idx, (series_desc, files) in enumerate(series_data.items()):
        print(f"\n[{series_idx+1}/{len(series_data)}] Processing {series_desc[:50]}...")
        
        # 모든 슬라이스 처리
        images = []
        # 디버그: 첫/마지막 슬라이스 z_position 출력
        if len(files) > 0:
            print(f"  Z-position range: {files[0][0]:.2f} (slice 0) → {files[-1][0]:.2f} (slice {len(files)-1})")
        
        for i, (z_pos, dcm_file, series_num) in enumerate(files):
            if i % 10 == 0:  # 진행 상황 표시 (10개마다)
                print(f"  Slice {i+1}/{len(files)}...", end='\r')
            
            img_data = dicom_to_png_base64(dcm_file)
            
            # 오버레이 생성 (PENUMBRA 시리즈 제외 - 의사가 직접 색칠한 영역)
            overlays = {}
            if masks and 'PENUMBRA' not in series_desc.upper():
                # 마스크 크기 확인
                mask_len = 0
                for mask_type in ['hypoperfusion', 'core', 'penumbra']:
                    if masks.get(mask_type) is not None:
                        mask_len = len(masks[mask_type])
                        break
                
                # 첫 슬라이스에서만 디버그 출력
                if i == 0:
                    print(f"    Mask length: {mask_len}, Series: {series_desc[:30]}")
                
                # 슬라이스 인덱스가 마스크 범위 내에 있는지 확인
                if mask_len > 0 and i < mask_len:
                    # 디버그: 슬라이스 인덱스 매칭 확인
                    if i == 0 or i == mask_len - 1:
                        print(f"      Slice {i}: z_pos={z_pos:.2f}, mask_index={i}")
                    
                    # 모든 시리즈에 Hypoperfusion (Tmax >6s) 추가
                    if masks.get('hypoperfusion') is not None:
                        overlays['hypoperfusion'] = create_overlay_mask(
                            masks['hypoperfusion'][i], color='green', alpha=1.0
                        )
                        if i == 0:
                            print(f"      Created hypoperfusion overlay (slice {i})")
                    
                    # 모든 시리즈에 Core와 Penumbra 추가 (TMAXD 조건 제거)
                    if masks.get('core') is not None:
                        overlays['core'] = create_overlay_mask(
                            masks['core'][i], color='red', alpha=1.0
                        )
                        if i == 0:
                            print(f"      Created core overlay (slice {i})")
                    
                    if masks.get('penumbra') is not None:
                        overlays['penumbra'] = create_overlay_mask(
                            masks['penumbra'][i], color='yellow', alpha=1.0
                        )
                        if i == 0:
                            print(f"      Created penumbra overlay (slice {i})")
            
            images.append({
                'index': i,
                'z_position': z_pos,
                'image': img_data,
                'overlays': overlays
            })
        
        series_images[series_desc] = {
            'series_number': files[0][2],
            'num_slices': len(files),
            'images': images
        }
        print(f"  Completed: {len(images)} images generated")
    
    # HTML 생성
    print("\nGenerating HTML...")
    patient_name = metrics_data.get('patient_info', {}).get('patient_name', 'Unknown')
    metrics = metrics_data.get('metrics', {})
    
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CT Perfusion DICOM Viewer - {patient_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a1a;
            color: #ffffff;
            overflow-x: hidden;
        }}
        .header {{
            background: rgba(15, 20, 35, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(99, 179, 237, 0.1);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }}
        .logo {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        .logo-icon {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }}
        .logo-text {{
            display: flex;
            flex-direction: column;
        }}
        .logo-text h1 {{
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
        }}
        .logo-text p {{
            font-size: 0.75rem;
            color: #8b92a7;
            letter-spacing: 1px;
            margin: 0;
        }}
        .main-layout {{
            display: grid;
            grid-template-columns: 240px 1fr;
            gap: 0;
            min-height: calc(100vh - 80px);
        }}
        .left-sidebar {{
            background: #2a2a2a;
            border-right: 1px solid #1a1a1a;
            overflow-y: auto;
            max-height: calc(100vh - 80px);
        }}
        .sidebar-section {{
            padding: 15px;
            border-bottom: 1px solid #1a1a1a;
        }}
        .sidebar-section h2 {{
            font-size: 0.7em;
            color: #667eea;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            font-weight: 600;
        }}
        .metrics {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .metric-card {{
            background: #3a3a3a;
            padding: 8px 10px;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }}
        .metric-card h3 {{
            font-size: 0.65em;
            color: #aaa;
            margin-bottom: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metric-card .value {{
            font-size: 1.1em;
            font-weight: bold;
            color: #fff;
        }}
        .series-tabs {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        .tab {{
            padding: 8px 10px;
            background: #3a3a3a;
            border: none;
            color: #aaa;
            cursor: pointer;
            border-radius: 5px;
            font-size: 0.75em;
            transition: all 0.3s;
            text-align: left;
            border-left: 3px solid transparent;
        }}
        .tab:hover {{
            background: #4a4a4a;
            color: #fff;
            border-left-color: #667eea;
        }}
        .tab-name {{
            font-weight: bold;
            font-size: 0.95em;
            margin-bottom: 2px;
        }}
        .tab-description {{
            font-size: 0.65em;
            opacity: 0.8;
            line-height: 1.2;
        }}
        .main-content {{
            background: #2a2a2a;
        }}
        .series-content {{
            display: none;
        }}
        .series-content.active {{
            display: block;
        }}
        .viewer-container {{
            display: grid;
            grid-template-columns: 1fr 200px 300px;
            gap: 15px;
            padding: 20px;
            align-items: start;
            height: calc(100vh - 80px);
        }}
        .viewer-center {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
        }}
        .viewer-controls-right {{
            display: flex;
            flex-direction: column;
            gap: 15px;
            height: 100%;
            overflow-y: auto;
        }}
        .viewer-overlays-right {{
            position: sticky;
            top: 100px;
            max-height: calc(100vh - 120px);
            overflow-y: auto;
        }}
        .main-image {{
            max-width: 100%;
            max-height: calc(100vh - 120px);
            width: auto;
            background: #000;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 8px 30px rgba(102, 126, 234, 0.3);
        }}
        .main-image img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        .overlay-controls {{
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 12px;
            background: #3a3a3a;
            border-radius: 8px;
        }}
        .overlay-item {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            padding: 8px;
            background: #2a2a2a;
            border-radius: 6px;
        }}
        .layer-description {{
            color: #999;
            font-size: 0.7em;
            font-style: italic;
            padding-left: 8px;
            margin-top: -4px;
            line-height: 1.3;
        }}
        .overlay-toggle {{
            padding: 8px 12px;
            background: #3a3a3a;
            color: #aaa;
            border: 2px solid #555;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8em;
            transition: all 0.3s;
            white-space: nowrap;
            width: 100%;
        }}
        .layer-controls-group {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            padding-left: 8px;
        }}
        .color-control {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .color-control label {{
            color: #aaa;
            font-size: 0.75em;
            min-width: 45px;
        }}
        .color-control input[type="color"] {{
            width: 40px;
            height: 28px;
            border: 2px solid #555;
            border-radius: 4px;
            cursor: pointer;
            background: transparent;
        }}
        .color-control input[type="color"]::-webkit-color-swatch-wrapper {{
            padding: 2px;
        }}
        .color-control input[type="color"]::-webkit-color-swatch {{
            border: none;
            border-radius: 4px;
        }}
        .overlay-toggle.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        .opacity-control {{
            display: flex;
            align-items: center;
            gap: 6px;
            flex: 1;
        }}
        .opacity-control label {{
            color: #aaa;
            font-size: 0.75em;
            min-width: 45px;
        }}
        .opacity-control input[type="range"] {{
            flex: 1;
            height: 5px;
            background: #555;
            border-radius: 2px;
            outline: none;
            cursor: pointer;
        }}
        .opacity-control input[type="range"]::-webkit-slider-thumb {{
            width: 14px;
            height: 14px;
            background: #667eea;
            cursor: pointer;
            border-radius: 50%;
            -webkit-appearance: none;
        }}
        .opacity-control input[type="range"]::-moz-range-thumb {{
            width: 14px;
            height: 14px;
            background: #667eea;
            cursor: pointer;
            border-radius: 50%;
            border: none;
        }}
        .opacity-control span {{
            min-width: 35px;
            color: #667eea;
            font-weight: bold;
            font-size: 0.75em;
        }}
        .overlay-layer {{
            opacity: 0.7;
        }}
        .controls {{
            width: 100%;
            padding: 15px;
            background: #3a3a3a;
            border-radius: 8px;
        }}
        .controls label {{
            display: block;
            margin-bottom: 8px;
            color: #aaa;
            font-size: 0.9em;
            text-align: center;
        }}
        .controls input[type="range"] {{
            width: 100%;
            height: 6px;
            background: #555;
            border-radius: 3px;
            outline: none;
            margin-bottom: 8px;
        }}
        .controls input[type="range"]::-webkit-slider-thumb {{
            width: 16px;
            height: 16px;
            background: #667eea;
            cursor: pointer;
            border-radius: 50%;
            -webkit-appearance: none;
        }}
        .controls span {{
            display: block;
            color: #667eea;
            font-weight: bold;
            font-size: 0.95em;
            text-align: center;
        }}
        .thumbnail-strip {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            overflow-y: auto;
            padding: 10px;
            background: #3a3a3a;
            border-radius: 8px;
            width: 100%;
            flex: 1;
            max-height: calc(100vh - 280px);
        }}
        .thumbnail {{
            min-height: 70px;
            width: 100%;
            height: 70px;
            cursor: pointer;
            border: 2px solid transparent;
            border-radius: 4px;
            transition: all 0.2s;
            opacity: 0.6;
        }}
        .thumbnail:hover {{
            opacity: 1;
            transform: scale(1.05);
        }}
        .thumbnail.active {{
            border-color: #667eea;
            opacity: 1;
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
        }}
        .thumbnail img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .instructions {{
            text-align: center;
            color: #aaa;
            padding: 10px;
            font-size: 0.75em;
            line-height: 1.4;
        }}
        
        /* Scrollbar styling */
        .left-sidebar::-webkit-scrollbar {{
            width: 8px;
        }}
        .left-sidebar::-webkit-scrollbar-track {{
            background: #1a1a1a;
        }}
        .left-sidebar::-webkit-scrollbar-thumb {{
            background: #667eea;
            border-radius: 4px;
        }}
        .left-sidebar::-webkit-scrollbar-thumb:hover {{
            background: #764ba2;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <div class="logo-icon">🧠</div>
            <div class="logo-text">
                <h1>NeuroFlow</h1>
                <p>CT PERFUSION ANALYSIS SUITE</p>
            </div>
        </div>
    </div>
    
    <div class="main-layout">
        <div class="left-sidebar">
            <div class="sidebar-section">
                <h2>📊 Key Metrics</h2>
                <div class="metrics">
                    <div class="metric-card">
                        <h3>Hypoperfusion</h3>
                        <div class="value">{metrics.get('hypoperfusion_volume_ml', 0):.1f} ml</div>
                    </div>
                    <div class="metric-card">
                        <h3>Infarct Core</h3>
                        <div class="value">{metrics.get('infarct_core_volume_ml', 0):.1f} ml</div>
                    </div>
                    <div class="metric-card">
                        <h3>Penumbra</h3>
                        <div class="value">{metrics.get('penumbra_volume_ml', 0):.1f} ml</div>
                    </div>
                    <div class="metric-card">
                        <h3>Mismatch Ratio</h3>
                        <div class="value">{metrics.get('mismatch_ratio', 0):.2f}</div>
                    </div>
                </div>
            </div>
            
            <div class="sidebar-section">
                <h2>🎯 Perfusion Maps</h2>
                <div class="series-tabs">
"""
    
    # 시리즈 설명 매핑
    series_descriptions = {
        'TMAXD': 'Time to Maximum (Tmax) - Delay in contrast arrival',
        'CBVD': 'Cerebral Blood Volume - Total blood in tissue',
        'CBFD': 'Cerebral Blood Flow - Blood flow rate',
        'MTTD': 'Mean Transit Time - Average blood transit time',
        'TTPM': 'Time to Peak - Time to peak enhancement',
        'PENUMBRA': 'Penumbra Region - Manually annotated by physician (no overlay)'
    }
    
    # 탭 생성
    for i, series_desc in enumerate(series_images.keys()):
        active_class = "active" if i == 0 else ""
        
        # 시리즈 이름에서 키워드 추출
        series_key = None
        for key in series_descriptions.keys():
            if key in series_desc.upper():
                series_key = key
                break
        
        description = series_descriptions.get(series_key, 'Perfusion parameter') if series_key else 'Perfusion data'
        
        html_content += f'''        <button class="tab {active_class}" onclick="showSeries('{series_desc}')">
            <div class="tab-name">{series_key if series_key else series_desc[:20]}</div>
            <div class="tab-description">{description}</div>
        </button>
'''
    
    html_content += """                </div>
            </div>
        </div>
        
        <div class="main-content">
"""
    
    # 각 시리즈 콘텐츠
    for i, (series_desc, series_info) in enumerate(series_images.items()):
        active_class = "active" if i == 0 else ""
        # 안전한 ID 생성 (특수문자 모두 제거)
        safe_id = ''.join(c if c.isalnum() or c == '_' else '_' for c in series_desc)
        
        # 오버레이 토글 버튼 HTML
        # 빈 딕셔너리도 True로 판단되므로, 실제 키가 있는지 확인
        has_overlays = any(len(img['overlays']) > 0 for img in series_info['images'])
        print(f"  Series: {series_desc[:50]}")
        print(f"    Has overlays: {has_overlays}")
        if has_overlays:
            overlay_count = sum(1 for img in series_info['images'] if len(img['overlays']) > 0)
            print(f"    Overlay count: {overlay_count}/{len(series_info['images'])}")
        
        overlay_buttons = ""
        if has_overlays:
            # 실제 오버레이 데이터가 있는 타입 확인
            available_overlays = set()
            for img in series_info['images']:
                available_overlays.update(img.get('overlays', {}).keys())
            
            print(f"    Available overlays for this series: {available_overlays}")
            
            # 오버레이 컨트롤 시작
            overlay_buttons = '<div class="overlay-controls">'
            
            # Hypoperfusion (모든 시리즈)
            if 'hypoperfusion' in available_overlays:
                overlay_buttons += f"""
                    <div class="overlay-item">
                        <button class="overlay-toggle active" onclick="toggleOverlay('{safe_id}', 'hypoperfusion', event)" title="Tmax ≥6초: 혈류 지연된 전체 영역">
                            🟢 Hypoperfusion
                        </button>
                        <div class="layer-description">Tmax ≥6s: 혈류가 느려진 전체 허혈 영역</div>
                        <div class="layer-controls-group">
                            <div class="color-control">
                                <label>Color:</label>
                                <input type="color" id="{safe_id}-color-hypoperfusion" value="#00ff00" 
                                       oninput="updateColor('{safe_id}', 'hypoperfusion', this.value)">
                            </div>
                            <div class="opacity-control">
                                <label>Opacity:</label>
                                <input type="range" id="{safe_id}-opacity-hypoperfusion" min="0" max="100" value="70" 
                                       oninput="updateOpacity('{safe_id}', 'hypoperfusion', this.value)">
                                <span id="{safe_id}-opacity-value-hypoperfusion">70%</span>
                            </div>
                        </div>
                    </div>
"""
            
            # Core (TMAXD 시리즈만)
            if 'core' in available_overlays:
                overlay_buttons += f"""
                    <div class="overlay-item">
                        <button class="overlay-toggle active" onclick="toggleOverlay('{safe_id}', 'core', event)" title="Tmax ≥10초 & CBV <2.0: 이미 손상된 조직">
                            🔴 Core
                        </button>
                        <div class="layer-description">Tmax ≥10s & CBV <2.0: 이미 손상된 조직 (회복 불가)</div>
                        <div class="layer-controls-group">
                            <div class="color-control">
                                <label>Color:</label>
                                <input type="color" id="{safe_id}-color-core" value="#ff0000" 
                                       oninput="updateColor('{safe_id}', 'core', this.value)">
                            </div>
                            <div class="opacity-control">
                                <label>Opacity:</label>
                                <input type="range" id="{safe_id}-opacity-core" min="0" max="100" value="90" 
                                       oninput="updateOpacity('{safe_id}', 'core', this.value)">
                                <span id="{safe_id}-opacity-value-core">90%</span>
                            </div>
                        </div>
                    </div>
"""
            
            # Penumbra (TMAXD 시리즈만)
            if 'penumbra' in available_overlays:
                overlay_buttons += f"""
                    <div class="overlay-item">
                        <button class="overlay-toggle active" onclick="toggleOverlay('{safe_id}', 'penumbra', event)" title="Hypoperfusion - Core: 구제 가능한 조직">
                            🟡 Penumbra
                        </button>
                        <div class="layer-description">6s ≤ Tmax < 10s: 구제 가능한 조직 (치료 목표)</div>
                        <div class="layer-controls-group">
                            <div class="color-control">
                                <label>Color:</label>
                                <input type="color" id="{safe_id}-color-penumbra" value="#ffff00" 
                                       oninput="updateColor('{safe_id}', 'penumbra', this.value)">
                            </div>
                            <div class="opacity-control">
                                <label>Opacity:</label>
                                <input type="range" id="{safe_id}-opacity-penumbra" min="0" max="100" value="80" 
                                       oninput="updateOpacity('{safe_id}', 'penumbra', this.value)">
                                <span id="{safe_id}-opacity-value-penumbra">80%</span>
                            </div>
                        </div>
                    </div>
"""
            
            # Low CBV (CBVD 시리즈)
            if 'low_cbv' in available_overlays:
                overlay_buttons += f"""
                    <div class="overlay-item">
                        <button class="overlay-toggle active" onclick="toggleOverlay('{safe_id}', 'low_cbv', event)" title="CBV <2.0 ml/100g: 혈류량 심각하게 감소">
                            🔵 Low CBV
                        </button>
                        <div class="layer-description">CBV <2.0: 혈류량 감소 (측부순환 불량)</div>
                        <div class="layer-controls-group">
                            <div class="color-control">
                                <label>Color:</label>
                                <input type="color" id="{safe_id}-color-low_cbv" value="#0088ff" 
                                       oninput="updateColor('{safe_id}', 'low_cbv', this.value)">
                            </div>
                            <div class="opacity-control">
                                <label>Opacity:</label>
                                <input type="range" id="{safe_id}-opacity-low_cbv" min="0" max="100" value="75" 
                                       oninput="updateOpacity('{safe_id}', 'low_cbv', this.value)">
                                <span id="{safe_id}-opacity-value-low_cbv">75%</span>
                            </div>
                        </div>
                    </div>
"""
            
            # CBF Core (CBFD 시리즈)
            if 'cbf_core' in available_overlays:
                overlay_buttons += f"""
                    <div class="overlay-item">
                        <button class="overlay-toggle active" onclick="toggleOverlay('{safe_id}', 'cbf_core', event)" title="Relative CBF <38%: 정확한 Core 예측">
                            🟠 CBF Core
                        </button>
                        <div class="layer-description">CBF <38%: CBF 기반 Core (더 정확한 예측)</div>
                        <div class="layer-controls-group">
                            <div class="color-control">
                                <label>Color:</label>
                                <input type="color" id="{safe_id}-color-cbf_core" value="#ff6600" 
                                       oninput="updateColor('{safe_id}', 'cbf_core', this.value)">
                            </div>
                            <div class="opacity-control">
                                <label>Opacity:</label>
                                <input type="range" id="{safe_id}-opacity-cbf_core" min="0" max="100" value="85" 
                                       oninput="updateOpacity('{safe_id}', 'cbf_core', this.value)">
                                <span id="{safe_id}-opacity-value-cbf_core">85%</span>
                            </div>
                        </div>
                    </div>
"""
            
            overlay_buttons += "</div>"
        
        html_content += f"""    <div class="series-content {active_class}" id="{safe_id}">
        <div class="viewer-container">
            <div class="viewer-center">
                <div class="main-image" id="{safe_id}-main" style="position: relative;">
                    <img src="{series_info['images'][0]['image']}" alt="Main view" style="display: block; width: 100%;">
                    <div id="{safe_id}-overlay-core" class="overlay-layer" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></div>
                    <div id="{safe_id}-overlay-penumbra" class="overlay-layer" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></div>
                    <div id="{safe_id}-overlay-hypoperfusion" class="overlay-layer" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></div>
                    <div id="{safe_id}-overlay-low_cbv" class="overlay-layer" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></div>
                    <div id="{safe_id}-overlay-cbf_core" class="overlay-layer" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></div>
                </div>
            </div>
            
            <div class="viewer-controls-right">
                <div class="controls">
                    <label>Slice: </label>
                    <input type="range" min="0" max="{series_info['num_slices']-1}" value="0" 
                           oninput="changeSlice('{safe_id}', this.value)"
                           id="{safe_id}-slider">
                    <span id="{safe_id}-slice-num">0 / {series_info['num_slices']-1}</span>
                </div>
                
                <div class="thumbnail-strip" id="{safe_id}-thumbnails">
"""
        
        # 썸네일 추가
        for idx, img_info in enumerate(series_info['images']):
            active_thumb = "active" if idx == 0 else ""
            html_content += f"""                <div class="thumbnail {active_thumb}" onclick="changeSlice('{safe_id}', {idx})">
                    <img src="{img_info['image']}" alt="Slice {idx}">
                </div>
"""
        
        html_content += f"""                </div>
                
                <div class="instructions">
                    🖱️ Wheel/Arrow keys to navigate<br>Click thumbnails to jump
                </div>
            </div>
            
            <div class="viewer-overlays-right">
                {overlay_buttons}
            </div>
        </div>
    </div>
    
"""
    
    html_content += """        </div>
    </div>
    
    <script>
        // 시리즈별 이미지 데이터 저장
        const seriesData = {};
        
"""
    
    # 각 시리즈의 이미지 및 오버레이 데이터를 JavaScript에 저장
    for series_desc, series_info in series_images.items():
        # 안전한 ID 생성 (특수문자 모두 제거)
        safe_id = ''.join(c if c.isalnum() or c == '_' else '_' for c in series_desc)
        
        # 이미지와 오버레이 데이터 준비
        images_data = []
        for img in series_info['images']:
            images_data.append({
                'image': img['image'],
                'overlays': img.get('overlays', {})
            })
        
        html_content += f"""        seriesData['{safe_id}'] = {json.dumps(images_data)};
"""
    
    html_content += """        
        function showSeries(seriesName) {
            // 안전한 ID 생성 (특수문자 모두 제거)
            const safeId = seriesName.replace(/[^a-zA-Z0-9_]/g, '_');
            
            // Hide all
            document.querySelectorAll('.series-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            
            // Show selected
            const targetContent = document.getElementById(safeId);
            if (targetContent) {
                targetContent.classList.add('active');
            }
            
            // Highlight active tab
            document.querySelectorAll('.tab').forEach(tab => {
                if (tab.getAttribute('onclick').includes(seriesName)) {
                    tab.classList.add('active');
                }
            });
        }
        
        // 오버레이 상태 저장
        const overlayStates = {};
        
        async function changeSlice(seriesId, sliceIndex) {
            const index = parseInt(sliceIndex);
            const images = seriesData[seriesId];
            const maxIndex = images.length - 1;
            
            // 범위 체크
            if (index < 0 || index > maxIndex) return;
            
            // 메인 이미지 업데이트
            const mainImg = document.querySelector(`#${seriesId}-main img`);
            mainImg.src = images[index].image;
            
            // 오버레이 업데이트 (색상 적용)
            const overlays = images[index].overlays || {};
            const overlayTypes = ['core', 'penumbra', 'hypoperfusion', 'low_cbv', 'cbf_core'];
            
            for (const type of overlayTypes) {
                const overlayDiv = document.getElementById(`${seriesId}-overlay-${type}`);
                if (overlayDiv) {
                    if (overlays[type] && overlayStates[`${seriesId}-${type}`] !== false) {
                        // 사용자 정의 색상 확인
                        const colorKey = `${seriesId}-${type}`;
                        const customColor = window.overlayColors && window.overlayColors[colorKey];
                        
                        if (customColor) {
                            // 색상 적용
                            const coloredImg = await applyColorToOverlay(overlays[type], customColor);
                            overlayDiv.innerHTML = `<img src="${coloredImg}" style="width: 100%; height: 100%;">`;
                        } else {
                            // 기본 색상
                            overlayDiv.innerHTML = `<img src="${overlays[type]}" style="width: 100%; height: 100%;">`;
                        }
                    } else {
                        overlayDiv.innerHTML = '';
                    }
                }
            }
            
            // 슬라이더 업데이트
            const slider = document.getElementById(`${seriesId}-slider`);
            slider.value = index;
            
            // 텍스트 업데이트
            document.getElementById(`${seriesId}-slice-num`).textContent = `${index} / ${maxIndex}`;
            
            // 썸네일 활성화 상태 업데이트
            const thumbnails = document.querySelectorAll(`#${seriesId}-thumbnails .thumbnail`);
            thumbnails.forEach((thumb, i) => {
                if (i === index) {
                    thumb.classList.add('active');
                    thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                } else {
                    thumb.classList.remove('active');
                }
            });
        }
        
        function toggleOverlay(seriesId, overlayType, event) {
            const key = `${seriesId}-${overlayType}`;
            
            // 초기화: 처음 클릭 시 true로 설정 (기본값)
            if (overlayStates[key] === undefined) {
                overlayStates[key] = true;
            }
            
            // 토글
            overlayStates[key] = !overlayStates[key];
            
            // 버튼 상태 업데이트
            const button = event.currentTarget;
            button.classList.toggle('active');
            
            console.log(`Overlay ${overlayType} for ${seriesId}: ${overlayStates[key] ? 'ON' : 'OFF'}`);
            
            // 현재 슬라이스 다시 렌더링
            const slider = document.getElementById(`${seriesId}-slider`);
            changeSlice(seriesId, slider.value);
        }
        
        function updateOpacity(seriesId, overlayType, value) {
            // 투명도 값 업데이트 (0-100 → 0-1)
            const opacity = value / 100;
            
            // 값 표시 업데이트
            const valueSpan = document.getElementById(`${seriesId}-opacity-value-${overlayType}`);
            if (valueSpan) {
                valueSpan.textContent = `${value}%`;
            }
            
            // 오버레이 레이어의 투명도 직접 변경
            const overlayLayer = document.getElementById(`${seriesId}-overlay-${overlayType}`);
            if (overlayLayer) {
                overlayLayer.style.opacity = opacity;
            }
            
            console.log(`Opacity ${overlayType} for ${seriesId}: ${value}%`);
        }
        
        function updateColor(seriesId, overlayType, hexColor) {
            // Hex color를 RGB로 변환
            const r = parseInt(hexColor.substr(1,2), 16);
            const g = parseInt(hexColor.substr(3,2), 16);
            const b = parseInt(hexColor.substr(5,2), 16);
            
            console.log(`Color ${overlayType} for ${seriesId}: ${hexColor} (RGB: ${r}, ${g}, ${b})`);
            
            // 색상 정보를 저장 (나중에 슬라이스 변경 시 사용)
            if (!window.overlayColors) window.overlayColors = {};
            const key = `${seriesId}-${overlayType}`;
            window.overlayColors[key] = {r, g, b};
            
            // 현재 슬라이스 다시 렌더링 (새 색상 적용)
            const slider = document.getElementById(`${seriesId}-slider`);
            if (slider) {
                changeSlice(seriesId, slider.value);
            }
        }
        
        // 오버레이 이미지에 색상 적용
        function applyColorToOverlay(overlayImg, targetColor) {
            // Canvas 생성
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            return new Promise((resolve) => {
                const img = new Image();
                img.crossOrigin = 'anonymous';
                img.onload = function() {
                    canvas.width = img.width;
                    canvas.height = img.height;
                    
                    // 원본 이미지 그리기
                    ctx.drawImage(img, 0, 0);
                    
                    // 이미지 데이터 가져오기
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    const data = imageData.data;
                    
                    // 각 픽셀의 색상 변경 (알파 채널은 유지)
                    for (let i = 0; i < data.length; i += 4) {
                        if (data[i + 3] > 0) {  // 투명하지 않은 픽셀만
                            // 원본 밝기 계산 (grayscale)
                            const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3 / 255;
                            
                            // 새 색상 적용 (밝기 유지)
                            data[i] = targetColor.r * brightness;     // R
                            data[i + 1] = targetColor.g * brightness; // G
                            data[i + 2] = targetColor.b * brightness; // B
                            // data[i + 3]는 알파 채널 (유지)
                        }
                    }
                    
                    // 수정된 이미지 데이터 적용
                    ctx.putImageData(imageData, 0, 0);
                    
                    // Data URL로 변환
                    resolve(canvas.toDataURL());
                };
                img.src = overlayImg;
            });
        }
        
        // RGB를 Hue로 변환 (0-360도)
        function rgbToHue(r, g, b) {
            r /= 255;
            g /= 255;
            b /= 255;
            
            const max = Math.max(r, g, b);
            const min = Math.min(r, g, b);
            const delta = max - min;
            
            if (delta === 0) return 0;
            
            let hue;
            if (max === r) {
                hue = ((g - b) / delta) % 6;
            } else if (max === g) {
                hue = (b - r) / delta + 2;
            } else {
                hue = (r - g) / delta + 4;
            }
            
            hue = Math.round(hue * 60);
            if (hue < 0) hue += 360;
            
            return hue;
        }
        
        // RGB를 Saturation으로 변환 (0-100%)
        function rgbToSaturation(r, g, b) {
            r /= 255;
            g /= 255;
            b /= 255;
            
            const max = Math.max(r, g, b);
            const min = Math.min(r, g, b);
            const delta = max - min;
            
            if (max === 0) return 0;
            
            const saturation = (delta / max) * 100;
            return Math.round(saturation * 2); // 2배로 강조
        }
        
        // 페이지 로드 시 초기 투명도 설정
        document.addEventListener('DOMContentLoaded', function() {
            // 모든 오버레이 레이어의 초기 투명도 설정
            document.querySelectorAll('[id$="-overlay-hypoperfusion"]').forEach(layer => {
                layer.style.opacity = 0.7;
            });
            document.querySelectorAll('[id$="-overlay-core"]').forEach(layer => {
                layer.style.opacity = 0.9;
            });
            document.querySelectorAll('[id$="-overlay-penumbra"]').forEach(layer => {
                layer.style.opacity = 0.8;
            });
            document.querySelectorAll('[id$="-overlay-low_cbv"]').forEach(layer => {
                layer.style.opacity = 0.75;
            });
            document.querySelectorAll('[id$="-overlay-cbf_core"]').forEach(layer => {
                layer.style.opacity = 0.85;
            });
            
            // 마우스 휠 이벤트 (슬라이스 변경)
            document.querySelectorAll('.main-image').forEach(mainImage => {
                mainImage.addEventListener('wheel', function(e) {
                    e.preventDefault();
                    
                    const seriesId = this.id.replace('-main', '');
                    const slider = document.getElementById(`${seriesId}-slider`);
                    const currentIndex = parseInt(slider.value);
                    const maxIndex = parseInt(slider.max);
                    
                    let newIndex = currentIndex;
                    if (e.deltaY < 0) {
                        newIndex = Math.max(0, currentIndex - 1);
                    } else {
                        newIndex = Math.min(maxIndex, currentIndex + 1);
                    }
                    
                    if (newIndex !== currentIndex) {
                        changeSlice(seriesId, newIndex);
                    }
                });
            });
            
            // 키보드 이벤트 (화살표 키)
            document.addEventListener('keydown', function(e) {
                const activeContent = document.querySelector('.series-content.active');
                if (!activeContent) return;
                
                const seriesId = activeContent.id;
                const slider = document.getElementById(`${seriesId}-slider`);
                const currentIndex = parseInt(slider.value);
                const maxIndex = parseInt(slider.max);
                
                if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                    e.preventDefault();
                    const newIndex = Math.max(0, currentIndex - 1);
                    changeSlice(seriesId, newIndex);
                } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                    e.preventDefault();
                    const newIndex = Math.min(maxIndex, currentIndex + 1);
                    changeSlice(seriesId, newIndex);
                }
            });
        });
    </script>
</body>
</html>
"""
    
    # HTML 저장
    html_path = output_dir / "viewer.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\n[OK] DICOM viewer created: {html_path}")
    print(f"[OK] Total series: {len(series_images)}")
    for series_desc, series_info in series_images.items():
        print(f"  - {series_desc}: {series_info['num_slices']} slices")
    
    return html_path


def main():
    try:
        print("=" * 60)
        print("DICOM Viewer Generator - Debug Mode")
        print("=" * 60)
        
        parser = argparse.ArgumentParser(description="Generate DICOM viewer")
        parser.add_argument("--dicom_dir", required=True, help="DICOM directory")
        parser.add_argument("--metrics", required=True, help="Metrics JSON file")
        parser.add_argument("--output_dir", required=True, help="Output directory")
        args = parser.parse_args()
        
        print("\n[Arguments]")
        print(f"  DICOM dir: {args.dicom_dir}")
        print(f"  Metrics: {args.metrics}")
        print(f"  Output dir: {args.output_dir}")
        print()
        
        html_path = generate_html_viewer(args.dicom_dir, args.metrics, args.output_dir)
        print(f"\n[OK] Viewer generated: {html_path}")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}")
        print(f"  Message: {str(e)}")
        import traceback
        print("\n[Full traceback]")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())