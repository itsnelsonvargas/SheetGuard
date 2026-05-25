# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — run: pyinstaller sheetguard.spec"""

from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    ["main.py"],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "resources"), "resources"),
    ],
    hiddenimports=[
        "sheetguard",
        "sheetguard.core",
        "sheetguard.gui",
        "sheetguard.models",
        "sheetguard.services",
        "sheetguard.utils",
        "openpyxl",
        "rapidfuzz",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SheetGuard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
