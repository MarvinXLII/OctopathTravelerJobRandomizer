# -*- mode: python -*-

block_cipher = None

a = Analysis(
    [
        'gui.py',
        'src/Abilities.py',
        'src/Classes.py',
        'src/Data.py',
        'src/Jobs.py',
        'src/ROM.py',
        'src/Treasures.py',
        'src/Utilities.py',
        'src/World.py',
    ],
    pathex=[],
    binaries=[],
    datas=[
        ('json/*.json', 'json'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OTR-JOBS.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False
)
