# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |-> classe de gestion des calques image  """


from PIL import Image, UnidentifiedImageError, ImageDraw
import tkinter as tk
from .layer import Layer

class LayerExcluZone(Layer):
    """
    Calque contenant les zone d'exclusion.
    """

    def __init__(self, tkparent, parent, canva_size, image_size, ratio, name='ZoneEx'):
        """
        Args:
            parent (object): Widget parent pour les boîtes de dialogue.
            name (str): Nom du calque.
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

        tk.Label(frame, text="calque zone d'exclusion").pack(anchor='nw')