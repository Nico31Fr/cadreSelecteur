# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['__main__.py'],
    pathex=['.'],  # Chemin relatif vers le script principal
    binaries=[],
    datas=[
        ('resources/*', 'resources'),
        ('Cadres/*', 'Cadres'),
        ('Templates/*', 'Templates'),
    ],
    hiddenimports=collect_submodules('CadreEditeur.text') +
                  ['PIL', 'PIL._imaging'], # Pour Pillow ; généralement inutile, mais sûr
    # matplotlib est généralement bien détecté mais tu peux ajouter `matplotlib` :
    # hiddenimports=['matplotlib'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

exe = EXE(
    a.pure,
    a.zipped_data,
    a.scripts,
    [],
    name='CadreSelecteur',   # Nom du .exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # Pas de fenêtre console (GUI tkinter)
    # icon='app.ico',        # Décommente si un jour tu ajoutes une icône
)