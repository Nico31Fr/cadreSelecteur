# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |-> classe de gestion des calques texte  """

from PIL import ImageFont, ImageDraw
from .layer import Layer


class LayerText(Layer):
    """
    Calque texte éditable, positionnable, redimensionnable.
    """

    def __init__(self, parent, canva_size, image_size, ratio, name="Text"):
        """
        Args:
            parent (object): widget parent Tkinter.
            canva_size, image_size, ratio : cf. Layer.
            name (str): nom du calque.
        """
        super().__init__(name, canva_size, image_size, ratio)
        self.parent = parent
        self.layer_type = "text"
        self.text = "Texte"
        self.font_color = "#000000"
        self.sel_font = {'family': "arial", 'size': 32}
        self.font_name = "arial.ttf"
        self.pil_font = ImageFont.truetype(self.font_name, self.sel_font['size'])
        self.txt_start_drag_pos = None

    def set_text(self, value):
        """
        Modifie le texte du calque.

        Args:
            value (str): nouveau texte.
        """
        self.text = value

    def resize_font(self, delta):
        """
        Redimensionne la police utilisée dans le calque.

        Args:
            delta (int): Variation (en px) de la taille.
        """
        new_size = max(4, self.sel_font['size'] + delta)
        self.sel_font['size'] = new_size
        self.pil_font = ImageFont.truetype(self.font_name, self.sel_font['size'])

    def draw_on_image(self, image, export=False):
        """
        Dessine le texte sur l’image PIL, à la position courante.

        Args:
            image (PIL.Image): Image cible.
            export (bool): True pour la résolution export.
        """
        if not self.visible or not self.text:
            return
        pos = self.image_position if export else self.display_position
        size = self.sel_font['size'] * self.RATIO if export else self.sel_font['size']
        font = ImageFont.truetype(self.font_name, size)
        draw = ImageDraw.Draw(image)
        draw.text(pos, self.text, fill=self.font_color, font=font)
