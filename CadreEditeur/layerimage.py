# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |-> classe de gestion des calques image  """


from PIL import Image, UnidentifiedImageError
import tkinter as tk
from tkinter import filedialog, messagebox
from .layer import Layer

class LayerImage(Layer):
    """
    Calque image importée, redimensionnable et positionnable.
    """

    def __init__(self, tkparent, parent, canva_size, image_size, ratio, name='Image'):
        """
        Args:
            parent (object): Widget parent pour les boîtes de dialogue.
            canva_size (tuple): Dimensions du canvas d’édition.
            image_size (tuple): Dimensions de l’image export.
            ratio (int): rapport image/canvas.
            name (str): Nom du calque.
        """
        super().__init__(name, canva_size, image_size, ratio)
        self.tkparent = tkparent
        self.parent = parent
        self.layer_type = 'Image'
        self.imported_image_path = None
        self.original_image = None
        self.display_imported_image = None
        self.display_imported_image_size = (0, 0)
        self.image_imported_image = None
        self.image_imported_image_size = (0, 0)
        self.img_start_drag_pos = None

    def import_image(self):
        """
        Ouvre un dialogue pour importer une image locale.
        Met à jour la miniature de prévisualisation et l’image exportable.

        Returns:
            bool: True si import OK, False sinon.
        """
        self.imported_image_path = filedialog.askopenfilename(parent=self.tkparent)
        if not self.imported_image_path:
            return False
        try:
            self.original_image = Image.open(self.imported_image_path).convert('RGBA')
        except UnidentifiedImageError:
            messagebox.showerror("Erreur d'image", "Image corrompue ou illisible.", parent=self.tkparent)
            return False
        except Exception as e:
            messagebox.showerror("Erreur d'image", str(e), parent=self.tkparent)
            return False
        w0, h0 = self.original_image.size
        aspect = w0 / h0
        desired_w = self.CANVA_W
        desired_h = int(desired_w / aspect)
        self.display_imported_image_size = (desired_w, desired_h)
        self.image_imported_image_size = (desired_w * self.RATIO, desired_h * self.RATIO)
        self.display_imported_image = self.original_image.resize(self.display_imported_image_size)
        self.image_imported_image = self.original_image.resize(self.image_imported_image_size)
        return True

    def resize(self, delta):
        """
        Redimensionne l’image importée en conservant le ratio.

        Args:
            delta (int): Variation de la largeur du calque (en px).
        """
        if not self.original_image:
            return
        w0, h0 = self.original_image.size
        aspect = w0 / h0
        new_w = self.display_imported_image_size[0] + delta
        new_h = int(new_w / aspect)
        new_w = max(15, new_w)
        new_h = max(10, new_h)
        self.display_imported_image_size = (new_w, new_h)
        self.image_imported_image_size = (new_w * self.RATIO, new_h * self.RATIO)
        self.display_imported_image = self.original_image.resize(self.display_imported_image_size)
        self.image_imported_image = self.original_image.resize(self.image_imported_image_size)

    def draw_on_image(self, image, export=False):
        """
        Dessine ce calque image sur une image PIL.

        Args:
            image (PIL.Image): image PIL.
            export (bool): True pour l’image export.
        """
        if not self.visible or not self.display_imported_image:
            return
        to_paste = self.image_imported_image if export else self.display_imported_image
        pos = self.image_position if export else self.display_position
        image.paste(to_paste, (int(pos[0]), int(pos[1])), to_paste)

    def update_param_zone(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

        tk.Label(frame, text=f"calque {self.name}").pack(anchor='nw')

    def clone(self, tkparent, parent):
        """
        Crée une copie indépendante de ce LayerImage (mêmes réglages, nouvelle instance)
        """
        new_layer = LayerImage(
            tkparent,
            parent,
            (self.CANVA_W, self.CANVA_H),
            (self.IMAGE_W, self.IMAGE_H),
            self.RATIO,
            name=self.name + "_copie"
        )
        new_layer.display_position         = tuple(self.display_position)
        new_layer.image_position           = tuple(self.image_position)
        new_layer.visible                  = self.visible
        new_layer.locked                   = self.locked

        new_layer.imported_image_path      = self.imported_image_path
        # Pour les images PIL : il faut vraiment cloner la donnée ! (sans 'link')
        if self.original_image is not None:
            new_layer.original_image           = self.original_image.copy()
        if self.display_imported_image is not None:
            new_layer.display_imported_image   = self.display_imported_image.copy()
        new_layer.display_imported_image_size  = tuple(self.display_imported_image_size)
        if self.image_imported_image is not None:
            new_layer.image_imported_image     = self.image_imported_image.copy()
        new_layer.image_imported_image_size    = tuple(self.image_imported_image_size)

        # Si tu utilises self.img_start_drag_pos (temporaire), à ne pas copier
        return new_layer

    def to_dict(self):
        """Retourne un dict serializable décrivant l’état du calque."""
        return {
            "class": "LayerImage",
            "layer_type": self.layer_type,
            "name": self.name,
            "display_position": self.display_position,
            "image_position": self.image_position,
            "visible": self.visible,
            "locked": self.locked,
            "imported_image_path": self.imported_image_path,
        }
    @staticmethod
    def from_dict(dct, tkparent, parent, canva_size, image_size, ratio, name=None):
        """
        Recrée un LayerImage à partir d'un dictionnaire sérialisé.

        Args:
            dct (dict): dictionnaire provenant du to_dict().
            tkparent (tk.Widget): parent pour le widget (frame).
            parent : instance appelante
            canva_size (tuple): (largeur, hauteur) du canvas affichage.
            image_size (tuple): (largeur, hauteur) pour export.
            ratio (int): rapport export/canvas.
            name (str, optionnel): nom du calque.

        Returns:
            LayerImage: un nouveau calque image restauré.
        """
        obj = LayerImage(tkparent,
                         parent,
                         canva_size,
                         image_size,
                         ratio,
                         name=dct.get("name", name or "Image"))
        obj.display_position = tuple(dct.get("display_position", (0, 0)))
        obj.image_position = tuple(dct.get("image_position", (0, 0)))
        obj.visible = dct.get("visible", True)
        obj.locked = dct.get("locked", False)
        obj.imported_image_path = dct.get("imported_image_path")

        # Recharge l’image si chemin présent
        if obj.imported_image_path:
            try:
                obj.original_image = Image.open(obj.imported_image_path).convert('RGBA')
                w0, h0 = obj.original_image.size
                aspect = w0 / h0
                desired_w = obj.CANVA_W
                desired_h = int(desired_w / aspect)
                obj.display_imported_image_size = (desired_w, desired_h)
                obj.image_imported_image_size = (desired_w * obj.RATIO, desired_h * obj.RATIO)
                obj.display_imported_image = obj.original_image.resize(obj.display_imported_image_size)
                obj.image_imported_image = obj.original_image.resize(obj.image_imported_image_size)
            except Exception as e:
                obj.original_image = None  # image absente/non trouvée
        return obj
