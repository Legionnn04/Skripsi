# -*- mode: python ; coding: utf-8 -*-

# include necessary Kivy runtime dependencies for SDL2/Glew
from kivy_deps import sdl2, glew

# convert dependency directories into (src, dest) pairs for PyInstaller
kivy_binaries = []
for _dir in sdl2.dep_bins + glew.dep_bins:
    kivy_binaries.append((_dir, '.'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=kivy_binaries,
    datas=[
        ('screens', 'screens'),
        ('utils', 'utils'),
        ('widgets', 'widgets'),
        ('logokampus.png', '.'),
        ('normal.png', '.'),
        ('azan1.mp3', '.'),
        ('alarmku.jpg', '.'),
        ('berpikir.gif', '.'),
        ('kagum.gif', '.'),
        ('marah.gif', '.'),
        ('mengantuk.gif', '.'),
        ('mengingatkan.gif', '.'),
        ('menyapa.gif', '.'),
        ('alarm_data.json', '.'),
        ('jadwal_data.json', '.'),
        ('alarm_audio', 'alarm_audio'),
    ],
    hiddenimports=[
        'kivy',
        'kivy.core.window',
        'kivy.core.audio',
        'kivy.uix.screenmanager',
        'kivy.deps.sdl2',
        'kivy.deps.glew',
        'win32timezone',
    ],
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
    a.binaries,
    a.datas,
    [],
    name='AsistenJadwalFinals',
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
