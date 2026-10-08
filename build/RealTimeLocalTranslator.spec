# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPEC).resolve().parent.parent

datas = []
binaries = []
hiddenimports = []

# Developer/test builds stay small and reuse models stored outside the executable.
# Set RTL_BUNDLE_MODELS=1 for a self-contained installer build.
if __import__("os").environ.get("RTL_BUNDLE_MODELS") == "1":
    datas.append((str(ROOT / "models"), "models"))

for package_name in ("sherpa_onnx", "faster_whisper", "ctranslate2", "argostranslate", "soundcard", "numpy", "PySide6"):
    d, b, h = collect_all(package_name)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
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
    exclude_binaries=True,
    name="RealTimeLocalTranslator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="RealTimeLocalTranslator",
)
