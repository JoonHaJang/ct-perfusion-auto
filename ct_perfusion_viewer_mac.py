#!/usr/bin/env python3
"""
CT Perfusion One-Stop Analyzer
Folder Selection → Auto Analysis → Web Viewer
"""
import sys
import os
import json
import subprocess
from pathlib import Path
import webbrowser

# Qt 플랫폼 플러그인 경로 설정 (macOS .app 번들용)
if getattr(sys, 'frozen', False):
    # py2app으로 빌드된 경우
    bundle_dir = Path(sys.executable).parent.parent / 'Resources'
    platforms_dir = bundle_dir / 'platforms'
    if platforms_dir.exists():
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(platforms_dir)
        os.environ['QT_PLUGIN_PATH'] = str(bundle_dir)

# import numpy as np  # 2D/3D 렌더링 제거로 불필요
# import nibabel as nib  # 2D/3D 렌더링 제거로 불필요
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTextEdit, QProgressBar,
    QGroupBox, QTableWidget, QTableWidgetItem
    # QTabWidget, QComboBox, QSpinBox, QCheckBox, QSplitter  # 2D/3D 렌더링용 제거
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
# import matplotlib  # 2D/3D 렌더링 제거로 불필요
# matplotlib.use('Qt5Agg')
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.figure import Figure
# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D


class AnalysisWorker(QThread):
    """Background Analysis Thread"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, patient_dir, output_dir):
        super().__init__()
        self.patient_dir = patient_dir
        self.output_dir = output_dir
    
    def run(self):
        try:
            # 스크립트 경로 (PyInstaller 호환)
            if getattr(sys, 'frozen', False):
                # PyInstaller로 패키징된 경우
                application_path = Path(sys.executable).parent
            else:
                # 일반 Python 실행
                application_path = Path(__file__).parent
            
            script_dir = application_path / "scripts"
            
            result = {
                "patient_dir": str(self.patient_dir),
                "output_dir": str(self.output_dir),
                "status": "processing"
            }
            
            # 1. Extract metrics from DICOM + Save NIfTI
            self.progress.emit("🔄 Analyzing Siemens CT Perfusion data...")
            
            # Extract patient name
            patient_name = Path(self.patient_dir).name
            
            cmd = [
                sys.executable, str(script_dir / "extract_metrics_from_dicom.py"),
                "--dicom_dir", str(self.patient_dir),
                "--output_dir", str(self.output_dir),
                "--patient_name", patient_name,
                "--save_nifti"  # Save NIfTI for web viewer
            ]
            
            # PyInstaller: CREATE_NO_WINDOW flag to prevent console window
            startupinfo = None
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', startupinfo=startupinfo)
            if proc.returncode != 0:
                error_msg = proc.stderr if proc.stderr else proc.stdout
                raise Exception(f"Metric extraction failed: {error_msg}")
            
            self.progress.emit("✅ Metric extraction completed!")
            
            # 2. Load results
            self.progress.emit("📖 Loading results...")
            metrics_json = Path(self.output_dir) / "perfusion_metrics.json"
            
            if metrics_json.exists():
                with open(metrics_json, "r", encoding="utf-8") as f:
                    metrics_data = json.load(f)
                    result["metrics"] = metrics_data["metrics"]
                    result["tmax_metadata"] = metrics_data.get("tmax_metadata", {})
                    result["cbv_metadata"] = metrics_data.get("cbv_metadata", {})
            else:
                raise Exception("Result file not found")
            
            result["masks_file"] = str(Path(self.output_dir) / "masks.npz")
            
            # 2.5. Extract TAC from Penumbra images
            self.progress.emit("📊 Extracting TAC from Penumbra images...")
            
            # TAC 추출 스크립트 경로 확인
            tac_script = script_dir / "extract_tac_from_penumbra.py"
            
            if tac_script.exists():
                try:
                    tac_output_dir = Path(self.output_dir) / "tac_extracted"
                    cmd = [
                        sys.executable, str(tac_script),
                        str(self.patient_dir),
                        str(tac_output_dir)
                        # --slice 파라미터 없음 = 자동으로 마지막 슬라이스 선택
                    ]
                    
                    proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', startupinfo=startupinfo if sys.platform == 'win32' else None)
                    
                    if proc.returncode == 0:
                        # Load TAC results (파일명 동적 검색)
                        tac_json_files = list(tac_output_dir.glob("tac_digitized_*.json"))
                        if tac_json_files:
                            tac_json = tac_json_files[0]  # 첫 번째 파일 사용
                            with open(tac_json, "r", encoding="utf-8") as f:
                                tac_data = json.load(f)
                                result["tac"] = tac_data
                            
                            self.progress.emit("✅ TAC extraction completed!")
                        else:
                            self.progress.emit("⚠️ TAC result file not found")
                    else:
                        self.progress.emit("⚠️ TAC extraction failed, continuing...")
                except Exception as e:
                    self.progress.emit(f"⚠️ TAC extraction error: {str(e)}")
            else:
                self.progress.emit("⚠️ TAC extraction script not found, skipping...")
            
            # 3. Generate DICOM web viewer
            self.progress.emit("🌐 Generating DICOM viewer...")
            viewer_dir = Path(self.output_dir) / "viewer"
            
            cmd = [
                sys.executable, str(script_dir / "generate_dicom_viewer.py"),
                "--dicom_dir", str(self.patient_dir),
                "--metrics", str(metrics_json),
                "--output_dir", str(viewer_dir)
            ]
            
            # PyInstaller: CREATE_NO_WINDOW flag to prevent console window
            startupinfo = None
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', startupinfo=startupinfo)
            if proc.returncode != 0:
                self.progress.emit("⚠️ Web viewer generation failed (metrics are OK)")
                self.progress.emit("=" * 50)
                # Output stdout (debug messages)
                if proc.stdout:
                    for line in proc.stdout.split('\n')[:20]:  # First 20 lines
                        if line.strip():
                            self.progress.emit(line)
                # Output stderr (error messages)
                if proc.stderr:
                    self.progress.emit("--- ERROR ---")
                    for line in proc.stderr.split('\n')[:20]:  # First 20 lines
                        if line.strip():
                            self.progress.emit(line)
                self.progress.emit("=" * 50)
            else:
                result["viewer_html"] = str(viewer_dir / "viewer.html")
                self.progress.emit("✅ DICOM viewer generated!")
            
            result["status"] = "completed"
            
            self.progress.emit("✅ Analysis completed!")
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))



class CTPerfusionViewer(QMainWindow):
    """Main Window"""
    
    def __init__(self):
        super().__init__()
        self.current_result = None
        # self.tmax_data = None  # 2D/3D 렌더링 제거
        # self.core_mask = None  # 2D/3D 렌더링 제거
        # self.penumbra_mask = None  # 2D/3D 렌더링 제거
        
        # Preferences
        self.zoom_level = 1.0
        self.font_size = 13
        self.font_family = "SF Pro Display"
        
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("🧠 NeuroFlow - CT Perfusion Analysis Suite")
        self.setGeometry(100, 100, int(1100 * self.zoom_level), int(750 * self.zoom_level))
        
        # Remove default icon with transparent 1x1 pixel
        from PyQt5.QtGui import QIcon, QPixmap, QImage
        from PyQt5.QtCore import Qt
        
        # Create transparent 1x1 image
        transparent_img = QImage(1, 1, QImage.Format_ARGB32)
        transparent_img.fill(Qt.transparent)
        
        # Convert to pixmap and set as icon
        transparent_pixmap = QPixmap.fromImage(transparent_img)
        self.setWindowIcon(QIcon(transparent_pixmap))
        
        # 애플 스타일 폰트 설정
        from PyQt5.QtGui import QFont
        app_font = QFont(self.font_family, int(self.font_size * self.zoom_level))
        self.setFont(app_font)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 애플 스타일 스타일시트
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f7;
            }
            QWidget {
                background-color: #f5f5f7;
            }
            QGroupBox {
                font-weight: 600;
                font-size: 13px;
                color: #1d1d1f;
                border: none;
                margin-top: 10px;
                background-color: white;
                border-radius: 12px;
                padding: 20px;
            }
            QLabel {
                color: #1d1d1f;
                font-size: 13px;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QTableWidget {
                background-color: white;
                border: none;
                border-radius: 8px;
                gridline-color: #e5e5e7;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #e5e5e7;
                color: #1d1d1f;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #e8f4fd;
                color: #1d1d1f;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 10px;
                border: none;
                font-weight: 600;
                color: #1d1d1f;
            }
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #e5e5e7;
                text-align: center;
                color: #1d1d1f;
                font-weight: 600;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
                border-radius: 4px;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #e5e5e7;
                border-radius: 8px;
                padding: 10px;
                font-family: 'SF Mono', 'Consolas', monospace;
                font-size: 11px;
                color: #1d1d1f;
            }
            QScrollBar:vertical {
                border: none;
                background: #f5f5f7;
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c7c7cc;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #aeaeb2;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f5f5f7;
                height: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #c7c7cc;
                border-radius: 4px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #aeaeb2;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        
        # 상단 헤더
        header = QWidget()
        header.setStyleSheet("background-color: white; border-bottom: 1px solid #e5e5e7;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 15, 30, 15)
        
        # Patient ID label
        self.folder_label = QLabel("Patient ID: Please select a folder")
        self.folder_label.setStyleSheet("font-size: 14px; color: #86868b; font-weight: 500;")
        
        # 버튼들
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.select_btn = QPushButton("📁 Select Folder")
        self.select_btn.clicked.connect(self.select_folder)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
            }
            QPushButton:hover {
                background-color: #e5e5e7;
            }
        """)
        
        self.analyze_btn = QPushButton("🚀 Start Analysis")
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
            }
            QPushButton:hover {
                background-color: #0051D5;
            }
            QPushButton:disabled {
                background-color: #e5e5e7;
                color: #86868b;
            }
        """)
        
        self.viewer_btn = QPushButton("🌐 View Results")
        self.viewer_btn.clicked.connect(self.open_web_viewer)
        self.viewer_btn.setEnabled(False)
        self.viewer_btn.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
            }
            QPushButton:hover {
                background-color: #248A3D;
            }
            QPushButton:disabled {
                background-color: #e5e5e7;
                color: #86868b;
            }
        """)
        
        self.folder_btn = QPushButton("📂 Result Folder")
        self.folder_btn.clicked.connect(self.open_result_folder)
        self.folder_btn.setEnabled(False)
        self.folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9500;
                color: white;
            }
            QPushButton:hover {
                background-color: #C75F00;
            }
            QPushButton:disabled {
                background-color: #e5e5e7;
                color: #86868b;
            }
        """)
        
        self.pref_btn = QPushButton("⚙️")
        self.pref_btn.clicked.connect(self.show_preferences)
        self.pref_btn.setFixedWidth(40)
        self.pref_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
            }
            QPushButton:hover {
                background-color: #e5e5e7;
            }
        """)
        
        button_layout.addWidget(self.select_btn)
        button_layout.addWidget(self.analyze_btn)
        button_layout.addWidget(self.viewer_btn)
        button_layout.addWidget(self.folder_btn)
        button_layout.addWidget(self.pref_btn)
        
        header_layout.addWidget(self.folder_label, 1)
        header_layout.addLayout(button_layout)
        
        main_layout.addWidget(header)
        
        # 컨텐츠 영역
        content = QWidget()
        content.setStyleSheet("background-color: #f5f5f7;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 30)
        content_layout.setSpacing(20)
        
        # 진행 상태 카드
        progress_card = QWidget()
        progress_card.setStyleSheet("background-color: white; border-radius: 12px; padding: 15px;")
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setSpacing(10)
        
        self.status_label = QLabel("✓ Ready for Analysis")
        self.status_label.setStyleSheet("font-size: 14px; color: #34C759; font-weight: 600;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)  # 텍스트 숨김
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #e5e5e7;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 3px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #007AFF,
                    stop:0.5 #00C7FF,
                    stop:1 #007AFF
                );
            }
        """)
        
        # 진행률 퍼센트 라벨 (선택적)
        self.progress_percent_label = QLabel("")
        self.progress_percent_label.setStyleSheet("font-size: 11px; color: #86868b; font-weight: 500;")
        self.progress_percent_label.setAlignment(Qt.AlignRight)
        
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_percent_label)
        
        content_layout.addWidget(progress_card)
        
        # 분석 결과 테이블
        results_group = QGroupBox("📊 Analysis Results")
        results_layout = QVBoxLayout()
        results_layout.setContentsMargins(15, 25, 15, 15)
        
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(3)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value", "Clinical Significance"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.setAlternatingRowColors(True)
        self.metrics_table.verticalHeader().setVisible(False)
        self.metrics_table.setMinimumHeight(200)  # 최소 높이 설정
        
        results_layout.addWidget(self.metrics_table)
        results_group.setLayout(results_layout)
        
        content_layout.addWidget(results_group, 1)
        
        # TAC 그래프 섹션 (버튼만)
        penumbra_group = QGroupBox("📊 Time-Attenuation Curve (TAC)")
        penumbra_layout = QVBoxLayout()
        penumbra_layout.setContentsMargins(15, 25, 15, 15)
        
        # View Graph 버튼
        view_full_btn = QPushButton("📊 View Graph")
        view_full_btn.clicked.connect(lambda: self.open_tac_viewer(None))
        view_full_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0051D5;
            }
            QPushButton:pressed {
                background-color: #003D99;
            }
        """)
        view_full_btn.hide()
        self.view_full_btn = view_full_btn
        
        penumbra_layout.addWidget(view_full_btn, alignment=Qt.AlignCenter)
        penumbra_group.setLayout(penumbra_layout)
        penumbra_group.hide()  # 초기에는 숨김
        self.penumbra_group = penumbra_group  # 참조 저장
        
        content_layout.addWidget(penumbra_group)
        
        # 로그
        log_group = QGroupBox("📝 Log")
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(15, 25, 15, 15)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #e5e5e7;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', sans-serif;
            }
        """)
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        content_layout.addWidget(log_group)
        
        main_layout.addWidget(content, 1)
        
        self.log("CT Perfusion One-Stop Analyzer Started")
        self.log("Please select a folder and start analysis")
    
    # === 2D/3D 렌더링 탭 설정 메서드 제거 (웹 뷰어로 대체) ===
    # def setup_metrics_tab(self):
    # def setup_slice_tab(self):
    # def setup_render_tab(self):
    # def setup_log_tab(self):
    
    def select_folder(self):
        """Select folder"""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Patient DICOM Folder",
            r"C:\Users\Joon\Code\의료 저널\Research\CTP_MT"
        )
        
        if folder:
            self.selected_folder = Path(folder)
            self.folder_label.setText(f"Patient ID: {self.selected_folder.name}")
            self.analyze_btn.setEnabled(True)
            self.log(f"✅ Folder selected: {self.selected_folder}")
    
    def start_analysis(self):
        """Start analysis"""
        # 프로젝트 루트의 analysis_results 폴더 사용 (절대 경로)
        project_root = Path(__file__).parent
        output_dir = project_root / "analysis_results" / self.selected_folder.name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.log(f"🚀 Analysis started: {self.selected_folder.name}")
        self.progress_bar.setRange(0, 0)  # Infinite progress
        self.progress_percent_label.setText("Processing...")
        self.status_label.setText("🔄 Analyzing...")
        self.status_label.setStyleSheet("font-size: 14px; color: #007AFF; font-weight: 600;")
        self.analyze_btn.setEnabled(False)
        
        # 워커 스레드 시작
        self.worker = AnalysisWorker(self.selected_folder, output_dir)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_progress(self, message):
        """Update progress status"""
        self.status_label.setText(message)
        self.log(message)
    
    def on_finished(self, result):
        """Analysis completed"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_percent_label.setText("100%")
        self.status_label.setText("✅ Analysis completed!")
        self.status_label.setStyleSheet("font-size: 14px; color: #34C759; font-weight: 600;")
        self.analyze_btn.setEnabled(True)
        self.folder_btn.setEnabled(True)
        
        self.current_result = result
        self.log(f"✅ Analysis completed!")
        self.log(f"📁 Result location: {result['output_dir']}")
        
        # 결과 표시
        self.display_metrics(result.get("metrics", {}))
        
        # 웹 뷰어 경로 저장
        if "viewer_html" in result:
            self.viewer_btn.setEnabled(True)
            self.log(f"🌐 Web viewer: {result['viewer_html']}")
        else:
            self.log(f"⚠️ Failed to generate web viewer")
    
    def on_error(self, error_msg):
        """Error handling"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_percent_label.setText("Failed")
        self.status_label.setText(f"❌ Error")
        self.status_label.setStyleSheet("font-size: 14px; color: #FF3B30; font-weight: 600;")
        self.analyze_btn.setEnabled(True)
        self.log(f"❌ Error: {error_msg}")
    
    def display_metrics(self, metrics):
        """Display metrics (including advanced metrics based on papers)"""
        if not metrics:
            return
        
        # 기본 지표
        hypoperfusion_ml = metrics.get('hypoperfusion_volume_ml', 0)
        core_ml = metrics.get('infarct_core_volume_ml', 0)
        penumbra_ml = metrics.get('penumbra_volume_ml', 0)
        mismatch_ratio = metrics.get('mismatch_ratio', 0)
        
        # 논문 기반 고급 지표
        hir = metrics.get('hir', None)
        pvt = metrics.get('pvt_ml', None)
        prr = metrics.get('prr', None)
        corrected_cbv_index = metrics.get('corrected_cbv_index', None)
        conventional_cbv_index = metrics.get('conventional_cbv_index', None)
        collateral_grade = metrics.get('collateral_grade', None)
        
        metrics_info = [
            ("Hypoperfusion Volume", f"{hypoperfusion_ml:.1f} ml", 
             "Tmax ≥ 6s region"),
            ("Infarct Core Volume", f"{core_ml:.1f} ml", 
             "Already damaged tissue (Tmax ≥ 10s & CBV < 2.0)"),
            ("Penumbra Volume", f"{penumbra_ml:.1f} ml", 
             "Salvageable tissue"),
            ("Mismatch Ratio", f"{mismatch_ratio:.2f}", 
             "✅ Suitable for thrombectomy" if mismatch_ratio > 1.8 else "⚠️ Not suitable"),
        ]
        
        # 고급 지표 추가
        if corrected_cbv_index is not None:
            metrics_info.append(
                ("Corrected CBV Index", f"{corrected_cbv_index:.3f}",
                 f"Collateral: {collateral_grade}" if collateral_grade else "Collateral assessment")
            )
        
        if conventional_cbv_index is not None:
            metrics_info.append(
                ("Conventional CBV Index", f"{conventional_cbv_index:.3f}",
                 "Conventional CBV metric")
            )
        
        if hir is not None:
            metrics_info.append(
                ("HIR", f"{hir:.3f}",
                 "Hypoperfusion Intensity Ratio (Tmax >10s / Tmax >6s)")
            )
        
        if prr is not None:
            prr_percent = prr * 100
            metrics_info.append(
                ("PRR", f"{prr_percent:.1f}%",
                 "✅ Mostly salvageable" if prr_percent > 80 else "⚠️ Limited salvageable area")
            )
        
        # pvt_ml은 hypoperfusion_volume_ml과 중복이므로 제거
        # PVT 데이터도 TAC로 대체되었으므로 표시하지 않음
        
        self.metrics_table.setRowCount(len(metrics_info))
        
        # Apple 감성 색상 팔레트
        from PyQt5.QtGui import QColor, QBrush
        
        for i, (name, value, meaning) in enumerate(metrics_info):
            name_item = QTableWidgetItem(name)
            value_item = QTableWidgetItem(value)
            meaning_item = QTableWidgetItem(meaning)
            
            # 행별 배경색 적용 (Apple 스타일)
            if i == 0:  # Hypoperfusion - 연한 민트
                bg_color = QColor("#e8f5e9")
                text_color = QColor("#2e7d32")
            elif i == 1:  # Infarct Core - 연한 빨강
                bg_color = QColor("#ffebee")
                text_color = QColor("#c62828")
            elif i == 2:  # Penumbra - 연한 노랑
                bg_color = QColor("#fff9e6")
                text_color = QColor("#f57c00")
            elif i == 3:  # Mismatch Ratio - 연한 파랑
                bg_color = QColor("#e3f2fd")
                text_color = QColor("#1565c0")
            elif name == "PVT Status":  # PVT 상태 - 조건부 색상
                if "PVT+" in value:
                    bg_color = QColor("#ffebee")  # 연한 빨강 (위험)
                    text_color = QColor("#c62828")
                else:
                    bg_color = QColor("#e8f5e9")  # 연한 초록 (정상)
                    text_color = QColor("#2e7d32")
            else:  # 기타 지표 - 연한 회색
                bg_color = QColor("#f5f5f7")
                text_color = QColor("#1d1d1f")
            
            # 배경색 적용
            name_item.setBackground(QBrush(bg_color))
            value_item.setBackground(QBrush(bg_color))
            meaning_item.setBackground(QBrush(bg_color))
            
            # 텍스트 색상 적용
            name_item.setForeground(QBrush(text_color))
            value_item.setForeground(QBrush(text_color))
            meaning_item.setForeground(QBrush(text_color))
            
            # 폰트 굵기 (중요 지표는 볼드)
            if i < 4:
                from PyQt5.QtGui import QFont
                font = QFont()
                font.setBold(True)
                name_item.setFont(font)
                value_item.setFont(font)
            
            self.metrics_table.setItem(i, 0, name_item)
            self.metrics_table.setItem(i, 1, value_item)
            self.metrics_table.setItem(i, 2, meaning_item)
        
        self.metrics_table.resizeColumnsToContents()
        
        # TAC 그래프 표시
        self.display_tac_graph()
    
    def display_tac_graph(self):
        """TAC 그래프 버튼 표시"""
        if not self.current_result or "tac" not in self.current_result:
            self.view_full_btn.hide()
            self.penumbra_group.hide()
            return
        
        # 원본 Penumbra 이미지 경로 (동적 검색)
        output_dir = Path(self.current_result.get("output_dir", ""))
        tac_extracted_dir = output_dir / "tac_extracted"
        
        if not tac_extracted_dir.exists():
            self.view_full_btn.hide()
            self.penumbra_group.hide()
            return
        
        # 원본 Penumbra 이미지 찾기
        penumbra_files = list(tac_extracted_dir.glob("penumbra_original_*.png"))
        if not penumbra_files:
            self.view_full_btn.hide()
            self.penumbra_group.hide()
            return
        
        self.current_penumbra_path = penumbra_files[0]  # 확대용으로 저장
        
        # 버튼만 표시
        self.view_full_btn.show()
        self.penumbra_group.show()
    
    def open_tac_viewer(self, event):
        """Penumbra 이미지 확대 뷰어 열기"""
        if not hasattr(self, 'current_penumbra_path'):
            return
        
        # 새 창 생성
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea
        from PyQt5.QtGui import QPixmap
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Penumbra Image - Original")
        dialog.setMinimumSize(1200, 800)
        
        layout = QVBoxLayout(dialog)
        
        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # 이미지 라벨
        image_label = QLabel()
        pixmap = QPixmap(str(self.current_penumbra_path))
        image_label.setPixmap(pixmap)  # 원본 크기로 표시
        image_label.setAlignment(Qt.AlignCenter)
        
        scroll.setWidget(image_label)
        layout.addWidget(scroll)
        
        dialog.exec_()
    
    # === 2D/3D 렌더링 메서드 제거 (웹 뷰어로 대체) ===
    # def load_nifti_data(self, result):
    # def update_slice_view(self):
    # def render_3d(self):
    
    def open_web_viewer(self):
        """Open web viewer"""
        if self.current_result and "viewer_html" in self.current_result:
            import webbrowser
            viewer_path = Path(self.current_result["viewer_html"])
            if viewer_path.exists():
                webbrowser.open(f'file://{viewer_path.absolute()}')
                self.log(f"🌐 Web viewer opened: {viewer_path}")
            else:
                self.log(f"❌ Web viewer file not found: {viewer_path}")
        else:
            self.log("❌ Web viewer not generated")
    
    def open_result_folder(self):
        """Open result folder"""
        if self.current_result and "output_dir" in self.current_result:
            import subprocess
            output_dir = Path(self.current_result["output_dir"])
            if output_dir.exists():
                # Windows 탐색기로 폴더 열기
                subprocess.run(['explorer', str(output_dir.absolute())])
                self.log(f"📂 Result folder opened: {output_dir}")
            else:
                self.log(f"❌ Result folder not found: {output_dir}")
        else:
            self.log("❌ Please run analysis first")
    
    def log(self, message):
        """Add log message"""
        self.log_text.append(message)
    
    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel (Ctrl + Wheel)"""
        from PyQt5.QtCore import Qt
        
        if event.modifiers() == Qt.ControlModifier:
            # Ctrl + 휠: 줌
            delta = event.angleDelta().y()
            
            if delta > 0:
                # 줌 인
                self.zoom_level = min(2.0, self.zoom_level + 0.1)
            else:
                # 줌 아웃
                self.zoom_level = max(0.5, self.zoom_level - 0.1)
            
            self.apply_zoom()
            event.accept()
        else:
            super().wheelEvent(event)
    
    def apply_zoom(self):
        """줌 레벨 적용"""
        from PyQt5.QtGui import QFont
        
        # 폰트 크기 조정
        app_font = QFont(self.font_family, int(self.font_size * self.zoom_level))
        self.setFont(app_font)
        
        # 창 크기 조정
        self.resize(int(1100 * self.zoom_level), int(750 * self.zoom_level))
        
        self.log(f"🔍 Zoom: {int(self.zoom_level * 100)}%")
    
    def show_preferences(self):
        """Show preferences dialog"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Preferences")
        dialog.setFixedSize(400, 250)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f5f7;
            }
            QLabel {
                font-size: 13px;
                color: #1d1d1f;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0051D5;
            }
            QSpinBox, QComboBox {
                padding: 6px;
                border: 1px solid #e5e5e7;
                border-radius: 6px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Font size
        font_layout = QHBoxLayout()
        font_label = QLabel("Font Size:")
        font_spin = QSpinBox()
        font_spin.setRange(10, 20)
        font_spin.setValue(self.font_size)
        font_spin.setSuffix(" pt")
        font_layout.addWidget(font_label)
        font_layout.addWidget(font_spin)
        layout.addLayout(font_layout)
        
        # Font family
        family_layout = QHBoxLayout()
        family_label = QLabel("Font:")
        family_combo = QComboBox()
        family_combo.addItems(["SF Pro Display", "Segoe UI", "Arial", "Helvetica", "Malgun Gothic"])
        family_combo.setCurrentText(self.font_family)
        family_layout.addWidget(family_label)
        family_layout.addWidget(family_combo)
        layout.addLayout(family_layout)
        
        # Zoom level
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("Screen Zoom:")
        zoom_spin = QSpinBox()
        zoom_spin.setRange(50, 200)
        zoom_spin.setValue(int(self.zoom_level * 100))
        zoom_spin.setSuffix(" %")
        zoom_spin.setSingleStep(10)
        zoom_layout.addWidget(zoom_label)
        zoom_layout.addWidget(zoom_spin)
        layout.addLayout(zoom_layout)
        
        # Info message
        info_label = QLabel("💡 You can also zoom with Ctrl + Mouse Wheel")
        info_label.setStyleSheet("color: #86868b; font-size: 11px;")
        layout.addWidget(info_label)
        
        # 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #e5e5e7; color: #1d1d1f;")
        cancel_btn.clicked.connect(dialog.reject)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(lambda: self.apply_preferences(
            font_spin.value(),
            family_combo.currentText(),
            zoom_spin.value() / 100.0,
            dialog
        ))
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(apply_btn)
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def apply_preferences(self, font_size, font_family, zoom_level, dialog):
        """Apply preferences"""
        self.font_size = font_size
        self.font_family = font_family
        self.zoom_level = zoom_level
        
        self.apply_zoom()
        dialog.accept()
        self.log(f"⚙️ Preferences applied: {font_family} {font_size}pt, Zoom {int(zoom_level * 100)}%")


def main():
    # Prevent multiple instances
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # QApplication 인스턴스 확인
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    else:
        # 이미 실행 중인 인스턴스가 있으면 종료
        return
    
    app.setStyle('Fusion')
    
    viewer = CTPerfusionViewer()
    viewer.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    # PyInstaller multiprocessing support
    import multiprocessing
    multiprocessing.freeze_support()
    
    main()
