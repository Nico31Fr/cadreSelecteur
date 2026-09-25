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

# ---------------------------------------------------------------------------
# Splash screen
# ---------------------------------------------------------------------------
# L'image est pré-générée une fois pour toutes par generate_splash.py et
# committée dans CadreSelecteur/resources/. Si tu changes le logo source,
# relance ce script puis reconstruis — pas besoin de Pillow ici, ni de
# logique de génération à chaque build.
#
# Dimensions fixées par generate_splash.py : 420x300, zone de texte réservée
# sur les 46 derniers pixels en bas (cohérent avec SPLASH_TEXT_POS ci-dessous).

SPLASH_IMG = os.path.join("CadreSelecteur", "resources", "cadreSelecteur_splash_pro.png")

if not os.path.isfile(SPLASH_IMG):
    raise FileNotFoundError(
        f"{SPLASH_IMG} est introuvable. Lance d'abord : python generate_splash.py"
    )

splash = Splash(
    SPLASH_IMG,
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(24, 270),       # sous le titre, dans la zone réservée (voir generate_splash.py)
    text_size=11,
    text_color="#a8a9ad",
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
