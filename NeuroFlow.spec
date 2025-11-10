# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ct_perfusion_viewer_windows.py'],
    pathex=[],
    binaries=[],
    datas=[('scripts', 'scripts'), ('pvt_masks', 'pvt_masks')],
    hiddenimports=['PyQt5', 'pydicom', 'nibabel', 'scipy.ndimage'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NeuroFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NeuroFlow',
)
