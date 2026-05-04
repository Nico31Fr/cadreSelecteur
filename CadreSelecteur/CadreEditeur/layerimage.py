# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |→ classe de gestion des calques image  """

from PIL import Image, UnidentifiedImageError
import tkinter as tk
from tkinter import filedialog, messagebox
from .layer import Layer
from os.path import basename
import shutil
import logging
# Import du traducteur
from ..i18n import t

logger = logging.getLogger(__name__)


class LayerImage(Layer):
    """
    Calque image importée, redimensionnable et positionable.
    """

    def __init__(self, tk_parent, parent, canva_size, image_size, ratio, name='Image', base_dir=None):
        """
        Args:
            parent (object): Widget parent pour les boîtes de dialogue.
            canva_size (tuple): Dimensions du canvas d'édition.
            image_size (tuple): Dimensions de l'image export.
            ratio (int): rapport image/canvas.
            name (str): Nom du calque.
            base_dir (str or Path): Répertoire de base pour les chemins relatifs (optionnel).
        """
        super().__init__(name, canva_size, image_size, ratio)
        self.tk_parent = tk_parent
        self.parent = parent
        self.base_dir = base_dir
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
        Copie l'image dans {base_dir}/Images/ et stocke le chemin relatif.
        Met à jour la miniature de prévisualisation et l'image exportable.

        Returns :
            bool : True si import OK, False sinon.
        """
        from pathlib import Path

        imported_path = filedialog.askopenfilename(parent=self.tk_parent)
        if not imported_path:
            return False

        try:
            # Valider l'image avant de la copier
            self.original_image = Image.open(imported_path).convert('RGBA')
        except UnidentifiedImageError:
            messagebox.showerror("Erreur d'image", "Image corrompue ou illisible.", parent=self.tk_parent)
            return False
        except Exception as e:
            messagebox.showerror("Erreur d'image", str(e), parent=self.tk_parent)
            return False

        # Copier l'image dans {base_dir}/Images/ si base_dir est défini
        if self.base_dir:
            try:
                base_dir_path = Path(self.base_dir)
                images_dir = base_dir_path / "Images"
                images_dir.mkdir(parents=True, exist_ok=True)

                # Obtenir le nom du fichier
                filename = Path(imported_path).name
                destination_path = images_dir / filename

                # Copier le fichier
                shutil.copy2(imported_path, destination_path)

                # Stocker le chemin relatif
                self.imported_image_path = f"Images/{filename}"
                logger.info(f"Image copiée dans {destination_path}")
            except Exception as e:
                logger.warning(f"Erreur lors de la copie de l'image: {e}")
                # Fallback: utiliser le chemin absolu
                self.imported_image_path = imported_path
        else:
            # Si base_dir n'est pas défini, utiliser le chemin absolu
            self.imported_image_path = imported_path

        # Recalculer les dimensions
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

        Args :
            delta (int) : Variation de la largeur du calque (en px).
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

    def draw_on_image(self, image: Image.Image, export=False):
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

        info = t('layerimage.label.info',
                 name=self.name,
                 filename=(basename(self.imported_image_path) if self.imported_image_path else ''),
                 position=self.image_position,
                 size=self.image_imported_image_size)
        tk.Label(frame, justify="left", text=info).pack(anchor='nw')

    def clone(self, tk_parent, parent):
        """
        Crée une copie indépendante de ce LayerImage (mêmes réglages, nouvelle instance)
        """
        new_layer = LayerImage(
            tk_parent,
            parent,
            (self.CANVA_W, self.CANVA_H),
            (self.IMAGE_W, self.IMAGE_H),
            self.RATIO,
            name=self.name + "_copie",
            base_dir=self.base_dir
        )
        new_layer.display_position = tuple(self.display_position)
        new_layer.image_position = tuple(self.image_position)
        new_layer.visible = self.visible
        new_layer.locked = self.locked

        new_layer.imported_image_path = self.imported_image_path
        # Pour les images PIL il faut vraiment cloner la donnée! (sans 'link')
        if self.original_image is not None:
            new_layer.original_image = self.original_image.copy()
        if self.display_imported_image is not None:
            new_layer.display_imported_image = self.display_imported_image.copy()
        new_layer.display_imported_image_size = tuple(self.display_imported_image_size)
        if self.image_imported_image is not None:
            new_layer.image_imported_image = self.image_imported_image.copy()
        new_layer.image_imported_image_size = tuple(self.image_imported_image_size)

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
            'display_imported_image_size': self.display_imported_image_size,
            'image_imported_image_size': self.image_imported_image_size,
        }

    @staticmethod
    def from_dict(dct, tk_parent, parent, canva_size, image_size, ratio, name=None, base_dir=None):
        """
        Recrée un LayerImage à partir d'un dictionnaire sérialisé.

        Args:
            dct (dict): dictionnaire provenant du to_dict().
            tk_parent (tk.Widget): parent pour le widget (frame).
            parent : instance appelante
            canva_size (tuple): (largeur, hauteur) du canvas affichage.
            image_size (tuple): (largeur, hauteur) pour export.
            ratio (int): rapport export/canvas.
            name (str, optionnel): nom du calque.
            base_dir (str or Path): Répertoire de base pour les chemins relatifs (optionnel).

        Returns:
            LayerImage: un nouveau calque image restauré.
        """
        obj = LayerImage(tk_parent,
                         parent,
                         canva_size,
                         image_size,
                         ratio,
                         name=dct.get("name", name or "Image"),
                         base_dir=base_dir)
        obj.display_position = tuple(dct.get("display_position", (0, 0)))
        obj.image_position = tuple(dct.get("image_position", (0, 0)))
        obj.visible = dct.get("visible", True)
        obj.locked = dct.get("locked", False)
        obj.imported_image_path = dct.get("imported_image_path")
        obj.display_imported_image_size = tuple(dct.get("display_imported_image_size", (obj.CANVA_W, obj.CANVA_H)))
        obj.image_imported_image_size = tuple(dct.get("image_imported_image_size", (obj.IMAGE_W, obj.IMAGE_H)))

        # Recharge l’image si chemin présent
        if obj.imported_image_path:
            try:
                from pathlib import Path
                # Résoudre le chemin relatif en chemin absolu si base_dir est défini
                image_path = obj.imported_image_path
                if base_dir and not Path(image_path).is_absolute():
                    image_path = str(Path(base_dir) / image_path)

                obj.original_image = Image.open(image_path).convert('RGBA')
                obj.display_imported_image = obj.original_image.resize(obj.display_imported_image_size)
                obj.image_imported_image = obj.original_image.resize(obj.image_imported_image_size)
            except FileNotFoundError:
                logger.warning(f"Fichier non trouvé: {obj.imported_image_path}")
                obj.original_image = None
            except UnidentifiedImageError:
                logger.warning(f"Erreur d'identification de l'image: {obj.imported_image_path}")
                obj.original_image = None
            except IOError:
                logger.warning(f"Erreur E/S: {obj.imported_image_path}")
                obj.original_image = None

        return obj
