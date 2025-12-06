# -*- mode: python ; coding: utf-8 -*-
import os
import sys

sys.path.append(os.getcwd())
from lolaudit import __version__

name = f"LolAudit_{__version__}"
icon = "./assets/lol_audit.ico"

a = Analysis(  # type: ignore
    ["./main.py"],
    pathex=[],
    binaries=[],
    datas=[(icon, ".")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)  # type: ignore

exe = EXE(  # type: ignore
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=name,
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
    icon=icon,
)
