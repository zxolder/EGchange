# -*- mode: python ; coding: utf-8 -*-
# Build with: pyinstaller build.spec
# Output: dist/ScreenTranslator.exe

hiddenimports = [
    "winsdk.windows.media.ocr",
    "winsdk.windows.globalization",
    "winsdk.windows.graphics.imaging",
    "winsdk.windows.storage.streams",
    "winsdk.windows.foundation",
    "winsdk.windows.foundation.collections",
    "keyboard._winkeyboard",
    "keyboard._winmouse",
    "mss.windows",
]

a = Analysis(
    ["screen_translator/main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ScreenTranslator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon=None,
)
