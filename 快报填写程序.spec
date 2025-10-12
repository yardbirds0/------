# -*- mode: python ; coding: utf-8 -*-
"""
快报填写程序 PyInstaller 打包配置文件
使用方法: pyinstaller 快报填写程序.spec
"""

import sys
import os
from pathlib import Path

# 程序基本信息
APP_NAME = '快报填写程序'
MAIN_SCRIPT = 'main.py'

# 图标文件（计算绝对路径）
ICON_FILE = None
icon_path = Path('icon.ico')
if icon_path.exists():
    ICON_FILE = str(icon_path.resolve())
    print(f"[INFO] 使用图标文件: {ICON_FILE}")
else:
    print("[WARNING] 未找到icon.ico，将使用默认图标")

block_cipher = None

# 分析依赖
a = Analysis(
    [MAIN_SCRIPT],
    pathex=[],
    binaries=[],
    datas=[
        # 添加配置文件夹
        ('config', 'config'),
        # 添加公式模板文件夹
        ('Fomular', 'Fomular'),
        # 添加数据文件夹
        ('data', 'data'),
    ],
    hiddenimports=[
        # Excel处理
        'openpyxl',
        'openpyxl.cell._writer',
        'openpyxl.styles',
        'openpyxl.utils',
        'openpyxl.workbook',
        'openpyxl.worksheet',
        # PySide6
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        # 其他
        'sqlite3',
        'json',
        'pathlib',
        'datetime',
        're',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的库
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'IPython',
        'notebook',
        'PyQt5',
        'PyQt6',  # 排除PyQt6避免冲突
        'wx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 处理依赖文件
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# 打包成可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
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
    icon=ICON_FILE,  # 使用计算好的绝对路径（字符串，不是列表）
)
