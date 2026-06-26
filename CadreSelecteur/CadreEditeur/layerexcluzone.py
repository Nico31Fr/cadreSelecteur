# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |→ classe de gestion des calques image  """

import os
from PIL import ImageDraw, Image
import tkinter as tk
from .layer import Layer
from ..i18n import t


class LayerExcluZone(Layer):
    """
    Calque contenant les zone d'exclusion.
    """

    def __init__(self, tk_parent, parent, canva_size, image_size, ratio, name='ZoneEx'):
        """
        Args:
            tk_parent (tk.Widget): parent pour le widget (frame).
            parent : instance appelante
            canva_size (tuple): (largeur, hauteur) du canvas affichage.
            image_size (tuple): (largeur, hauteur) pour export.
            ratio (int): rapport export/canvas.
            name (str, optionnel): nom du calque.
        """
        super().__init__(name, canva_size, image_size, ratio)
        self.parent = parent
        self.tk_parent = tk_parent
        self.name = name
        self.layer_type = 'ZoneEx'
        self.exclusion_zone = [(0, 0, 0, 0)]

    def set_exclusion_zone(self, value):
        """
        Modifie le texte du calque.

        Args:
            value (str): nouveau texte.
        """
        self.exclusion_zone = value

    def draw_on_image(self, image: Image.Image, export=False):
        """
        Dessine les zones d'exclusion et, en mode édition, les images de substitution.

        Args:
            image (PIL.Image): image PIL.
            export (bool): True pour l’image export, False pour l’édition.
        """
        if not self.visible or not self.exclusion_zone:
            return

        # Calcul des dimensions et positions
        draw_i = ImageDraw.Draw(image)
        local_ratio = self.RATIO if export else 1

        # Répertoire des ressources (basé sur le dossier parent du module)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        res_dir = os.path.join(base_dir, "resources")

        for i, (d_x, d_y, d_w, d_h) in enumerate(self.exclusion_zone):
            i_x, i_y, i_w, i_h = (d_x * local_ratio, d_y * local_ratio,
                                  d_w * local_ratio, d_h * local_ratio)

            # Insertion des images de substitution UNIQUEMENT si export est False
            if not export:
                img_path = os.path.join(res_dir, f"photo{i + 1}.png")
                if os.path.exists(img_path):
                    try:
                        placeholder = Image.open(img_path).convert("RGBA")
                        placeholder = placeholder.resize((int(i_w), int(i_h)))
                        image.paste(placeholder, (int(i_x), int(i_y)), placeholder)
                    except Exception as e:
                        # Log de l'erreur sans bloquer l'application
                        print(f"Erreur chargement image {img_path}: {e}")
            else:
                # Dessin du rectangle transparent (ou contour)
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
        obj.exclusion_zone = dct.get('exclusion_zone', [(0,0,0,0)])
        return obj
