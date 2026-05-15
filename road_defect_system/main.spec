# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# 收集 folium 数据
from PyInstaller.utils.hooks import collect_data_files, collect_all

datas = []
hiddenimports = []

# Folium 数据
try:
    folium_data = collect_data_files('folium')
    datas.extend(folium_data)
except:
    pass

# branca 数据
try:
    branca_all = collect_all('branca')
    datas.extend(branca_all[0])
    hiddenimports.extend(branca_all[1])
except:
    pass

# jinja2 数据
try:
    jinja_all = collect_all('jinja2')
    datas.extend(jinja_all[0])
except:
    pass

# 添加模型文件夹
if os.path.exists('models'):
    datas.append(('models', 'models'))

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'test'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=True,
    name='RoadDefectSystem',
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
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RoadDefectSystem',
)