# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |-> classe de gestion des calques texte  """

from PIL import ImageFont, ImageDraw
import tkinter as tk
from tkinter import messagebox, colorchooser
import matplotlib.font_manager as fm

from .layer import Layer
from .text import askfont

class LayerText(Layer):
    """
    Calque texte éditable, positionnable, redimensionnable.
    """

    def __init__(self, tkparent, parent, canva_size, image_size, ratio, name="Text"):
        """
        Args:
            parent (object): widget parent Tkinter.
            canva_size, image_size, ratio : cf. Layer.
            name (str): nom du calque.
        """
        super().__init__(name, canva_size, image_size, ratio)
        self.tkparent = tkparent
        self.parent = parent
        self.layer_type = "text"
        # variables texte
        self.text = tk.StringVar(value='Texte')
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
        draw.text(pos, self.text.get(), fill=self.font_color, font=font)

    def update_param_zone(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

        tk.Label(frame, text=f"calque {self.name}").pack(anchor='nw')
        # bouton et saisie pour le texte
        tk.Entry(frame,
                 textvariable=self.text, width=40).pack(padx=10, pady=10, anchor='nw')
        tk.Button(frame,
                  text='Couleur',
                  command=lambda: self.choisir_couleur()).pack(padx=10, pady=10, side='top', anchor='nw')
        tk.Button(frame,
                  text='Police',
                  command=self.callback_font).pack(padx=10, pady=10, side='top', anchor='nw')
        self.text.trace_add("write", self.on_text_change)

    def callback_font(self):
        """
        lorsque le bouton font est cliqué lance l'interface
         de selection de police d'écriture
        """
        try:
            font_selected = askfont(self.tkparent,
                                    text=self.text.get(),
                                    title="Police",
                                    family=self.sel_font['family'],
                                    size=self.sel_font['size'],)

            # met à jour la police sélectionné
            if font_selected:
                self.sel_font = font_selected
                font_name_found = self.find_font_path(self.sel_font['family'])
                if font_name_found is not None:
                    self.font_name = font_name_found

            self.parent.update_canvas()

        except Exception as e:
            messagebox.showerror("Erreur de font", f"Exception inattendue : {str(e)}")

    @staticmethod
    def find_font_path(font_name_to_find):
        """
        trouve le chemin de la police
        """
        try:
            # Obtenir la liste de toutes les polices système
            font_paths = fm.findSystemFonts(fontpaths=None, fontext='ttf')

            for font_path in font_paths:
                # Vérifier si le nom de la police correspond
                prop = fm.FontProperties(fname=font_path)
                if prop.get_name().lower() == font_name_to_find.replace('@', '').lower():
                    return font_path
            return None
        except Exception as e:
            messagebox.showerror("Erreur de police", f"Exception inattendue: {str(e)}")
            return None

    # gestion couleur
    def choisir_couleur(self):
        """ Ouvrir une boîte de dialogue de sélection de couleur """
        try:
            couleur = colorchooser.askcolor(title="Choisissez une couleur")
            self.font_color = couleur[1]
            self.parent.update_canvas()

        except Exception as e:
            messagebox.showerror("Erreur de couleur", f"Exception inattendue : {str(e)}")

    def on_text_change(self, *args):
        """
        Ajoute du texte provenant du champ de texte
        à l'image à une position prédéfinie.
        """
        try:
            if args:
                self.parent.update_canvas()
        except Exception as e:
            messagebox.showerror("Erreur de texte", f"Exception inattendue : {str(e)}")