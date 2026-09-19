# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.building.splash import Splash
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

# Splash natif affiché par le bootloader pendant l'extraction et l'import
# (uniquement en .exe ; fermé dans __main__.py via pyi_splash.close())
# L'image fait 128x168 : logo sur 128px + bande transparente de 40px en bas,
# dans laquelle le texte de progression est affiché sous le logo.
splash = Splash(
    os.path.join("CadreSelecteur", "resources", "cadreSelecteur_splash.png"),
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(8, 160),
    text_size=10,
    minify_script=True,
)

exe = EXE(
    pyz,
    a.scripts,
    splash,
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
