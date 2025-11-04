#!/usr/bin/env python3
"""
Generate Web Viewer Data
NIfTI 데이터를 웹 뷰어용 JSON으로 변환
"""
import argparse
import json
import numpy as np
import nibabel as nib
from pathlib import Path
import base64
from PIL import Image
import io


def apply_colormap(normalized, colormap='jet', mask=None):
    """컬러맵 적용
    
    Args:
        normalized: 0-255 normalized array
        colormap: 'jet', 'hot', 'rainbow'
        mask: Boolean mask (True = valid tissue, False = background)
    
    Returns:
        RGB image array
    """
    # Jet colormap (파랑-청록-초록-노랑-빨강)
    if colormap == 'jet':
        # 0-255 값을 RGB로 변환
        rgb = np.zeros((*normalized.shape, 3), dtype=np.uint8)
        
        for i in range(normalized.shape[0]):
            for j in range(normalized.shape[1]):
                # 마스크 체크: 배경은 검정색
                if mask is not None and not mask[i, j]:
                    rgb[i, j] = [0, 0, 0]
                    continue
                
                val = normalized[i, j]
                
                # 낮은 값도 배경으로 처리 (더 전문적인 표시)
                if val < 10:  # 매우 낮은 값 = 배경
                    rgb[i, j] = [0, 0, 0]
                elif val < 64:  # 보라-파랑 (낮은 관류)
                    # 보라색에서 시작
                    ratio = val / 64.0
                    rgb[i, j] = [int(128 * (1 - ratio)), 0, int(128 + 127 * ratio)]
                elif val < 128:  # 파랑-청록-초록
                    ratio = (val - 64) / 64.0
                    rgb[i, j] = [0, int(255 * ratio), int(255 * (1 - ratio))]
                elif val < 192:  # 초록-노랑
                    ratio = (val - 128) / 64.0
                    rgb[i, j] = [int(255 * ratio), 255, 0]
                else:  # 노랑-빨강 (높은 관류/지연)
                    ratio = (val - 192) / 63.0
                    rgb[i, j] = [255, int(255 * (1 - ratio)), 0]
        
        return rgb
    
    # Hot colormap (검정-빨강-노랑-흰색)
    elif colormap == 'hot':
        rgb = np.zeros((*normalized.shape, 3), dtype=np.uint8)
        
        for i in range(normalized.shape[0]):
            for j in range(normalized.shape[1]):
                val = normalized[i, j]
                
                if val < 85:
                    rgb[i, j] = [val * 3, 0, 0]
                elif val < 170:
                    rgb[i, j] = [255, (val - 85) * 3, 0]
                else:
                    rgb[i, j] = [255, 255, (val - 170) * 3]
        
        return rgb
    
    # Rainbow colormap
    elif colormap == 'rainbow':
        rgb = np.zeros((*normalized.shape, 3), dtype=np.uint8)
        
        for i in range(normalized.shape[0]):
            for j in range(normalized.shape[1]):
                val = normalized[i, j]
                
                if val < 51:  # 보라
                    rgb[i, j] = [128 + val * 2, 0, 255]
                elif val < 102:  # 파랑
                    rgb[i, j] = [0, 0, 255]
                elif val < 153:  # 초록
                    rgb[i, j] = [0, 255, 0]
                elif val < 204:  # 노랑
                    rgb[i, j] = [255, 255, 0]
                else:  # 빨강
                    rgb[i, j] = [255, 0, 0]
        
        return rgb
    
    else:  # grayscale
        return np.stack([normalized] * 3, axis=-1)


def nifti_slice_to_base64(data, slice_idx, colormap='gray', vmin=None, vmax=None):
    """NIfTI 슬라이스를 base64 PNG로 변환
    
    Args:
        data: 3D numpy array
        slice_idx: 슬라이스 인덱스
        colormap: 컬러맵 ('gray', 'jet', 'hot', 'rainbow')
        vmin, vmax: 값 범위
    
    Returns:
        base64 encoded PNG string
    """
    slice_data = data[slice_idx, :, :]
    
    # 정규화
    if vmin is None:
        vmin = slice_data.min()
    if vmax is None:
        vmax = slice_data.max()
    
    if vmax > vmin:
        normalized = ((slice_data - vmin) / (vmax - vmin) * 255).astype(np.uint8)
    else:
        normalized = np.zeros_like(slice_data, dtype=np.uint8)
    
    # 컬러맵 적용
    rgb_array = apply_colormap(normalized, colormap)
    
    # PIL Image로 변환
    img = Image.fromarray(rgb_array, 'RGB')
    
    # PNG로 저장
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Base64 인코딩
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"


def generate_viewer_data(nifti_dir, metrics_file, output_dir):
    """웹 뷰어용 데이터 생성
    
    Args:
        nifti_dir: NIfTI 파일 디렉토리
        metrics_file: metrics.json 파일 경로
        output_dir: 출력 디렉토리
    """
    print("[Web Viewer] Generating viewer data...")
    
    nifti_dir = Path(nifti_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 파일 찾기
    files = {}
    for nifti_file in nifti_dir.glob("*.nii.gz"):
        name_lower = nifti_file.name.lower()
        if 'cbf' in name_lower and 'rcbf' not in name_lower:
            files['cbf'] = nifti_file
        elif 'cbv' in name_lower and 'rcbv' not in name_lower:
            files['cbv'] = nifti_file
        elif 'mtt' in name_lower:
            files['mtt'] = nifti_file
        elif 'tmax' in name_lower:
            files['tmax'] = nifti_file
    
    # 메트릭스 로드
    metrics = {}
    if metrics_file and Path(metrics_file).exists():
        with open(metrics_file, 'r', encoding='utf-8') as f:
            metrics = json.load(f)
    
    # 각 시리즈별 데이터 생성
    viewer_data = {
        'series': {},
        'metrics': metrics,
        'patient_info': {
            'name': 'UNKNOWN',
            'study_date': '2024-04-23'
        }
    }
    
    for series_name, filepath in files.items():
        print(f"  [Processing] {series_name.upper()}...")
        
        img = nib.load(filepath)
        data = img.get_fdata()
        
        num_slices = data.shape[0]
        
        # 각 슬라이스를 base64로 변환 (모든 슬라이스는 용량이 크므로 샘플링)
        # 실제로는 서버에서 동적으로 로드하는 것이 좋음
        slices = []
        
        # 대표 슬라이스만 저장 (5개 간격)
        sample_indices = list(range(0, num_slices, 5))
        if num_slices - 1 not in sample_indices:
            sample_indices.append(num_slices - 1)
        
        for idx in sample_indices:
            # 슬라이스를 PNG로 저장
            slice_data = data[idx, :, :]
            
            # 뇌 조직 마스크 생성 (임계값 기반)
            # 데이터의 하위 5% 값을 배경으로 간주
            threshold = np.percentile(slice_data[slice_data > 0], 5) if np.any(slice_data > 0) else 0
            tissue_mask = slice_data > threshold
            
            # 정규화 (뇌 조직 영역만)
            if tissue_mask.any():
                tissue_values = slice_data[tissue_mask]
                vmin = tissue_values.min()
                vmax = np.percentile(tissue_values, 99)  # 상위 1% 이상값 제외
            else:
                vmin = slice_data.min()
                vmax = slice_data.max()
            
            if vmax > vmin:
                normalized = np.clip((slice_data - vmin) / (vmax - vmin) * 255, 0, 255).astype(np.uint8)
            else:
                normalized = np.zeros_like(slice_data, dtype=np.uint8)
            
            # 컬러맵 적용 (Jet colormap for medical imaging)
            rgb_array = apply_colormap(normalized, 'jet', mask=tissue_mask)
            
            # PNG 파일로 저장
            img_pil = Image.fromarray(rgb_array, 'RGB')
            png_path = output_dir / f"{series_name}_slice_{idx:03d}.png"
            img_pil.save(png_path)
            
            slices.append({
                'index': idx,
                'path': f"{series_name}_slice_{idx:03d}.png"
            })
        
        viewer_data['series'][series_name] = {
            'name': series_name.upper(),
            'description': get_series_description(series_name),
            'num_slices': num_slices,
            'shape': list(data.shape),
            'vmin': float(data.min()),
            'vmax': float(data.max()),
            'slices': slices
        }
    
    # JSON 저장
    json_path = output_dir / 'viewer_data.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(viewer_data, f, indent=2)
    
    print(f"[OK] Viewer data saved: {json_path}")
    
    # HTML 파일 복사 및 수정
    generate_viewer_html(output_dir, viewer_data)
    
    return json_path


def get_series_description(series_name):
    """시리즈 설명 반환"""
    descriptions = {
        'cbf': 'Cerebral Blood Flow (ml/100g/min)',
        'cbv': 'Cerebral Blood Volume (ml/100g)',
        'mtt': 'Mean Transit Time (s)',
        'tmax': 'Time to Maximum (s)'
    }
    return descriptions.get(series_name, series_name.upper())


def generate_viewer_html(output_dir, viewer_data):
    """웹 뷰어 HTML 생성 - Apple 스타일"""
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CT Perfusion Viewer</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
            background: #000000;
            color: #f5f5f7;
            overflow: hidden;
            cursor: default;
        }}
        
        .header {{
            background: rgba(29, 29, 31, 0.95);
            backdrop-filter: saturate(180%) blur(20px);
            padding: 16px 24px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .header-left {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .header h1 {{
            font-size: 20px;
            font-weight: 600;
            letter-spacing: -0.5px;
            color: #f5f5f7;
        }}
        
        .header-info {{
            font-size: 13px;
            color: #86868b;
            font-weight: 400;
        }}
        
        .container {{
            display: flex;
            height: calc(100vh - 65px);
        }}
        
        .sidebar {{
            width: 200px;
            background: rgba(29, 29, 31, 0.95);
            backdrop-filter: saturate(180%) blur(20px);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px 16px;
            overflow-y: auto;
        }}
        
        .sidebar::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .sidebar::-webkit-scrollbar-track {{
            background: transparent;
        }}
        
        .sidebar::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
        }}
        
        .sidebar h3 {{
            font-size: 13px;
            font-weight: 600;
            color: #86868b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }}
        
        .series-btn {{
            width: 100%;
            background: rgba(255, 255, 255, 0.05);
            color: #f5f5f7;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 10px 14px;
            margin-bottom: 8px;
            border-radius: 8px;
            cursor: pointer;
            text-align: left;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .series-btn:hover {{
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
        }}
        
        .series-btn.active {{
            background: #0071e3;
            border-color: #0071e3;
            color: #ffffff;
        }}
        
        .viewer {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: #000000;
            padding: 40px;
            position: relative;
        }}
        
        #imageCanvas {{
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            cursor: crosshair;
        }}
        
        .toolbar {{
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(29, 29, 31, 0.95);
            backdrop-filter: saturate(180%) blur(20px);
            padding: 12px 20px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            gap: 12px;
            align-items: center;
        }}
        
        .tool-btn {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #f5f5f7;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        .tool-btn:hover {{
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
        }}
        
        .tool-btn.active {{
            background: #0071e3;
            border-color: #0071e3;
            color: #ffffff;
        }}
        
        .color-picker {{
            width: 32px;
            height: 32px;
            border-radius: 6px;
            border: 2px solid rgba(255, 255, 255, 0.2);
            cursor: pointer;
        }}
        
        .export-btn {{
            background: #0071e3;
            border: none;
            color: #ffffff;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
        }}
        
        .export-btn:hover {{
            background: #0077ed;
            transform: translateY(-1px);
        }}
        
        .controls {{
            position: absolute;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(29, 29, 31, 0.95);
            backdrop-filter: saturate(180%) blur(20px);
            padding: 16px 32px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            gap: 20px;
            min-width: 400px;
        }}
        
        .slice-info {{
            font-size: 14px;
            font-weight: 500;
            color: #f5f5f7;
            min-width: 80px;
        }}
        
        .slice-number {{
            color: #0071e3;
            font-weight: 600;
        }}
        
        input[type="range"] {{
            flex: 1;
            height: 4px;
            border-radius: 2px;
            background: rgba(255, 255, 255, 0.1);
            outline: none;
            -webkit-appearance: none;
        }}
        
        input[type="range"]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #0071e3;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0, 113, 227, 0.5);
            transition: all 0.2s;
        }}
        
        input[type="range"]::-webkit-slider-thumb:hover {{
            transform: scale(1.2);
            box-shadow: 0 4px 12px rgba(0, 113, 227, 0.7);
        }}
        
        input[type="range"]::-moz-range-thumb {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #0071e3;
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 8px rgba(0, 113, 227, 0.5);
        }}
        
        .metrics {{
            width: 280px;
            background: rgba(29, 29, 31, 0.95);
            backdrop-filter: saturate(180%) blur(20px);
            border-left: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px 16px;
            overflow-y: auto;
        }}
        
        .metrics::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .metrics::-webkit-scrollbar-track {{
            background: transparent;
        }}
        
        .metrics::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
        }}
        
        .metrics h3 {{
            font-size: 13px;
            font-weight: 600;
            color: #86868b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 16px;
        }}
        
        .metric-item {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 14px;
            margin-bottom: 10px;
            border-radius: 10px;
            transition: all 0.2s;
        }}
        
        .metric-item:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.15);
        }}
        
        .metric-label {{
            font-size: 11px;
            color: #86868b;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}
        
        .metric-value {{
            font-size: 18px;
            font-weight: 600;
            color: #0071e3;
            font-variant-numeric: tabular-nums;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <h1>CT Perfusion Viewer</h1>
        </div>
        <div class="header-info">
            Patient: {viewer_data['patient_info']['name']} • {viewer_data['patient_info']['study_date']}
        </div>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <h3>Series</h3>
            <div id="seriesButtons"></div>
        </div>
        
        <div class="viewer">
            <div class="toolbar">
                <button class="tool-btn active" id="toolDraw">✏️ Draw</button>
                <button class="tool-btn" id="toolArrow">➡️ Arrow</button>
                <button class="tool-btn" id="toolCircle">⭕ Circle</button>
                <button class="tool-btn" id="toolRect">▭ Rect</button>
                <button class="tool-btn" id="toolText">📝 Text</button>
                <input type="color" id="colorPicker" class="color-picker" value="#ff0000">
                <button class="tool-btn" id="toolClear">🗑️ Clear</button>
                <button class="export-btn" id="exportBtn">💾 Export</button>
            </div>
            <canvas id="imageCanvas"></canvas>
            <div class="controls">
                <div class="slice-info">
                    Slice <span class="slice-number" id="sliceLabel">1</span>
                </div>
                <input type="range" id="sliceSlider" min="0" max="32" value="16">
            </div>
        </div>
        
        <div class="metrics">
            <h3>Metrics</h3>
            <div id="metricsPanel"></div>
        </div>
    </div>
    
    <script>
        const viewerData = {json.dumps(viewer_data, indent=2)};
        
        let currentSeries = 'cbf';
        let currentSlice = 16;
        
        // Canvas setup
        const canvas = document.getElementById('imageCanvas');
        const ctx = canvas.getContext('2d');
        let currentImage = new Image();
        let annotations = [];
        let isDrawing = false;
        let isDragging = false;
        let startX, startY;
        let currentTool = 'draw';
        let currentColor = '#ff0000';
        let drawPath = [];
        let selectedAnnotation = null;
        let dragOffsetX = 0;
        let dragOffsetY = 0;
        let hoverAnnotation = null;
        
        // 시리즈 버튼 생성
        const seriesButtons = document.getElementById('seriesButtons');
        for (const [key, series] of Object.entries(viewerData.series)) {{
            const btn = document.createElement('button');
            btn.className = 'series-btn' + (key === currentSeries ? ' active' : '');
            btn.textContent = series.name;
            btn.onclick = () => loadSeries(key);
            seriesButtons.appendChild(btn);
        }}
        
        // 메트릭스 표시
        const metricsPanel = document.getElementById('metricsPanel');
        if (viewerData.metrics) {{
            for (const [key, value] of Object.entries(viewerData.metrics)) {{
                const div = document.createElement('div');
                div.className = 'metric-item';
                div.innerHTML = `
                    <div class="metric-label">${{key}}</div>
                    <div class="metric-value">${{value}}</div>
                `;
                metricsPanel.appendChild(div);
            }}
        }}
        
        // 슬라이스 슬라이더
        const sliceSlider = document.getElementById('sliceSlider');
        sliceSlider.addEventListener('input', function() {{
            currentSlice = parseInt(this.value);
            document.getElementById('sliceLabel').textContent = currentSlice + 1;
            updateImage();
        }});
        
        // Canvas 크기 설정 및 이미지 그리기
        function resizeCanvas() {{
            const viewerDiv = document.querySelector('.viewer');
            const maxWidth = viewerDiv.clientWidth - 80;
            const maxHeight = viewerDiv.clientHeight - 200;
            
            if (currentImage.complete && currentImage.naturalWidth > 0) {{
                const imgRatio = currentImage.naturalWidth / currentImage.naturalHeight;
                let canvasWidth = maxWidth;
                let canvasHeight = canvasWidth / imgRatio;
                
                if (canvasHeight > maxHeight) {{
                    canvasHeight = maxHeight;
                    canvasWidth = canvasHeight * imgRatio;
                }}
                
                canvas.width = canvasWidth;
                canvas.height = canvasHeight;
                redrawCanvas();
            }}
        }}
        
        function redrawCanvas() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            if (currentImage.complete) {{
                ctx.drawImage(currentImage, 0, 0, canvas.width, canvas.height);
            }}
            
            // 주석 다시 그리기
            annotations.forEach((ann, idx) => {{
                const isSelected = selectedAnnotation === idx;
                const isHovered = hoverAnnotation === idx;
                
                ctx.strokeStyle = ann.color;
                ctx.fillStyle = ann.color;
                ctx.lineWidth = isSelected ? 5 : 3;
                
                if (ann.type === 'draw') {{
                    ctx.beginPath();
                    ann.path.forEach((point, i) => {{
                        if (i === 0) ctx.moveTo(point.x, point.y);
                        else ctx.lineTo(point.x, point.y);
                    }});
                    ctx.stroke();
                }} else if (ann.type === 'arrow') {{
                    drawArrow(ann.x1, ann.y1, ann.x2, ann.y2);
                }} else if (ann.type === 'circle') {{
                    const radius = Math.sqrt(Math.pow(ann.x2 - ann.x1, 2) + Math.pow(ann.y2 - ann.y1, 2));
                    ctx.beginPath();
                    ctx.arc(ann.x1, ann.y1, radius, 0, 2 * Math.PI);
                    ctx.stroke();
                }} else if (ann.type === 'rect') {{
                    ctx.strokeRect(ann.x1, ann.y1, ann.x2 - ann.x1, ann.y2 - ann.y1);
                }} else if (ann.type === 'text') {{
                    ctx.font = '20px -apple-system, sans-serif';
                    ctx.fillText(ann.text, ann.x, ann.y);
                    
                    // 텍스트 박스 표시
                    const textWidth = ctx.measureText(ann.text).width;
                    ctx.strokeStyle = ann.color;
                    ctx.lineWidth = 2;
                    ctx.strokeRect(ann.x - 5, ann.y - 25, textWidth + 10, 30);
                }}
                
                // 선택된 주석 하이라이트
                if (isSelected || isHovered) {{
                    ctx.strokeStyle = '#00ff00';
                    ctx.lineWidth = 2;
                    ctx.setLineDash([5, 5]);
                    
                    if (ann.type === 'draw') {{
                        const bounds = getDrawBounds(ann.path);
                        ctx.strokeRect(bounds.minX - 5, bounds.minY - 5, bounds.maxX - bounds.minX + 10, bounds.maxY - bounds.minY + 10);
                    }} else if (ann.type === 'arrow' || ann.type === 'circle' || ann.type === 'rect') {{
                        const minX = Math.min(ann.x1, ann.x2);
                        const minY = Math.min(ann.y1, ann.y2);
                        const maxX = Math.max(ann.x1, ann.x2);
                        const maxY = Math.max(ann.y1, ann.y2);
                        ctx.strokeRect(minX - 5, minY - 5, maxX - minX + 10, maxY - minY + 10);
                    }} else if (ann.type === 'text') {{
                        const textWidth = ctx.measureText(ann.text).width;
                        ctx.strokeRect(ann.x - 10, ann.y - 30, textWidth + 20, 40);
                    }}
                    
                    ctx.setLineDash([]);
                }}
            }});
        }}
        
        function getDrawBounds(path) {{
            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
            path.forEach(p => {{
                minX = Math.min(minX, p.x);
                minY = Math.min(minY, p.y);
                maxX = Math.max(maxX, p.x);
                maxY = Math.max(maxY, p.y);
            }});
            return {{ minX, minY, maxX, maxY }};
        }}
        
        function findAnnotationAt(x, y) {{
            for (let i = annotations.length - 1; i >= 0; i--) {{
                const ann = annotations[i];
                
                if (ann.type === 'draw') {{
                    const bounds = getDrawBounds(ann.path);
                    if (x >= bounds.minX - 5 && x <= bounds.maxX + 5 && y >= bounds.minY - 5 && y <= bounds.maxY + 5) {{
                        return i;
                    }}
                }} else if (ann.type === 'arrow' || ann.type === 'circle' || ann.type === 'rect') {{
                    const minX = Math.min(ann.x1, ann.x2) - 5;
                    const minY = Math.min(ann.y1, ann.y2) - 5;
                    const maxX = Math.max(ann.x1, ann.x2) + 5;
                    const maxY = Math.max(ann.y1, ann.y2) + 5;
                    if (x >= minX && x <= maxX && y >= minY && y <= maxY) {{
                        return i;
                    }}
                }} else if (ann.type === 'text') {{
                    const textWidth = ctx.measureText(ann.text).width;
                    if (x >= ann.x - 5 && x <= ann.x + textWidth + 5 && y >= ann.y - 25 && y <= ann.y + 5) {{
                        return i;
                    }}
                }}
            }}
            return null;
        }}
        
        function drawArrow(x1, y1, x2, y2) {{
            const headlen = 15;
            const angle = Math.atan2(y2 - y1, x2 - x1);
            
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.lineTo(x2 - headlen * Math.cos(angle - Math.PI / 6), y2 - headlen * Math.sin(angle - Math.PI / 6));
            ctx.moveTo(x2, y2);
            ctx.lineTo(x2 - headlen * Math.cos(angle + Math.PI / 6), y2 - headlen * Math.sin(angle + Math.PI / 6));
            ctx.stroke();
        }}
        
        // 마우스 이벤트
        canvas.addEventListener('mousedown', (e) => {{
            const rect = canvas.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
            
            // 기존 주석 선택 확인
            const clickedAnn = findAnnotationAt(startX, startY);
            
            if (clickedAnn !== null) {{
                // 드래그 시작
                selectedAnnotation = clickedAnn;
                isDragging = true;
                const ann = annotations[clickedAnn];
                
                if (ann.type === 'draw') {{
                    const bounds = getDrawBounds(ann.path);
                    dragOffsetX = startX - bounds.minX;
                    dragOffsetY = startY - bounds.minY;
                }} else if (ann.type === 'text') {{
                    dragOffsetX = startX - ann.x;
                    dragOffsetY = startY - ann.y;
                }} else {{
                    dragOffsetX = startX - ann.x1;
                    dragOffsetY = startY - ann.y1;
                }}
                
                canvas.style.cursor = 'move';
                redrawCanvas();
            }} else {{
                // 새로운 주석 그리기
                selectedAnnotation = null;
                isDrawing = true;
                
                if (currentTool === 'draw') {{
                    drawPath = [{{x: startX, y: startY}}];
                }} else if (currentTool === 'text') {{
                    const text = prompt('텍스트를 입력하세요:');
                    if (text) {{
                        annotations.push({{
                            type: 'text',
                            text: text,
                            x: startX,
                            y: startY,
                            color: currentColor
                        }});
                        redrawCanvas();
                    }}
                    isDrawing = false;
                }}
            }}
        }});
        
        canvas.addEventListener('mousemove', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const currentX = e.clientX - rect.left;
            const currentY = e.clientY - rect.top;
            
            if (isDragging && selectedAnnotation !== null) {{
                // 드래그 중
                const ann = annotations[selectedAnnotation];
                
                if (ann.type === 'draw') {{
                    const bounds = getDrawBounds(ann.path);
                    const deltaX = currentX - dragOffsetX - bounds.minX;
                    const deltaY = currentY - dragOffsetY - bounds.minY;
                    ann.path = ann.path.map(p => ({{ x: p.x + deltaX, y: p.y + deltaY }}));
                }} else if (ann.type === 'text') {{
                    ann.x = currentX - dragOffsetX;
                    ann.y = currentY - dragOffsetY;
                }} else {{
                    const deltaX = currentX - dragOffsetX - ann.x1;
                    const deltaY = currentY - dragOffsetY - ann.y1;
                    ann.x1 += deltaX;
                    ann.y1 += deltaY;
                    ann.x2 += deltaX;
                    ann.y2 += deltaY;
                }}
                
                redrawCanvas();
            }} else if (isDrawing && currentTool !== 'text') {{
                // 새로운 주석 그리기
                if (currentTool === 'draw') {{
                    drawPath.push({{x: currentX, y: currentY}});
                    redrawCanvas();
                    ctx.strokeStyle = currentColor;
                    ctx.lineWidth = 3;
                    ctx.beginPath();
                    drawPath.forEach((point, i) => {{
                        if (i === 0) ctx.moveTo(point.x, point.y);
                        else ctx.lineTo(point.x, point.y);
                    }});
                    ctx.stroke();
                }} else {{
                    redrawCanvas();
                    ctx.strokeStyle = currentColor;
                    ctx.lineWidth = 3;
                    
                    if (currentTool === 'arrow') {{
                        drawArrow(startX, startY, currentX, currentY);
                    }} else if (currentTool === 'circle') {{
                        const radius = Math.sqrt(Math.pow(currentX - startX, 2) + Math.pow(currentY - startY, 2));
                        ctx.beginPath();
                        ctx.arc(startX, startY, radius, 0, 2 * Math.PI);
                        ctx.stroke();
                    }} else if (currentTool === 'rect') {{
                        ctx.strokeRect(startX, startY, currentX - startX, currentY - startY);
                    }}
                }}
            }} else {{
                // 호버 감지
                const hoveredAnn = findAnnotationAt(currentX, currentY);
                if (hoveredAnn !== hoverAnnotation) {{
                    hoverAnnotation = hoveredAnn;
                    canvas.style.cursor = hoveredAnn !== null ? 'pointer' : 'crosshair';
                    redrawCanvas();
                }}
            }}
        }});
        
        canvas.addEventListener('mouseup', (e) => {{
            if (isDragging) {{
                isDragging = false;
                canvas.style.cursor = 'crosshair';
                redrawCanvas();
            }} else if (isDrawing && currentTool !== 'text') {{
                const rect = canvas.getBoundingClientRect();
                const endX = e.clientX - rect.left;
                const endY = e.clientY - rect.top;
                
                if (currentTool === 'draw') {{
                    annotations.push({{
                        type: 'draw',
                        path: drawPath,
                        color: currentColor
                    }});
                }} else if (currentTool === 'arrow') {{
                    annotations.push({{
                        type: 'arrow',
                        x1: startX,
                        y1: startY,
                        x2: endX,
                        y2: endY,
                        color: currentColor
                    }});
                }} else if (currentTool === 'circle') {{
                    annotations.push({{
                        type: 'circle',
                        x1: startX,
                        y1: startY,
                        x2: endX,
                        y2: endY,
                        color: currentColor
                    }});
                }} else if (currentTool === 'rect') {{
                    annotations.push({{
                        type: 'rect',
                        x1: startX,
                        y1: startY,
                        x2: endX,
                        y2: endY,
                        color: currentColor
                    }});
                }}
                
                isDrawing = false;
                redrawCanvas();
            }}
        }});
        
        // 툴바 버튼 이벤트
        document.querySelectorAll('.tool-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                if (this.id === 'toolClear') {{
                    annotations = [];
                    selectedAnnotation = null;
                    hoverAnnotation = null;
                    redrawCanvas();
                }} else {{
                    document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    
                    if (this.id === 'toolDraw') currentTool = 'draw';
                    else if (this.id === 'toolArrow') currentTool = 'arrow';
                    else if (this.id === 'toolCircle') currentTool = 'circle';
                    else if (this.id === 'toolRect') currentTool = 'rect';
                    else if (this.id === 'toolText') currentTool = 'text';
                }}
            }});
        }});
        
        document.getElementById('colorPicker').addEventListener('change', (e) => {{
            currentColor = e.target.value;
        }});
        
        document.getElementById('exportBtn').addEventListener('click', () => {{
            const link = document.createElement('a');
            link.download = `ct_perfusion_slice_${{currentSlice + 1}}_annotated.png`;
            link.href = canvas.toDataURL();
            link.click();
        }});
        
        // 마우스 휠 이벤트 (전체 화면에서 작동)
        document.addEventListener('wheel', function(e) {{
            e.preventDefault();
            
            const series = viewerData.series[currentSeries];
            if (!series) return;
            
            // 휠 방향에 따라 슬라이스 변경
            if (e.deltaY < 0) {{
                // 휠 올림 - 슬라이스 증가
                currentSlice = Math.min(currentSlice + 1, series.num_slices - 1);
            }} else {{
                // 휠 내림 - 슬라이스 감소
                currentSlice = Math.max(currentSlice - 1, 0);
            }}
            
            // UI 업데이트
            sliceSlider.value = currentSlice;
            document.getElementById('sliceLabel').textContent = currentSlice + 1;
            updateImage();
        }}, {{ passive: false }});
        
        function loadSeries(seriesKey) {{
            currentSeries = seriesKey;
            document.querySelectorAll('.series-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            updateImage();
        }}
        
        function updateImage() {{
            const series = viewerData.series[currentSeries];
            if (!series) return;
            
            // 가장 가까운 슬라이스 찾기
            let closestSlice = series.slices[0];
            let minDiff = Math.abs(closestSlice.index - currentSlice);
            
            for (const slice of series.slices) {{
                const diff = Math.abs(slice.index - currentSlice);
                if (diff < minDiff) {{
                    minDiff = diff;
                    closestSlice = slice;
                }}
            }}
            
            // Canvas에 이미지 로드
            currentImage.onload = function() {{
                resizeCanvas();
            }};
            currentImage.src = closestSlice.path;
            
            // 슬라이스 변경 시 주석 초기화
            annotations = [];
        }}
        
        // 윈도우 리사이즈 이벤트
        window.addEventListener('resize', resizeCanvas);
        
        // 초기 이미지 로드
        updateImage();
    </script>
</body>
</html>
"""
    
    html_path = output_dir / 'viewer.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[OK] Viewer HTML saved: {html_path}")


def main():
    ap = argparse.ArgumentParser(description="Generate Web Viewer Data")
    ap.add_argument("--nifti_dir", required=True, help="NIfTI files directory")
    ap.add_argument("--metrics", help="metrics.json file path")
    ap.add_argument("--output_dir", default="web_viewer_data", help="Output directory")
    args = ap.parse_args()
    
    generate_viewer_data(args.nifti_dir, args.metrics, args.output_dir)


if __name__ == "__main__":
    main()
