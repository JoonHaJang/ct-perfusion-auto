"""
NeuroFlow - macOS Application Setup (py2app)
Usage: python3 setup_py2app.py py2app
"""

from setuptools import setup

APP = ['ct_perfusion_viewer.py']
import os
import sys
from pathlib import Path

# PyQt5 플러그인 경로 찾기
pyqt5_path = None
for path in sys.path:
    qt_plugins = Path(path) / 'PyQt5' / 'Qt5' / 'plugins'
    if qt_plugins.exists():
        pyqt5_path = qt_plugins
        break

DATA_FILES = [
    ('scripts', [
        'scripts/extract_metrics_from_dicom.py',
        'scripts/generate_dicom_viewer.py',
        'scripts/compute_metrics.py',
        'scripts/convert_dicom_to_nifti.py',
        'scripts/extract_real_data.py',
        'scripts/generate_enhanced_viewer.py',
        'scripts/generate_web_viewer_data.py',
        'scripts/inspect_dicom.py',
        'scripts/interactive_3d_viewer.py',
        'scripts/quick_validate.py',
        'scripts/validate_visualization.py',
        'scripts/verify_accuracy.py',
    ]),
]

# Qt 플랫폼 플러그인 추가
if pyqt5_path:
    platforms_dir = pyqt5_path / 'platforms'
    if platforms_dir.exists():
        DATA_FILES.append(('platforms', [str(f) for f in platforms_dir.glob('*.dylib')]))
    styles_dir = pyqt5_path / 'styles'
    if styles_dir.exists():
        DATA_FILES.append(('styles', [str(f) for f in styles_dir.glob('*.dylib')]))

OPTIONS = {
    'argv_emulation': False,
    'packages': [
        'PyQt5',
        'pydicom',
        'numpy',
        'PIL',
        'scipy',
        'scipy.ndimage',
        'nibabel',
    ],
    'includes': [
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'pydicom.charset',
        'numpy.core._multiarray_umath',
        'PIL._imaging',
    ],
    'excludes': [
        'matplotlib',
        'pandas',
        'IPython',
        'jupyter',
        'tkinter',
        'PyInstaller',
        'test',
        'tests',
        'unittest',
    ],
    'iconfile': None,  # 아이콘 파일 경로 (선택사항)
    'plist': {
        'CFBundleName': 'NeuroFlow',
        'CFBundleDisplayName': 'NeuroFlow - CT Perfusion Analyzer',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleIdentifier': 'com.neuroflow.ctperfusion',
        'NSHumanReadableCopyright': 'Copyright © 2025 NeuroFlow. All rights reserved.',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15.0',
        'LSEnvironment': {
            'QT_PLUGIN_PATH': '@executable_path/../Resources/platforms',
        },
    },
    'qt_plugins': ['platforms', 'styles'],  # Qt 플러그인 명시적 포함
}

setup(
    name='NeuroFlow',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
