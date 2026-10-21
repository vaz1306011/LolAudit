# -*- mode: python ; coding: utf-8 -*-
import os
import subprocess
import sys

sys.path.append(os.getcwd())

try:
    describe = subprocess.check_output(["git", "describe", "--tags", "--always", "--dirty"], text=True).strip()
    with open("lolaudit/_build.py", "w", encoding="utf-8") as f:
        f.write(f'__version__ = "{describe}"\n')
except Exception as e:
    print(f"Warning: could not get git describe: {e}")

name = "LolAudit"
icon = "./assets/lol_audit.icns"

a = Analysis(  # type: ignore
    ["./main.py"],
    pathex=[],
    binaries=[],
    datas=[(icon, "./assets/")],
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

app = BUNDLE(  # type: ignore
    exe,
    name=name + ".app",
    icon=icon,
    bundle_identifier=None,
)

exe_path = os.path.join("dist", name)
if os.path.exists(exe_path) and not exe_path.endswith(".app"):
    try:
        os.remove(exe_path)
        print(f"Removed extra executable: {exe_path}")
    except Exception as e:
        print(f"Warning: could not remove {exe_path}: {e}")
