# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Répertoire racine du projet (le dossier qui contient CadreSelecteur/)
project_path = os.path.abspath(".")

datas = [
    ('CadreSelecteur/resources/*', 'resources'),
]

hiddenimports = (
    collect_submodules("numpy")
    + collect_submodules("PIL")
    + [
        "PIL",
        "PIL._imaging",
        "PIL.ImageTk",
        "tkinter",
        "matplotlib",
    ]
)

a = Analysis(
    ['CadreSelecteur/__main__.py'],
    pathex=[project_path],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CadreSelecteur',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon=os.path.join("CadreSelecteur", "resources", "cadreSelecteur.ico"),
)
