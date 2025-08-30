# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |-> classe de gestion des calques image  """


from PIL import ImageDraw
import tkinter as tk
from .layer import Layer

class LayerExcluZone(Layer):
    """
    Calque contenant les zone d'exclusion.
    """

    def __init__(self, tkparent, parent, canva_size, image_size, ratio, name='ZoneEx'):
        """
        Args:
            tkparent (tk.Widget): parent pour le widget (frame).
            parent : instance appelante
            canva_size (tuple): (largeur, hauteur) du canvas affichage.
            image_size (tuple): (largeur, hauteur) pour export.
            ratio (int): rapport export/canvas.
            name (str, optionnel): nom du calque.
        """
        super().__init__(name, canva_size, image_size, ratio)
        self.parent = parent
        self.tkparent = tkparent
        self.name = name
        self.layer_type = 'ZoneEx'
        self.exclusion_zone = [(0,0,0,0)]

    def set_exclusion_zone(self, value):
        """
        Modifie le texte du calque.

        Args:
            value (str): nouveau texte.
        """
        self.exclusion_zone = value

    def draw_on_image(self, image, export=False):
        """
        Dessine ce calque image sur une image PIL.

        Args:
            image (PIL.Image): image PIL.
            export (bool): True pour l’image export.
        """
        if not self.visible or not self.exclusion_zone:
            return
        # insère les zones transparentes (Display et Image)
        draw_i = ImageDraw.Draw(image)
        local_ratio = self.RATIO if export else 1
        for d_x, d_y, d_w, d_h in self.exclusion_zone:
            i_x, i_y, i_w, i_h = (d_x * local_ratio,
                                  d_y * local_ratio,
                                  d_w * local_ratio,
                                  d_h * local_ratio)
            draw_i.rectangle((i_x, i_y, i_x + i_w, i_y + i_h), fill=(255, 255, 255, 0))

    def update_param_zone(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

        tk.Label(frame, text='calque zone d\'exclusion').pack(anchor='nw')

    def clone(self, tkparent, parent):
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

    def from_dict(dct, tkparent, parent, canva_size, image_size, ratio, name=None):
        """
        Recrée un LayerExcluZone à partir d'un dictionnaire sérialisé.

        Args:
            dct (dict): dictionnaire provenant du to_dict().
            parent (tk.Widget): parent pour le widget (frame).
            canva_size (tuple): (largeur, hauteur) du canvas affichage.
            image_size (tuple): (largeur, hauteur) pour export.
            ratio (int): rapport export/canvas.
            name (str, optionnel): nom du calque.

        Returns:
            LayerExcluZone: un nouveau calque texte restauré.
        """
        obj = LayerExcluZone(tkparent,
                             parent,
                             canva_size,
                             image_size,
                             ratio,
                             name=dct.get('name', name or 'ZoneEx'))
        obj.display_position = tuple(dct.get('display_position', (0, 0)))
        obj.image_position = tuple(dct.get('image_position', (0, 0)))
        obj.visible = dct.get('visible', True)
        obj.locked = dct.get('locked', False)
        obj.exclusion_zone = dct.get('exclusion_zone', False)
        return obj