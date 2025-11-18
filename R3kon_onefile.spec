# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# Get current directory
current_dir = os.path.abspath('.')

# Find llama_cpp library files
llama_cpp_libs = []
try:
    import llama_cpp
    llama_cpp_path = Path(llama_cpp.__file__).parent
    lib_path = llama_cpp_path / 'lib'
    
    if lib_path.exists():
        # Include all DLL files from lib directory
        for dll_file in lib_path.glob('*.dll'):
            llama_cpp_libs.append((str(dll_file), 'llama_cpp/lib'))
        for so_file in lib_path.glob('*.so*'):
            llama_cpp_libs.append((str(so_file), 'llama_cpp/lib'))
        for dylib_file in lib_path.glob('*.dylib'):
            llama_cpp_libs.append((str(dylib_file), 'llama_cpp/lib'))
    
    # Also check for DLLs in the main llama_cpp directory
    for dll_file in llama_cpp_path.glob('*.dll'):
        llama_cpp_libs.append((str(dll_file), 'llama_cpp'))
    for so_file in llama_cpp_path.glob('*.so*'):
        llama_cpp_libs.append((str(so_file), 'llama_cpp'))
    for pyd_file in llama_cpp_path.glob('*.pyd'):
        llama_cpp_libs.append((str(pyd_file), 'llama_cpp'))
        
except Exception as e:
    print(f"Warning: Could not locate llama_cpp libraries: {e}")

print(f"Found {len(llama_cpp_libs)} llama_cpp library files")

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=llama_cpp_libs,
    datas=[
        ('model', 'model'),  # Include the model folder
        ('icon.ico', '.'),   # Include icon in root
    ],
    hiddenimports=[
        'llama_cpp',
        'llama_cpp.llama_cpp',
        'llama_cpp.llama',
        'llama_cpp.llama_tokenizer',
        'tkinter',
        'tkinter.scrolledtext',
        'tkinter.ttk',
        'tkinter.messagebox',
        'threading',
        'json',
        'os',
        're',
        'datetime',
        'sys',
        'ctypes',
        'ctypes.util',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'numpy.random',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# SINGLE FILE BUILD - Everything bundled into one EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # Include binaries in EXE
    a.zipfiles,      # Include zipfiles in EXE
    a.datas,         # Include data files in EXE
    [],
    name='R3KON_GPT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,        # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)