# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['__main__.py'],
    pathex=['.'],  # chemin vers ton script principal
    binaries=[],
    datas=[
        ('resources/*', 'resources'),
        ('Fonts/*', 'Fonts'),
    ],
    hiddenimports=collect_submodules('numpy') + [
        'PIL',
        'PIL._imaging',
        'matplotlib',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CadreSelecteur',   # nom du .exe final
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # pas de console (GUI tkinter)
    # icon='app.ico',        # décommente si tu ajoutes une icône
)
