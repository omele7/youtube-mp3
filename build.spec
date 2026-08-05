# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

datas = [
    ("resources/ffmpeg/ffmpeg.exe", "resources/ffmpeg"),
]
if os.path.exists("resources/icon.ico"):
    datas.append(("resources/icon.ico", "resources"))

a = Analysis(
    ["src/main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="VideoToMP3",
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
    icon="resources/icon.ico" if os.path.exists("resources/icon.ico") else None,
)
