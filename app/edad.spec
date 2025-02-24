# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['edad.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('edad-icon.png', '.'),  # Include the PNG file
        ('edad-banner.gif', '.')  # Include the GIF file
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'mysql.connector',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'numpy.core._methods',
        'numpy.lib.format',
        'mysql.connector.locales',
        'mysql.connector.plugins'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EDAD',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='edad-icon.png'
)