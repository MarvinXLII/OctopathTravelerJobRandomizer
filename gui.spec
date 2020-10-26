# -*- mode: python -*-

block_cipher = None

a = Analysis(
    [
        'gui.py',
        'src/Utilities.py',
        'src/ROM.py',
        'src/JobData.py',
    ],
    pathex=[],
    binaries=[],
    datas=[
        ('./data/parameters.json', 'data'),
        ('data/support.json', 'data'),
        ('data/skills.json', 'data'),
        ('data/Octopath_Traveler', 'Octopath_Traveler'),
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
