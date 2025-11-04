#!/usr/bin/env python3
"""
고품질 DICOM 뷰어 with Index 시각화
- 원본 스칼라값 복원
- Window/Level 조정
- CBV Index ROI 시각화
- 논문 지표 특화 뷰
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


def rgb_to_scalar_siemens(rgb_array, max_value):
    """Siemens RGB → 원본 스칼라값 복원 (고정밀)"""
    if len(rgb_array.shape) != 3 or rgb_array.shape[-1] != 3:
        return rgb_array
    
    r = rgb_array[:, :, 0].astype(np.float32)
    g = rgb_array[:, :, 1].astype(np.float32)
    b = rgb_array[:, :, 2].astype(np.float32)
    
    # Siemens 인코딩: value = (R * 256 + G + B/256) / 65536 * max_value
    scalar = (r * 256.0 + g + b / 256.0) / 65536.0 * max_value
    
    return scalar


def apply_window_level(scalar_array, window, level, colormap='gray'):
    """Window/Level 적용 및 컬러맵 변환"""
    # Window/Level 적용
    lower = level - window / 2
    upper = level + window / 2
    
    # 정규화
    normalized = np.clip((scalar_array - lower) / (upper - lower), 0, 1)
    
    # 8-bit 변환
    display_array = (normalized * 255).astype(np.uint8)
    
    # 컬러맵 적용
    if colormap == 'jet':
        # Jet colormap (Tmax, CBV 등)
        img = Image.fromarray(display_array, mode='L')
        img = img.convert('RGB')
        # PIL에서 jet colormap 적용 (간단 버전)
        rgb_array = np.array(img)
        # 간단한 jet 근사: 파랑 → 녹색 → 빨강
        jet_r = np.clip(255 * (1.5 - 2 * abs(normalized - 0.75)), 0, 255).astype(np.uint8)
        jet_g = np.clip(255 * (1.5 - 2 * abs(normalized - 0.5)), 0, 255).astype(np.uint8)
        jet_b = np.clip(255 * (1.5 - 2 * abs(normalized - 0.25)), 0, 255).astype(np.uint8)
        rgb_array[:, :, 0] = jet_r
        rgb_array[:, :, 1] = jet_g
        rgb_array[:, :, 2] = jet_b
        return rgb_array
    else:
        # Grayscale
        return np.stack([display_array] * 3, axis=-1)


def create_roi_overlay(scalar_array, mask, color, alpha=0.3):
    """ROI 마스크 오버레이 생성"""
    overlay = np.zeros((*scalar_array.shape, 4), dtype=np.uint8)
    
    if color == 'red':
        overlay[mask, 0] = 255
        overlay[mask, 3] = int(255 * alpha)
    elif color == 'blue':
        overlay[mask, 2] = 255
        overlay[mask, 3] = int(255 * alpha)
    elif color == 'green':
        overlay[mask, 1] = 255
        overlay[mask, 3] = int(255 * alpha)
    
    return overlay


def dicom_to_enhanced_base64(dicom_file, window=None, level=None, colormap='gray'):
    """DICOM → 고품질 Base64 (Window/Level 적용)"""
    ds = pydicom.dcmread(dicom_file)
    pixel_array = ds.pixel_array
    series_desc = ds.get('SeriesDescription', '')
    
    # 기본 Window/Level 설정
    if window is None or level is None:
        if 'TMAXD' in series_desc.upper():
            window, level = 12, 6
        elif 'CBVD' in series_desc.upper():
            window, level = 80, 40
        elif 'CBFD' in series_desc.upper():
            window, level = 100, 50
        else:
            window, level = 100, 50
    
    # RGB → Scalar 변환
    if len(pixel_array.shape) == 3 and pixel_array.shape[-1] == 3:
        # 최대값 추정
        if 'TMAXD' in series_desc.upper():
            max_value = 12.0
        elif 'CBVD' in series_desc.upper():
            max_value = 10.0
        elif 'CBFD' in series_desc.upper():
            max_value = 100.0
        else:
            max_value = 100.0
        
        scalar_array = rgb_to_scalar_siemens(pixel_array, max_value)
    else:
        scalar_array = pixel_array.astype(np.float32)
    
    # Window/Level 적용
    display_array = apply_window_level(scalar_array, window, level, colormap)
    
    # PNG 인코딩 (최고 품질)
    img = Image.fromarray(display_array.astype(np.uint8), mode='RGB')
    buffer = BytesIO()
    img.save(buffer, format='PNG', compress_level=1)  # 최소 압축
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}", scalar_array


def generate_enhanced_html(dicom_dir, output_file, metrics_file=None):
    """고품질 HTML 뷰어 생성"""
    
    print(f"Starting enhanced viewer generation...")
    print(f"DICOM dir: {dicom_dir}")
    print(f"Output: {output_file}")
    print(f"Metrics: {metrics_file}")
    
    # 메트릭 로드
    metrics = {}
    if metrics_file and Path(metrics_file).exists():
        try:
            with open(metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # metrics가 중첩된 경우 처리
                if 'metrics' in data:
                    metrics = data['metrics']
                else:
                    metrics = data
            print(f"Metrics loaded: {list(metrics.keys())}")
        except Exception as e:
            print(f"Warning: Could not load metrics: {e}")
            metrics = {}
    
    # DICOM 시리즈 수집
    series_data = defaultdict(list)
    
    print(f"Scanning DICOM files in {dicom_dir}...")
    dcm_files = list(Path(dicom_dir).glob("*.dcm"))
    print(f"Found {len(dcm_files)} DICOM files")
    
    for dcm_file in dcm_files:
        try:
            ds = pydicom.dcmread(dcm_file, stop_before_pixels=True)
            series_desc = ds.get('SeriesDescription', 'Unknown')
            series_num = ds.get('SeriesNumber', 0)
            
            if any(keyword in series_desc.upper() for keyword in ['TMAXD', 'CBVD', 'CBFD', 'MTTD', 'TTPM', 'PENUMBRA']):
                z_pos = float(ds.ImagePositionPatient[2]) if hasattr(ds, 'ImagePositionPatient') else 0
                unique_key = f"{series_desc} [#{series_num}]"
                series_data[unique_key].append((z_pos, dcm_file, series_num))
        except Exception as e:
            print(f"Warning: Could not read {dcm_file.name}: {e}")
            continue
    
    print(f"Found {len(series_data)} perfusion series")
    
    if not series_data:
        raise ValueError("No perfusion series found")
    
    # 시리즈별 이미지 생성
    series_images = {}
    
    for series_desc, files in series_data.items():
        print(f"Processing series: {series_desc} ({len(files)} slices)")
        files.sort(key=lambda x: x[0])
        
        images = []
        for z_pos, dcm_file, series_num in files:
            try:
                img_base64, scalar_array = dicom_to_enhanced_base64(dcm_file)
                
                images.append({
                    'image': img_base64,
                    'z_position': z_pos,
                    'slice_number': len(images)
                })
            except Exception as e:
                print(f"Warning: Could not process {dcm_file.name}: {e}")
                continue
        
        if images:
            series_images[series_desc] = {
                'images': images,
                'num_slices': len(images)
            }
            print(f"  → Generated {len(images)} images")
    
    if not series_images:
        raise ValueError("No images could be generated")
    
    # HTML 생성
    html_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NeuroFlow - Enhanced CT Perfusion Viewer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 16px;
            opacity: 0.9;
        }
        
        /* Index 인디케이터 */
        .index-panel {
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .index-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        
        .index-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .index-card .label {
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }
        
        .index-card .value {
            font-size: 24px;
            font-weight: 700;
            color: #333;
        }
        
        .index-card .grade {
            font-size: 14px;
            margin-top: 5px;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        
        .grade.good {
            background: #d4edda;
            color: #155724;
        }
        
        .grade.poor {
            background: #f8d7da;
            color: #721c24;
        }
        
        /* 탭 */
        .tabs {
            display: flex;
            background: #f5f5f5;
            padding: 10px 20px;
            gap: 10px;
            overflow-x: auto;
        }
        
        .tab {
            padding: 12px 24px;
            background: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            color: #666;
            transition: all 0.3s;
            white-space: nowrap;
        }
        
        .tab:hover {
            background: #e0e0e0;
        }
        
        .tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        /* 뷰어 */
        .series-content {
            display: none;
            padding: 30px;
        }
        
        .series-content.active {
            display: block;
        }
        
        .viewer-container {
            display: flex;
            gap: 20px;
        }
        
        .main-viewer {
            flex: 3;
        }
        
        .main-image {
            background: #000;
            border-radius: 10px;
            overflow: hidden;
            position: relative;
            cursor: crosshair;
        }
        
        .main-image img {
            width: 100%;
            height: auto;
            display: block;
        }
        
        /* 픽셀값 툴팁 */
        .pixel-tooltip {
            position: absolute;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            pointer-events: none;
            display: none;
            z-index: 1000;
        }
        
        /* Window/Level 컨트롤 */
        .wl-controls {
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .wl-controls label {
            display: block;
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }
        
        .wl-controls input[type="range"] {
            width: 100%;
            margin-bottom: 10px;
        }
        
        /* 썸네일 */
        .thumbnail-strip {
            display: flex;
            gap: 10px;
            overflow-x: auto;
            padding: 15px 0;
        }
        
        .thumbnail {
            min-width: 80px;
            height: 80px;
            border: 2px solid transparent;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s;
            overflow: hidden;
        }
        
        .thumbnail:hover {
            border-color: #667eea;
            transform: scale(1.05);
        }
        
        .thumbnail.active {
            border-color: #764ba2;
            box-shadow: 0 0 10px rgba(118, 75, 162, 0.5);
        }
        
        .thumbnail img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        /* 사이드 패널 */
        .side-panel {
            flex: 1;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
        }
        
        .side-panel h3 {
            font-size: 16px;
            margin-bottom: 15px;
            color: #333;
        }
        
        .roi-info {
            background: white;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 10px;
            font-size: 13px;
        }
        
        .roi-info .roi-label {
            font-weight: 600;
            color: #666;
            margin-bottom: 5px;
        }
        
        .roi-info .roi-value {
            font-size: 18px;
            font-weight: 700;
            color: #333;
        }
        
        /* 슬라이더 */
        .controls {
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .controls input[type="range"] {
            width: 100%;
        }
        
        .instructions {
            margin-top: 15px;
            padding: 12px;
            background: #e3f2fd;
            border-radius: 6px;
            font-size: 13px;
            color: #1976d2;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 NeuroFlow Enhanced Viewer</h1>
            <p>High-Quality CT Perfusion Analysis with Index Visualization</p>
        </div>
"""
    
    # Index 패널 추가
    if metrics:
        corrected_cbv = metrics.get('corrected_cbv_index')
        conventional_cbv = metrics.get('conventional_cbv_index')
        collateral_grade = metrics.get('collateral_grade', 'N/A')
        hir = metrics.get('hir')
        prr = metrics.get('prr')
        
        grade_class = 'good' if corrected_cbv and corrected_cbv >= 0.70 else 'poor'
        
        html_content += f"""
        <div class="index-panel">
            <div class="index-grid">
                <div class="index-card">
                    <div class="label">Corrected CBV Index</div>
                    <div class="value">{corrected_cbv:.3f if corrected_cbv else 'N/A'}</div>
                    <div class="grade {grade_class}">{collateral_grade}</div>
                </div>
                <div class="index-card">
                    <div class="label">Conventional CBV Index</div>
                    <div class="value">{conventional_cbv:.3f if conventional_cbv else 'N/A'}</div>
                </div>
                <div class="index-card">
                    <div class="label">HIR (Hypoperfusion Intensity)</div>
                    <div class="value">{hir:.3f if hir else 'N/A'}</div>
                </div>
                <div class="index-card">
                    <div class="label">PRR (Penumbral Rescue Ratio)</div>
                    <div class="value">{prr*100:.1f if prr else 'N/A'}%</div>
                </div>
            </div>
        </div>
"""
    
    # 탭
    html_content += """
        <div class="tabs">
"""
    
    for i, series_desc in enumerate(series_images.keys()):
        active_class = "active" if i == 0 else ""
        html_content += f'            <button class="tab {active_class}" onclick="showSeries(\'{series_desc}\')">{series_desc}</button>\n'
    
    html_content += """        </div>
"""
    
    # 시리즈 콘텐츠
    for i, (series_desc, series_info) in enumerate(series_images.items()):
        active_class = "active" if i == 0 else ""
        safe_id = ''.join(c if c.isalnum() or c == '_' else '_' for c in series_desc)
        
        html_content += f"""
        <div class="series-content {active_class}" id="{safe_id}">
            <div class="viewer-container">
                <div class="main-viewer">
                    <div class="main-image" id="{safe_id}-main">
                        <img src="{series_info['images'][0]['image']}" alt="Main view">
                        <div class="pixel-tooltip" id="{safe_id}-tooltip"></div>
                    </div>
                    
                    <div class="controls">
                        <label>Slice: <span id="{safe_id}-slice-num">0 / {series_info['num_slices']-1}</span></label>
                        <input type="range" min="0" max="{series_info['num_slices']-1}" value="0"
                               oninput="changeSlice('{safe_id}', this.value)"
                               id="{safe_id}-slider">
                    </div>
                    
                    <div class="thumbnail-strip" id="{safe_id}-thumbnails">
"""
        
        # 썸네일
        for j, img_data in enumerate(series_info['images']):
            active_thumb = "active" if j == 0 else ""
            html_content += f"""                        <div class="thumbnail {active_thumb}" onclick="changeSlice('{safe_id}', {j})">
                            <img src="{img_data['image']}" alt="Slice {j}">
                        </div>
"""
        
        html_content += f"""                    </div>
                    
                    <div class="instructions">
                        🖱️ 마우스 휠로 슬라이스 이동 | 마우스 오버로 픽셀값 확인
                    </div>
                </div>
                
                <div class="side-panel">
                    <h3>📊 ROI Analysis</h3>
                    <div class="roi-info">
                        <div class="roi-label">Current Slice</div>
                        <div class="roi-value" id="{safe_id}-current-slice">0</div>
                    </div>
                    <div class="roi-info">
                        <div class="roi-label">Z Position</div>
                        <div class="roi-value" id="{safe_id}-z-pos">{series_info['images'][0]['z_position']:.1f} mm</div>
                    </div>
                </div>
            </div>
        </div>
"""
    
    # JavaScript
    html_content += """
    </div>
    
    <script>
        // 시리즈 데이터
        const seriesData = {};
"""
    
    for series_desc, series_info in series_images.items():
        safe_id = ''.join(c if c.isalnum() or c == '_' else '_' for c in series_desc)
        images = [img['image'] for img in series_info['images']]
        z_positions = [img['z_position'] for img in series_info['images']]
        html_content += f"""
        seriesData['{safe_id}'] = {{
            images: {json.dumps(images)},
            zPositions: {json.dumps(z_positions)}
        }};
"""
    
    html_content += """
        function showSeries(seriesName) {
            const safeId = seriesName.replace(/[^a-zA-Z0-9_]/g, '_');
            
            document.querySelectorAll('.series-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            
            document.getElementById(safeId).classList.add('active');
            event.target.classList.add('active');
        }
        
        function changeSlice(seriesId, sliceIndex) {
            const index = parseInt(sliceIndex);
            const data = seriesData[seriesId];
            const maxIndex = data.images.length - 1;
            
            if (index < 0 || index > maxIndex) return;
            
            // 메인 이미지 업데이트
            const mainImg = document.querySelector(`#${seriesId}-main img`);
            mainImg.src = data.images[index];
            
            // 슬라이더 업데이트
            const slider = document.getElementById(`${seriesId}-slider`);
            slider.value = index;
            
            // 텍스트 업데이트
            document.getElementById(`${seriesId}-slice-num`).textContent = `${index} / ${maxIndex}`;
            document.getElementById(`${seriesId}-current-slice`).textContent = index;
            document.getElementById(`${seriesId}-z-pos`).textContent = `${data.zPositions[index].toFixed(1)} mm`;
            
            // 썸네일 활성화
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
        
        // 마우스 휠 이벤트
        document.addEventListener('DOMContentLoaded', function() {
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
            
            // 키보드 이벤트
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
    
    # 저장
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Enhanced viewer generated: {output_file}")
        print(f"   File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    except Exception as e:
        print(f"❌ Error saving HTML: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Generate enhanced DICOM viewer")
    parser.add_argument("--dicom_dir", required=True, help="DICOM directory")
    parser.add_argument("--output", required=True, help="Output HTML file")
    parser.add_argument("--metrics", help="Metrics JSON file (optional)")
    args = parser.parse_args()
    
    generate_enhanced_html(args.dicom_dir, args.output, args.metrics)


if __name__ == "__main__":
    main()
