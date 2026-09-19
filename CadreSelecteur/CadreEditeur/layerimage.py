# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |→ classe de gestion des calques image  """

from PIL import Image, UnidentifiedImageError
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from os.path import basename
import shutil
import logging

from ..i18n import t
from .layer import Layer

logger = logging.getLogger(__name__)


class LayerImage(Layer):
    """
    Calque image importée, redimensionnable et positionable.
    """

    def __init__(self, tk_parent, parent, canva_size, image_size, ratio, name='Image'):
        """
        Args:
            parent (object): Widget parent pour les boîtes de dialogue.
            canva_size (tuple): Dimensions du canvas d'édition.
            image_size (tuple): Dimensions de l'image export.
            ratio (int): rapport image/canvas.
            name (str): Nom du calque.
            frame_dir (str or Path): Répertoire du cadre (Templates/<nom_du_cadre>/) pour stocker les images.
        """
        super().__init__(name, canva_size, image_size, ratio)
        self.tk_parent = tk_parent
        self.parent = parent
        self.frame_dir = getattr(parent, 'frame_dir', None)
        self.layer_type = 'Image'
        self.imported_image_path = None
        self.original_image = None
        self.display_imported_image = None
        self.display_imported_image_size = (0, 0)
        self.image_imported_image = None
        self.image_imported_image_size = (0, 0)
        self.img_start_drag_pos = None
        # Version export recalculée paresseusement : pendant le
        # redimensionnement interactif (molette), seule la version
        # d'affichage est reconstruite ; l'export suit à la demande.
        self._export_dirty = False

    def import_image(self):
        """
        Ouvre un dialogue pour importer une image locale.
        Copie l'image dans {frame_dir}
        Stocke le chemin relatif.

        Returns :
            bool : True si import OK, False sinon.
        """

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

        # Déterminer le répertoire de destination
        if self.frame_dir:
            try:
                frame_dir_path = Path(self.frame_dir)
                frame_dir_path.mkdir(parents=True, exist_ok=True)

                # Obtenir le nom du fichier
                filename = Path(imported_path).name
                destination_path = frame_dir_path / filename

                # Copier le fichier
                shutil.copy2(imported_path, destination_path)

                # Stocker le chemin relatif (juste le nom du fichier)
                self.imported_image_path = filename
                logger.info(f"Image copiée dans {destination_path}")
            except Exception as e:
                logger.warning(f"Erreur lors de l'import' de l'image: {e}")
                self.imported_image_path = imported_path
        else:
            # Si aucun répertoire n'est défini, utiliser le chemin absolu
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
        Redimensionne l'image importée en conservant le ratio.

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
        self._export_dirty = True

    def _ensure_export_image(self):
        """Reconstruit la version export si un resize l'a invalidée."""
        if self._export_dirty and self.original_image:
            self.image_imported_image = self.original_image.resize(self.image_imported_image_size)
            self._export_dirty = False

    def draw_on_image(self, image: Image.Image, export=False):
        """
        Dessine ce calque image sur une image PIL.

        Args:
            image (PIL.Image): image PIL.
            export (bool): True pour l'image export.
        """
        if not self.visible or not self.display_imported_image:
            return
        if export:
            self._ensure_export_image()
            if self.image_imported_image is None:
                return
        to_paste = self.image_imported_image if export else self.display_imported_image
        pos = self.image_position if export else self.display_position
        image.paste(to_paste, (int(pos[0]), int(pos[1])), to_paste)

    def set_position(self, x, y):
        """
        Définit la position du calque (canvas + export synchronisés).

        Args :
            x (int/float) : Abscisse canvas.
            y (int/float) : Ordonnée canvas.
        """
        self.set_display_position(x, y)

    def set_size(self, width, height):
        """
        Redimensionne l'image importée à des dimensions libres
        (sans conservation forcée du ratio).

        Args :
            width (int) : Largeur canvas souhaitée.
            height (int) : Hauteur canvas souhaitée.

        Raises :
            ValueError : si dimensions invalides ou aucune image importée.
        """
        if not self.original_image:
            raise ValueError("Aucune image importée")
        new_w = max(15, int(width))
        new_h = max(10, int(height))
        self.display_imported_image_size = (new_w, new_h)
        self.image_imported_image_size = (new_w * self.RATIO, new_h * self.RATIO)
        self.display_imported_image = self.original_image.resize(self.display_imported_image_size)
        self._export_dirty = True

    def update_param_zone(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

        try:
            title = t('layerimage.label.title', name=self.name)
        except Exception:
            title = f"Calque {self.name}"
        try:
            file_label = t('layerimage.label.file',
                           filename=(basename(self.imported_image_path) if self.imported_image_path else ''))
        except Exception:
            file_label = basename(self.imported_image_path) if self.imported_image_path else ''
        tk.Label(frame, justify="left", text=f"{title}\n{file_label}").pack(anchor='nw')

        try:
            lbl_x = t('layerimage.label.x')
        except Exception:
            lbl_x = 'X :'
        try:
            lbl_y = t('layerimage.label.y')
        except Exception:
            lbl_y = 'Y :'
        try:
            lbl_w = t('layerimage.label.width')
        except Exception:
            lbl_w = 'Largeur :'
        try:
            lbl_h = t('layerimage.label.height')
        except Exception:
            lbl_h = 'Hauteur :'

        geom_frame = tk.Frame(frame)
        geom_frame.pack(anchor='nw', padx=5, pady=5)

        disp_x, disp_y = self.display_position
        disp_w, disp_h = self.display_imported_image_size

        var_x = tk.StringVar(value=str(int(disp_x)))
        var_y = tk.StringVar(value=str(int(disp_y)))
        var_w = tk.StringVar(value=str(int(disp_w)))
        var_h = tk.StringVar(value=str(int(disp_h)))
        # Références pour sync_param_zone() (modif souris → champs).
        self._param_vars = {'x': var_x, 'y': var_y, 'w': var_w, 'h': var_h}

        tk.Label(geom_frame, text=lbl_x).grid(row=0, column=0, sticky='e')
        entry_x = tk.Entry(geom_frame, textvariable=var_x, width=8)
        entry_x.grid(row=0, column=1, padx=2, pady=2)
        tk.Label(geom_frame, text=lbl_y).grid(row=0, column=2, sticky='e')
        entry_y = tk.Entry(geom_frame, textvariable=var_y, width=8)
        entry_y.grid(row=0, column=3, padx=2, pady=2)

        tk.Label(geom_frame, text=lbl_w).grid(row=1, column=0, sticky='e')
        entry_w = tk.Entry(geom_frame, textvariable=var_w, width=8)
        entry_w.grid(row=1, column=1, padx=2, pady=2)
        tk.Label(geom_frame, text=lbl_h).grid(row=1, column=2, sticky='e')
        entry_h = tk.Entry(geom_frame, textvariable=var_h, width=8)
        entry_h.grid(row=1, column=3, padx=2, pady=2)

        def _parse_values():
            """Parse les 4 champs. Lève ValueError si invalide."""
            def _num(var):
                return int(float(var.get().strip().replace(',', '.')))
            return _num(var_x), _num(var_y), _num(var_w), _num(var_h)

        def _enforce_ratio(new_w, new_h):
            """Recalcule toujours la dimension esclave depuis le ratio de
            l'image d'origine. Le champ qui a changé par rapport à la
            taille courante est considéré comme maître."""
            if not self.original_image:
                return new_w, new_h
            w0, h0 = self.original_image.size
            if not h0:
                return new_w, new_h
            aspect = w0 / h0
            cur_w, cur_h = self.display_imported_image_size
            if new_w != cur_w:
                new_h = max(10, int(round(new_w / aspect)))
            elif new_h != cur_h:
                new_w = max(15, int(round(new_h * aspect)))
            return new_w, new_h

        def _show_invalid():
            try:
                messagebox.showerror(t('layerimage.msg.error.invalid_title'),
                                     t('layerimage.msg.error.invalid_message'),
                                     parent=self.tk_parent)
            except Exception:
                messagebox.showerror("Valeur invalide",
                                     "Saisir des nombres entiers pour X, Y, Largeur, Hauteur.",
                                     parent=self.tk_parent)

        def _refresh_canvas():
            if self.parent is not None and hasattr(self.parent, 'update_canvas'):
                try:
                    self.parent.update_canvas()
                except Exception as exc:
                    logger.warning(f"update_canvas après édition dimensions: {exc}")

        def _apply_values(show_errors):
            """Applique les champs vers le calque. Retourne True si appliqué."""
            try:
                new_x, new_y, new_w, new_h = _parse_values()
            except (ValueError, AttributeError):
                if show_errors:
                    _show_invalid()
                return False
            if not self.original_image:
                if show_errors:
                    messagebox.showerror("Erreur", "Aucune image importée",
                                         parent=self.tk_parent)
                return False
            new_w, new_h = _enforce_ratio(new_w, new_h)
            if new_w < 15 or new_h < 10:
                if show_errors:
                    _show_invalid()
                return False
            self.set_position(new_x, new_y)
            try:
                self.set_size(new_w, new_h)
            except ValueError as exc:
                if show_errors:
                    messagebox.showerror("Erreur", str(exc), parent=self.tk_parent)
                return False
            # Repousse la dimension esclave recalculée vers son champ
            # (trace protégée par _syncing).
            self._syncing = True
            try:
                var_w.set(str(new_w))
                var_h.set(str(new_h))
            except Exception:
                pass
            finally:
                self._syncing = False
            _refresh_canvas()
            return True

        def _apply_live(*_args):
            """Mise à jour en direct pendant la frappe (silencieuse : ignore les
            valeurs intermédiaires invalides sans popup)."""
            if self._syncing:
                return
            _apply_values(False)

        def _apply(*_args):
            _apply_values(True)

        # Mise à jour en direct (trace) + validation explicite sur
        # Entrée / sortie de champ. Pas de bouton : le live suffit.
        for entry in (entry_x, entry_y, entry_w, entry_h):
            entry.bind('<Return>', _apply)
            entry.bind('<FocusOut>', _apply)
        for var in (var_x, var_y, var_w, var_h):
            var.trace_add('write', _apply_live)

        # Croix directionnelle (déplacement) + zoom +/- (ratio d'origine).
        pad_frame = tk.Frame(frame)
        pad_frame.pack(anchor='nw', padx=5, pady=5)

        def _nudge(dx, dy):
            if self.locked:
                return
            x, y = self.display_position
            self.set_position(x + dx, y + dy)
            self.sync_param_zone()
            _refresh_canvas()

        def _zoom(step):
            if not self.original_image:
                return
            w0, h0 = self.original_image.size
            aspect = (w0 / h0) if h0 else 1
            cur_w, _cur_h = self.display_imported_image_size
            new_w = max(15, cur_w + step)
            new_h = max(10, int(round(new_w / aspect)))
            try:
                self.set_size(new_w, new_h)
            except ValueError:
                return
            self.sync_param_zone()
            _refresh_canvas()

        _step = 5
        _bw = 2  # boutons carrés compacts (param_frame étroit : 250 px)
        tk.Button(pad_frame, text='▲', width=_bw,
                  command=lambda: _nudge(0, -_step)).grid(row=0, column=1)
        tk.Button(pad_frame, text='◄', width=_bw,
                  command=lambda: _nudge(-_step, 0)).grid(row=1, column=0)
        tk.Button(pad_frame, text='►', width=_bw,
                  command=lambda: _nudge(_step, 0)).grid(row=1, column=2)
        tk.Button(pad_frame, text='▼', width=_bw,
                  command=lambda: _nudge(0, _step)).grid(row=2, column=1)
        tk.Button(pad_frame, text='+', width=_bw,
                  command=lambda: _zoom(10)).grid(row=0, column=3, padx=(6, 0))
        tk.Button(pad_frame, text='-', width=_bw,
                  command=lambda: _zoom(-10)).grid(row=1, column=3, padx=(6, 0))

    def sync_param_zone(self):
        """Repousse position/taille courantes vers les champs d'édition
        (appelé après drag/resize à la souris)."""
        vars = self._param_vars
        if not vars:
            return
        self._syncing = True
        try:
            vars['x'].set(str(int(self.display_position[0])))
            vars['y'].set(str(int(self.display_position[1])))
            vars['w'].set(str(int(self.display_imported_image_size[0])))
            vars['h'].set(str(int(self.display_imported_image_size[1])))
        except Exception:
            pass
        finally:
            self._syncing = False

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
        new_layer._export_dirty = self._export_dirty

        return new_layer

    def to_dict(self):
        """Retourne un dict serializable décrivant l'état du calque."""
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
    def from_dict(dct, tk_parent, parent, canva_size, image_size, ratio, name=None):
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

        Returns:
            LayerImage: un nouveau calque image restauré.
        """
        obj = LayerImage(tk_parent,
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
        obj.display_imported_image_size = tuple(dct.get("display_imported_image_size", (obj.CANVA_W, obj.CANVA_H)))
        obj.image_imported_image_size = tuple(dct.get("image_imported_image_size", (obj.IMAGE_W, obj.IMAGE_H)))

        # Recharge l'image si chemin présent
        if obj.imported_image_path:
            try:
                p = Path(obj.imported_image_path)
                parent_frame_dir = getattr(parent, 'frame_dir', None)
                if p.is_absolute() or not parent_frame_dir:
                    image_path = str(p)
                else:
                    image_path = str(Path(parent_frame_dir) / p.name)

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
