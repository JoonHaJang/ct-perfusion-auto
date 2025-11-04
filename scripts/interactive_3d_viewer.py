#!/usr/bin/env python3
"""
Interactive 3D Viewer using nilearn and plotly
브라우저에서 전문적인 3D 시각화
"""
import argparse
import numpy as np
import nibabel as nib
from nilearn import plotting, surface
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import webbrowser
from pathlib import Path


def create_nilearn_viewer(tmax_path, core_path=None, penumbra_path=None, output_html="viewer_3d.html"):
    """nilearn을 사용한 인터랙티브 뷰어 생성
    
    Args:
        tmax_path: Tmax NIfTI 파일
        core_path: Infarct core 마스크
        penumbra_path: Penumbra 마스크
        output_html: 출력 HTML 파일명
    """
    print("[3D] nilearn 3D viewer creating...")
    
    # HTML 시작
    html_parts = []
    html_parts.append("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>CT Perfusion 3D Viewer</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            h1 { color: #2c3e50; }
            .viewer-container { 
                background: white; 
                padding: 20px; 
                margin: 10px 0; 
                border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .info { 
                background: #e3f2fd; 
                padding: 15px; 
                border-left: 4px solid #2196F3; 
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <h1>🧠 CT Perfusion 3D Interactive Viewer</h1>
        <div class="info">
            <strong>사용법:</strong> 마우스로 드래그하여 회전, 스크롤로 확대/축소
        </div>
    """)
    
    # 1. Tmax 배경 이미지
    if tmax_path:
        print("  [Tmax] Slice view creating...")
        html_parts.append('<div class="viewer-container">')
        html_parts.append('<h2>Tmax Map (Orthogonal Views)</h2>')
        
        # nilearn plotting으로 PNG 생성
        display = plotting.plot_anat(
            tmax_path,
            display_mode='ortho',
            cut_coords=(0, 0, 0),
            title='Tmax',
            draw_cross=False,
            annotate=True,
            cmap='hot'
        )
        
        temp_img = "temp_tmax_ortho.png"
        display.savefig(temp_img, dpi=150)
        display.close()
        
        # PNG를 base64로 인코딩하여 HTML에 삽입
        import base64
        with open(temp_img, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        
        html_parts.append(f'<img src="data:image/png;base64,{img_data}" style="width:100%; max-width:800px;">')
        html_parts.append('</div>')
        
        Path(temp_img).unlink()  # 임시 파일 삭제
    
    # 2. Penumbra 오버레이
    if penumbra_path and tmax_path:
        print("  [Penumbra] Overlay creating...")
        html_parts.append('<div class="viewer-container">')
        html_parts.append('<h2>Penumbra (Green) Overlay</h2>')
        
        display = plotting.plot_roi(
            penumbra_path,
            bg_img=tmax_path,
            display_mode='ortho',
            cut_coords=(0, 0, 0),
            title='Penumbra',
            cmap='Greens',
            alpha=0.5,
            draw_cross=False
        )
        
        temp_img = "temp_penumbra.png"
        display.savefig(temp_img, dpi=150)
        display.close()
        
        with open(temp_img, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        
        html_parts.append(f'<img src="data:image/png;base64,{img_data}" style="width:100%; max-width:800px;">')
        html_parts.append('</div>')
        
        Path(temp_img).unlink()
    
    # 3. Core 오버레이
    if core_path and tmax_path:
        print("  [Core] Overlay creating...")
        html_parts.append('<div class="viewer-container">')
        html_parts.append('<h2>Infarct Core (Red) Overlay</h2>')
        
        display = plotting.plot_roi(
            core_path,
            bg_img=tmax_path,
            display_mode='ortho',
            cut_coords=(0, 0, 0),
            title='Infarct Core',
            cmap='Reds',
            alpha=0.7,
            draw_cross=False
        )
        
        temp_img = "temp_core.png"
        display.savefig(temp_img, dpi=150)
        display.close()
        
        with open(temp_img, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        
        html_parts.append(f'<img src="data:image/png;base64,{img_data}" style="width:100%; max-width:800px;">')
        html_parts.append('</div>')
        
        Path(temp_img).unlink()
    
    # HTML 종료
    html_parts.append("""
    </body>
    </html>
    """)
    
    # HTML 파일 저장
    with open(output_html, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))
    
    print(f"[OK] HTML viewer created: {output_html}")
    return output_html


def create_plotly_3d_viewer(tmax_path, core_path=None, penumbra_path=None, output_html="viewer_3d_plotly.html"):
    """Plotly를 사용한 완전 인터랙티브 3D 뷰어
    
    Args:
        tmax_path: Tmax NIfTI 파일
        core_path: Infarct core 마스크
        penumbra_path: Penumbra 마스크
        output_html: 출력 HTML 파일명
    """
    print("[3D] Plotly interactive 3D viewer creating...")
    
    # 데이터 로드
    tmax_data = nib.load(tmax_path).get_fdata() if tmax_path else None
    core_data = nib.load(core_path).get_fdata() if core_path else None
    penumbra_data = nib.load(penumbra_path).get_fdata() if penumbra_path else None
    
    # Figure 생성
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'scatter3d'}, {'type': 'scatter3d'}]],
        subplot_titles=('Penumbra (Green)', 'Infarct Core (Red)')
    )
    
    # Penumbra 3D scatter
    if penumbra_data is not None:
        print("  [Penumbra] Extracting points...")
        coords = np.where(penumbra_data > 0)
        
        # 다운샘플링 (너무 많으면 느림)
        step = max(1, len(coords[0]) // 20000)
        
        fig.add_trace(
            go.Scatter3d(
                x=coords[2][::step],
                y=coords[1][::step],
                z=coords[0][::step],
                mode='markers',
                marker=dict(
                    size=2,
                    color='green',
                    opacity=0.3
                ),
                name='Penumbra',
                hovertemplate='X: %{x}<br>Y: %{y}<br>Z: %{z}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Core 3D scatter
    if core_data is not None:
        print("  [Core] Extracting points...")
        coords = np.where(core_data > 0)
        
        step = max(1, len(coords[0]) // 10000)
        
        fig.add_trace(
            go.Scatter3d(
                x=coords[2][::step],
                y=coords[1][::step],
                z=coords[0][::step],
                mode='markers',
                marker=dict(
                    size=3,
                    color='red',
                    opacity=0.6
                ),
                name='Infarct Core',
                hovertemplate='X: %{x}<br>Y: %{y}<br>Z: %{z}<extra></extra>'
            ),
            row=1, col=2
        )
    
    # 레이아웃 설정
    fig.update_layout(
        title={
            'text': '🧠 CT Perfusion 3D Interactive Viewer',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24}
        },
        showlegend=True,
        height=700,
        hovermode='closest',
        template='plotly_white'
    )
    
    # 축 설정
    for i in [1, 2]:
        fig.update_scenes(
            dict(
                xaxis=dict(title='X (Left-Right)'),
                yaxis=dict(title='Y (Posterior-Anterior)'),
                zaxis=dict(title='Z (Inferior-Superior)'),
                aspectmode='data'
            ),
            row=1, col=i
        )
    
    # HTML 저장
    fig.write_html(
        output_html,
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan3d', 'select3d', 'lasso3d']
        }
    )
    
    print(f"[OK] Plotly viewer created: {output_html}")
    return output_html


def main():
    ap = argparse.ArgumentParser(description="Interactive 3D Viewer")
    ap.add_argument("--tmax", help="Tmax NIfTI file")
    ap.add_argument("--core", help="Infarct core mask")
    ap.add_argument("--penumbra", help="Penumbra mask")
    ap.add_argument("--output", default="viewer_3d.html", help="Output HTML file")
    ap.add_argument("--plotly", action="store_true", help="Use Plotly instead of nilearn")
    ap.add_argument("--open", action="store_true", dest="open_browser", help="Open browser automatically")
    args = ap.parse_args()
    
    if args.plotly:
        # Plotly 인터랙티브 뷰어
        output_file = create_plotly_3d_viewer(
            args.tmax,
            args.core,
            args.penumbra,
            args.output
        )
    else:
        # nilearn 뷰어
        output_file = create_nilearn_viewer(
            args.tmax,
            args.core,
            args.penumbra,
            args.output
        )
    
    # 브라우저 자동 열기
    if args.open_browser:
        print(f"[Browser] Opening...")
        webbrowser.open(f'file://{Path(output_file).absolute()}')
    else:
        print(f"\n[File] Location: {Path(output_file).absolute()}")
        print(f"[Tip] Double-click the file to open in browser")


if __name__ == "__main__":
    main()
