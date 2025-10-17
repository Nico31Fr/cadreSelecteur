# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |→ classe de gestion des calques texte  """

from PIL import ImageFont, ImageDraw, Image
import tkinter as tk
from tkinter import messagebox, colorchooser
import os
import sys

from .layer import Layer
from .text import ask_font


def resource_path(relative_path):
    """Retourne le chemin absolu du fichier embarqué (compatible PyInstaller)."""
    # Accès à _MEIPASS nécessaire pour la compatibilité avec PyInstaller
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))  # type: ignore[attr-defined]
    return os.path.join(base_path, relative_path)


class LayerText(Layer):
    """
    Calque texte éditable, positionable, redimensionnable.
    """

    def __init__(self, tk_parent, parent, canva_size, image_size, ratio, name="Text"):
        """
        Args:
            parent (object): widget parent Tkinter.
            canva_size, image_size, ratio : cf. Layer.
            name (str): nom du calque.
        """
        super().__init__(name, canva_size, image_size, ratio)
        self.tk_parent = tk_parent
        self.parent = parent
        self.layer_type = 'Texte'

        # Variables texte
        self.text = tk.StringVar(value='Texte')
        self.font_color = '#000000'
        self.sel_font = {'family': "arial", 'size': 32}

        # Répertoire Fonts (embarquable)
        self.fonts_dir = resource_path('./Fonts')

        # Police par défaut
        self.font_name = self.find_font_path(self.sel_font['family']) or resource_path("Fonts/arial.ttf")
        self.pil_font = ImageFont.truetype(str(self.font_name), self.sel_font['size'])

        self.txt_start_drag_pos = None

    def set_text(self, value):
        """Modifie le texte du calque."""
        self.text = value

    def resize_font(self, delta):
        """Redimensionne la police utilisée dans le calque."""
        new_size = max(4, self.sel_font['size'] + delta)
        self.sel_font['size'] = new_size
        self.pil_font = ImageFont.truetype(str(self.font_name), self.sel_font['size'])

    def draw_on_image(self, image: Image.Image, export=False):
        """Dessine le texte sur l’image PIL, à la position courante."""
        if not self.visible or not self.text:
            return
        pos = self.image_position if export else self.display_position
        size = self.sel_font['size'] * self.RATIO if export else self.sel_font['size']
        font = ImageFont.truetype(str(self.font_name), size)
        draw = ImageDraw.Draw(image)
        draw.text(pos, self.text.get(), fill=self.font_color, font=font)

    def update_param_zone(self, frame):
        """Met à jour la zone de paramètres du panneau latéral."""
        for widget in frame.winfo_children():
            widget.destroy()

        tk.Label(frame, text=f"calque {self.name}").pack(anchor='nw')
        tk.Entry(frame,
                 textvariable=self.text, width=40).pack(padx=5, pady=5, anchor='nw')
        tk.Button(frame,
                  text='Couleur',
                  command=lambda: self.choisir_couleur()).pack(padx=5, pady=5, side='top', anchor='nw')
        tk.Button(frame,
                  text='Police',
                  command=self.callback_font).pack(padx=5, pady=5, side='top', anchor='nw')
        self.text.trace_add("write", self.on_text_change)

    def callback_font(self):
        """
        Lorsque le bouton Police est cliqué :
        ouvre la fenêtre ask_font() et charge la police sélectionnée
        depuis le répertoire Fonts/.
        """
        try:
            font_selected = ask_font(self.tk_parent,
                                     text=self.text.get(),
                                     title="Choisir une police",
                                     family=self.sel_font['family'],
                                     size=self.sel_font['size'])

            if font_selected:
                self.sel_font = font_selected
                family = self.sel_font['family']

                # Recherche dans le dossier Fonts
                font_name_found = self.find_font_path(family)
                if font_name_found:
                    self.font_name = font_name_found
                    self.pil_font = ImageFont.truetype(self.font_name, self.sel_font['size'])
                else:
                    messagebox.showwarning("Police introuvable",
                                           f"La police '{family}' n'a pas été trouvée dans Fonts/. "
                                           "Police par défaut utilisée.")
                    self.font_name = resource_path("Fonts/arial.ttf")

            self.parent.update_canvas()

        except Exception as e:
            messagebox.showerror("Erreur de font", f"Exception inattendue : {str(e)}")

    def find_font_path(self, font_name_to_find):
        """
        Trouve le chemin de la police dans le dossier Fonts.
        Renvoie le chemin complet si trouvé, sinon None.
        """
        try:
            if not os.path.isdir(self.fonts_dir):
                print(f"[AVERTISSEMENT] Dossier Fonts introuvable : {self.fonts_dir}")
                return None

            for file in os.listdir(str(self.fonts_dir)):
                if not file.lower().endswith(".ttf"):
                    continue
                name_no_ext = os.path.splitext(file)[0]
                # Correspondance tolérante : ignore les espaces / majuscules
                if name_no_ext.lower().replace(" ", "") == font_name_to_find.lower().replace(" ", ""):
                    return os.path.join(str(self.fonts_dir), file)

            return None

        except Exception as e:
            messagebox.showerror("Erreur de police", f"Exception inattendue: {str(e)}")
            return None

    def choisir_couleur(self):
        """Ouvre une boîte de dialogue de sélection de couleur."""
        try:
            couleur = colorchooser.askcolor(title="Choisissez une couleur")
            self.font_color = couleur[1]
            self.parent.update_canvas()

        except Exception as e:
            messagebox.showerror("Erreur de couleur", f"Exception inattendue : {str(e)}")

    def on_text_change(self, *args):
        """Met à jour le texte sur le canvas quand il change."""
        try:
            if args:
                self.parent.update_canvas()
        except Exception as e:
            messagebox.showerror("Erreur de texte", f"Exception inattendue : {str(e)}")

    def clone(self, tk_parent, parent):
        """Crée une copie indépendante de ce LayerText (mêmes réglages, nouvelle instance)."""
        new_layer = LayerText(
            tk_parent,
            parent,
            (self.CANVA_W, self.CANVA_H),
            (self.IMAGE_W, self.IMAGE_H),
            self.RATIO,
            name=self.name + "_copie"
        )
        new_layer.display_position = tuple(self.display_position)
        new_layer.image_position = tuple(self.image_position)
        new_layer.visible = self.visible
        new_layer.locked = self.locked
        new_layer.text.set(self.text.get())
        new_layer.font_color = self.font_color
        new_layer.sel_font = self.sel_font.copy()
        new_layer.font_name = self.font_name
        new_layer.pil_font = ImageFont.truetype(str(self.font_name), self.sel_font['size'])
        return new_layer

    def to_dict(self):
        """Retourne un dict serializable décrivant l’état du calque."""

        return {
            "class": "LayerText",
            "layer_type": self.layer_type,
            "name": self.name,
            "display_position": self.display_position,
            "image_position": self.image_position,
            "visible": self.visible,
            "locked": self.locked,
            "text": self.text.get(),
            "font_color": self.font_color,
            "sel_font": self.sel_font,
            "font_name": self.font_name,
        }

    @staticmethod
    def from_dict(dct, tk_parent, parent, canva_size, image_size, ratio, name=None):
        """
        Recrée un LayerText à partir d'un dictionnaire sérialisé.

        Args:
            dct (dict): dictionnaire provenant du to_dict().
            tk_parent (tk.Widget): parent pour le widget (frame).
            parent : instance appelante
            canva_size (tuple): (largeur, hauteur) du canvas affichage.
            image_size (tuple): (largeur, hauteur) pour export.
            ratio (int): rapport export/canvas.
            name (str, optionnel): nom du calque.

        Returns:
            LayerText: un nouveau calque texte restauré.
        """
        obj = LayerText(
            tk_parent,
            parent,
            canva_size,
            image_size,
            ratio,
            name=dct.get("name", name or "Texte")
        )
        obj.display_position = tuple(dct.get("display_position", (0, 0)))
        obj.image_position = tuple(dct.get("image_position", (0, 0)))
        obj.visible = dct.get("visible", True)
        obj.locked = dct.get("locked", False)
        obj.text.set(dct.get("text", "Texte"))
        obj.font_color = dct.get("font_color", "#000000")
        obj.sel_font = dict(dct.get("sel_font", {"family": "arial", "size": 32}))
        obj.font_name = obj.find_font_path(obj.sel_font['family']) or resource_path("Fonts/arial.ttf")
        obj.pil_font = ImageFont.truetype(str(obj.font_name), obj.sel_font['size'])
        return obj
