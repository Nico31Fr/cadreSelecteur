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
# Splash screen : généré au build avec Pillow
# ---------------------------------------------------------------------------
# On ne se contente plus d'aplatir le PNG sur fond blanc : on compose une
# vraie image opaque (dégradé sombre, halo derrière le logo, titre, filet
# d'accent). Opaque = compatible Windows et Linux (pas de transparence
# nécessaire, PyInstaller ne la gère pas sur Linux).
#
# Le texte de progression (pyi_splash.update_text) est dessiné par Tk
# par-dessus l'image, en bas à gauche, dans la zone réservée.

SPLASH_SRC = os.path.join("CadreSelecteur", "resources", "cadreSelecteur_splash.png")
SPLASH_OUT = os.path.join(project_path, "build", "cadreSelecteur_splash_pro.png")

APP_TITLE = "CadreSelecteur"

# Palette (modifiable ici)
COLOR_BG_TOP = (15, 23, 42)       # #0f172a
COLOR_BG_BOTTOM = (30, 41, 59)    # #1e293b
COLOR_ACCENT = (59, 130, 246)     # #3b82f6
COLOR_BORDER = (51, 65, 85)       # #334155
COLOR_TITLE = (241, 245, 249)     # #f1f5f9
TEXT_COLOR_TK = "#94a3b8"         # texte de progression (Tk)

SPLASH_W, SPLASH_H = 420, 260
LOGO_SIZE = 128
FOOTER_H = 44                      # zone basse réservée au texte de progression


def _find_font(size, bold=False):
    """Cherche une police TrueType courante sur Windows / Linux / macOS."""
    from PIL import ImageFont
    candidates = [
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def build_splash():
    from PIL import Image, ImageDraw, ImageFilter

    W, H = SPLASH_W, SPLASH_H

    # 1) Fond en dégradé vertical
    img = Image.new("RGB", (W, H), COLOR_BG_TOP)
    px = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        color = tuple(
            int(COLOR_BG_TOP[i] + (COLOR_BG_BOTTOM[i] - COLOR_BG_TOP[i]) * t)
            for i in range(3)
        )
        px.line([(0, y), (W, y)], fill=color)

    # 2) Logo : on ne garde que la partie haute (128x128) du PNG source,
    #    la bande basse de l'ancien splash n'est plus utile.
    logo = Image.open(SPLASH_SRC).convert("RGBA")
    logo = logo.crop((0, 0, min(LOGO_SIZE, logo.width), min(LOGO_SIZE, logo.height)))
    logo_x = (W - logo.width) // 2
    logo_y = 28

    # 3) Halo bleu doux derrière le logo
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    cx, cy = W // 2, logo_y + logo.height // 2
    r = 78
    gdraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=COLOR_ACCENT + (70,))
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    img = Image.alpha_composite(img.convert("RGBA"), glow)

    # 4) Logo par-dessus (le canal alpha du PNG sert de masque)
    img.alpha_composite(logo, (logo_x, logo_y))

    draw = ImageDraw.Draw(img)

    # 5) Titre centré sous le logo
    title_font = _find_font(24, bold=True)
    tw = draw.textlength(APP_TITLE, font=title_font)
    title_y = logo_y + logo.height + 14
    draw.text(((W - tw) / 2, title_y), APP_TITLE, font=title_font, fill=COLOR_TITLE)

    # 6) Petit filet d'accent sous le titre
    line_y = title_y + 40
    draw.rounded_rectangle(
        [W // 2 - 28, line_y, W // 2 + 28, line_y + 3],
        radius=1, fill=COLOR_ACCENT,
    )

    # 7) Séparateur fin au-dessus de la zone de progression
    sep_y = H - FOOTER_H
    draw.line([(20, sep_y), (W - 20, sep_y)], fill=COLOR_BORDER, width=1)

    # 8) Bande d'accent tout en bas + bordure extérieure discrète
    draw.rectangle([0, H - 3, W, H], fill=COLOR_ACCENT)
    draw.rectangle([0, 0, W - 1, H - 1], outline=COLOR_BORDER, width=1)

    os.makedirs(os.path.dirname(SPLASH_OUT), exist_ok=True)
    img.convert("RGB").save(SPLASH_OUT, "PNG")
    return SPLASH_OUT


try:
    SPLASH_IMG = build_splash()
    SPLASH_TEXT_COLOR = TEXT_COLOR_TK
    SPLASH_TEXT_POS = (20, SPLASH_H - 14)   # coin bas-gauche du texte
except Exception as exc:
    # Repli : ancien PNG (fond clair) => texte foncé pour rester lisible
    print(f"[spec] Splash pro non généré ({exc}), repli sur le PNG source.")
    SPLASH_IMG = SPLASH_SRC
    SPLASH_TEXT_COLOR = "black"
    SPLASH_TEXT_POS = (8, 160)

splash = Splash(
    SPLASH_IMG,
    binaries=a.binaries,
    datas=a.datas,
    text_pos=SPLASH_TEXT_POS,
    text_size=11,
    text_color=SPLASH_TEXT_COLOR,
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
