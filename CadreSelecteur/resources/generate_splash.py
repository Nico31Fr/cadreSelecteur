"""
Génère le splash screen statique de CadreSelecteur.

À lancer UNE SEULE FOIS (ou à chaque changement du logo source), depuis la
racine du projet :

    python generate_splash.py

Produit : CadreSelecteur/resources/cadreSelecteur_splash_pro.png
Ce fichier est ensuite utilisé tel quel par CadreSelecteur.spec — plus
besoin de Pillow ni de logique de génération au moment du build PyInstaller.
"""

import os

from PIL import Image, ImageDraw, ImageFont

SPLASH_SRC = os.path.join("cadreSelecteur.png")
SPLASH_OUT = os.path.join("cadreSelecteur_splash_pro.png")

APP_TITLE = "Cadre Selecteur"

# Palette — gris/anthracite, pas de couleur vive
COLOR_BG_TOP = (80, 84, 102)        # #181a1e
COLOR_BG_BOTTOM = (12, 13, 16)     # #0c0d10
COLOR_BORDER = (110, 112, 118)     # gris simple pour le cadre et le séparateur
COLOR_TITLE = (235, 236, 238)      # texte du titre, quasi blanc

SPLASH_W, SPLASH_H = 420, 300
LOGO_MAX = 140                      # taille MAX du logo ; jamais agrandi si plus petit
LOGO_TOP = 30
TITLE_GAP = 18
FOOTER_H = 60                      # doit rester cohérent avec SPLASH_TEXT_POS dans le .spec


def _find_font(size, bold=False):
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


def main():
    W, H = SPLASH_W, SPLASH_H

    # Fond en dégradé vertical
    img = Image.new("RGB", (W, H), COLOR_BG_TOP)
    px = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        color = tuple(
            int(COLOR_BG_TOP[i] + (COLOR_BG_BOTTOM[i] - COLOR_BG_TOP[i]) * t)
            for i in range(3)
        )
        px.line([(0, y), (W, y)], fill=color)
    img = img.convert("RGBA")

    # Logo redimensionné (jamais rogné, jamais agrandi), proportions conservées
    logo = Image.open(SPLASH_SRC).convert("RGBA")
    logo.thumbnail((LOGO_MAX, LOGO_MAX), Image.LANCZOS)
    logo_x = (W - logo.width) // 2
    logo_y = LOGO_TOP
    img.alpha_composite(logo, (logo_x, logo_y))

    draw = ImageDraw.Draw(img)

    # Titre centré sous le logo
    title_font = _find_font(22, bold=True)
    tw = draw.textlength(APP_TITLE, font=title_font)
    title_y = logo_y + logo.height + TITLE_GAP
    draw.text(((W - tw) / 2, title_y), APP_TITLE, font=title_font, fill=COLOR_TITLE)

    # Séparateur fin au-dessus de la zone réservée au texte de progression
    sep_y = H - FOOTER_H
    draw.line([(24, sep_y), (W - 24, sep_y)], fill=COLOR_BORDER, width=1)

    # Cadre extérieur : simple bordure grise
    draw.rectangle([0, 0, W - 1, H - 1], outline=COLOR_BORDER, width=1)

    # os.makedirs(os.path.dirname(SPLASH_OUT), exist_ok=True)
    img.convert("RGB").save(SPLASH_OUT, "PNG")  # aplati : aucune transparence
    print(f"Splash généré : {SPLASH_OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
