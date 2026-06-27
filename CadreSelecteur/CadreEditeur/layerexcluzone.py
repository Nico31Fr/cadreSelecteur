# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |→ classe de gestion des calques image  """


import tkinter as tk
from math import radians, cos, sin
from pathlib import Path
from PIL import ImageDraw, Image
from .layer import Layer
from ..i18n import t
from ..path_resolver import resolve_resources_dir

class LayerExcluZone(Layer):
    """
    Calque contenant les zones d'exclusion (avec gestion de la rotation).
    """

    def __init__(self, tk_parent, parent, canva_size, image_size, ratio, name='ZoneEx'):
        super().__init__(name, canva_size, image_size, ratio)
        self.parent = parent
        self.tk_parent = tk_parent
        self.name = name
        self.layer_type = 'ZoneEx'
        # Format attendu : [(x, y, w, h, angle)] ou ancien format [(x, y, w, h)]
        self.exclusion_zone = [(0, 0, 0, 0, 0)]

    def set_exclusion_zone(self, value):
        self.exclusion_zone = value

    def draw_on_image(self, image: Image.Image, export=False):
        """
        Dessine les zones d'exclusion et, en mode édition, les images de substitution.
        Gère la rotation des zones.
        """
        if not self.visible or not self.exclusion_zone:
            return

        draw_i = ImageDraw.Draw(image)
        local_ratio = self.RATIO if export else 1

        res_dir = resolve_resources_dir()

        for i, zone_data in enumerate(self.exclusion_zone):
            # Rétrocompatibilité : vérifie si l'angle est présent dans les données
            if len(zone_data) == 5:
                d_x, d_y, d_w, d_h, angle = zone_data
            else:
                d_x, d_y, d_w, d_h = zone_data
                angle = 0

            i_x, i_y, i_w, i_h = (d_x * local_ratio, d_y * local_ratio,
                                  d_w * local_ratio, d_h * local_ratio)

            # Calcul du centre de la zone (nécessaire pour pivoter proprement)
            c_x = i_x + (i_w / 2)
            c_y = i_y + (i_h / 2)

            if not export:
                # --- MODE ÉDITION : Affichage de l'image de substitution ---
                img_path = res_dir / f"photo{i + 1}.png"
                if img_path.exists():
                    try:
                        placeholder = Image.open(img_path).convert("RGBA")
                        # 1. Mise à l'échelle
                        placeholder = placeholder.resize((int(i_w), int(i_h)), Image.Resampling.LANCZOS)

                        # 2. Rotation si nécessaire
                        if angle != 0:
                            # expand=True évite que les coins de l'image soient coupés lors de la rotation
                            placeholder = placeholder.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

                        # 3. Recalcul des coordonnées de collage pour centrer l'image pivotée
                        p_w, p_h = placeholder.size
                        paste_x = int(c_x - (p_w / 2))
                        paste_y = int(c_y - (p_h / 2))

                        image.paste(placeholder, (paste_x, paste_y), placeholder)
                    except Exception as e:
                        print(f"Erreur chargement image {img_path}: {e}")
            else:
                # --- MODE EXPORT : Dessin de la zone d'exclusion (trou) ---
                if angle != 0:
                    # On utilise la trigonométrie pour calculer les 4 coins pivotés
                    # On inverse l'angle car l'axe Y est orienté vers le bas en traitement d'image
                    rad = radians(-angle)

                    def rotate_pt(px, py):
                        dx, dy = px - c_x, py - c_y
                        nx = dx * cos(rad) - dy * sin(rad)
                        ny = dx * sin(rad) + dy * cos(rad)
                        return (nx + c_x, ny + c_y)

                    # Calcul des sommets du polygone (Haut-Gauche, Haut-Droit, Bas-Droit, Bas-Gauche)
                    p1 = rotate_pt(i_x, i_y)
                    p2 = rotate_pt(i_x + i_w, i_y)
                    p3 = rotate_pt(i_x + i_w, i_y + i_h)
                    p4 = rotate_pt(i_x, i_y + i_h)

                    # On trace un polygone orienté à la place d'un rectangle standard
                    draw_i.polygon([p1, p2, p3, p4], fill=(255, 255, 255, 0))
                else:
                    # Traitement standard si pas de rotation (plus rapide)
                    draw_i.rectangle((i_x, i_y, i_x + i_w, i_y + i_h), fill=(255, 255, 255, 0))

    def update_param_zone(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()
        tk.Label(frame, text=t('layer.exclusion_name')).pack(anchor='nw')

    def clone(self, tk_parent, parent):
        pass

    def to_dict(self):
        """Retourne un dict serializable décrivant l’état du calque."""
        return {
            'class': 'LayerExcluZone',
            'layer_type': 'ZoneEx',
            'name': self.name,
            'display_position': self.display_position,
            'image_position': self.image_position,
            'visible': self.visible,
            'locked': self.locked,
            'exclusion_zone': self.exclusion_zone
        }

    @staticmethod
    def from_dict(dct, tk_parent, parent, canva_size, image_size, ratio, name=None, base_dir=None, frame_dir=None):
        """
        Recrée un LayerExcluZone à partir d'un dictionnaire sérialisé.

        Args:
            dct (dict): dictionnaire provenant du to_dict().
            tk_parent (tk.Widget): parent pour le widget (frame).
            parent : instance appelante
            canva_size (tuple): (largeur, hauteur) du canvas affichage.
            image_size (tuple): (largeur, hauteur) pour export.
            ratio (int): rapport export/canvas.
            name (str, optionnel): nom du calque.
            base_dir (str or Path): Répertoire de base (non utilisé pour zones d'exclusion).
            frame_dir (str or Path): Répertoire du cadre (non utilisé pour zones d'exclusion).

        Returns:
            LayerExcluZone: un nouveau calque texte restauré.
        """
        obj = LayerExcluZone(tk_parent,
                             parent,
                             canva_size,
                             image_size,
                             ratio,
                             name=dct.get('name', name or 'ZoneEx'))
        obj.display_position = tuple(dct.get('display_position', (0, 0)))
        obj.image_position = tuple(dct.get('image_position', (0, 0)))
        obj.visible = dct.get('visible', True)
        obj.locked = dct.get('locked', False)
        # S'assure de récupérer la zone correctement, qu'elle ait 4 ou 5 paramètres
        obj.exclusion_zone = dct.get('exclusion_zone', [(0, 0, 0, 0, 0)])
        return obj
