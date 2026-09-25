# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |→ classe de gestion des calques texte  """

from PIL import ImageFont, ImageDraw, Image
import tkinter as tk
from tkinter import messagebox, colorchooser
from os import path, listdir
import logging
from pathlib import Path

from .layer import Layer
from .text import ask_font
from ..path_resolver import resolve_file_in_package
# Import du traducteur
from ..i18n import t

logger = logging.getLogger(__name__)


class LayerText(Layer):
    """
    Calque texte éditable, positionable, redimensionnable.
    """

    MIN_FONT_SIZE = 4
    MAX_FONT_SIZE = 200  # borne haute : au-delà, PIL alloue des bitmaps
    # géants → freeze + cascade de popups d'erreur à chaque refresh.

    def __init__(self, tk_parent, parent, canva_size, image_size, ratio, name="Text", base_dir=None):
        """
        Args:
            parent (object): widget parent Tkinter.
            canva_size, image_size, ratio : cf. Layer.
            name (str): nom du calque.
            base_dir (str or Path): Répertoire de base pour les chemins relatifs (optionnel).
        """
        super().__init__(name, canva_size, image_size, ratio)
        self.tk_parent = tk_parent
        self.parent = parent
        self.base_dir = base_dir
        self.layer_type = 'Texte'

        # Variables texte
        try:
            default_text = t('layertext.default_text')
        except Exception:
            default_text = 'Texte'
        self.text = tk.StringVar(value=default_text)
        self.text.trace_add("write", self.on_text_change)
        self.font_color = '#000000'
        self.sel_font = {'family': "arial", 'size': 32}

        # Répertoire Fonts (utiliser path_resolver centralisé)
        fonts_dir = resolve_file_in_package('Fonts')
        self.fonts_dir = str(fonts_dir)

        # Police par défaut
        default_font = self.find_font_path(self.sel_font['family'])
        if not default_font:
            default_font = fonts_dir / "Anton-Regular.ttf"
        self.font_name = str(default_font)
        self.pil_font = None
        self.pil_font_export = None
        self._rebuild_fonts()

        self.txt_start_drag_pos = None

    def set_text(self, value):
        """Modifie le texte du calque.
        Assure que l'on met à jour le StringVar au lieu d'écraser l'attribut.
        """
        self.text.set(value)


    @staticmethod
    def clamp_font_size(size):
        """Borne une taille de police dans [MIN_FONT_SIZE, MAX_FONT_SIZE]."""
        try:
            size = int(size)
        except (TypeError, ValueError):
            return LayerText.MIN_FONT_SIZE
        return min(LayerText.MAX_FONT_SIZE, max(LayerText.MIN_FONT_SIZE, size))

    def _rebuild_fonts(self):
        """Reconstruit les fontes cachées (affichage + export) depuis
        font_name / sel_font. Évite de relire le fichier TTF à chaque
        redraw (molette, drag, frappe)."""
        size = self.clamp_font_size(self.sel_font['size'])
        self.sel_font['size'] = size
        self.pil_font = ImageFont.truetype(str(self.font_name), size)
        self.pil_font_export = ImageFont.truetype(str(self.font_name), size * self.RATIO)

    def resize_font(self, delta):
        """Redimensionne la police utilisée dans le calque."""
        self.sel_font['size'] = self.clamp_font_size(self.sel_font['size'] + delta)
        self._rebuild_fonts()

    def set_position(self, x, y):
        """
        Définit la position du calque texte (canvas + export synchronisés).

        Args :
            x (int/float) : Abscisse canvas.
            y (int/float) : Ordonnée canvas.
        """
        self.set_display_position(x, y)

    def set_font_size(self, size):
        """Définit la taille de police absolue (canvas), bornée."""
        self.sel_font['size'] = self.clamp_font_size(size)
        self._rebuild_fonts()

    def draw_on_image(self, image: Image.Image, export=False):
        """Dessine le texte sur l’image PIL, à la position courante."""
        if not self.visible or not self.text:
            return
        pos = self.image_position if export else self.display_position
        # Fontes cachées (jamais de taille aberrante : bornées à la saisie).
        font = self.pil_font_export if export else self.pil_font
        if font is None:
            self._rebuild_fonts()
            font = self.pil_font_export if export else self.pil_font
        draw = ImageDraw.Draw(image)
        draw.text(pos, self.text.get(), fill=self.font_color, font=font)

    def update_param_zone(self, frame):
        """Met à jour la zone de paramètres du panneau latéral."""
        for widget in frame.winfo_children():
            widget.destroy()

        tk.Label(frame, text=t('layertext.label.layer', name=self.name)).pack(anchor='nw')
        tk.Entry(frame,
                 textvariable=self.text, width=40).pack(padx=5, pady=5, anchor='nw')
        btn_row = tk.Frame(frame)
        btn_row.pack(anchor='nw', padx=5, pady=5)
        tk.Button(btn_row,
                  text=t('layertext.button.color'),
                  command=lambda: self.choisir_couleur()).pack(side='left', padx=(0, 5))
        tk.Button(btn_row,
                  text=t('layertext.button.font'),
                  command=self.callback_font).pack(side='left')

        try:
            lbl_x = t('layertext.label.x')
        except Exception:
            lbl_x = 'X :'
        try:
            lbl_y = t('layertext.label.y')
        except Exception:
            lbl_y = 'Y :'
        try:
            lbl_size = t('layertext.label.font_size')
        except Exception:
            lbl_size = 'Taille :'

        geom_frame = tk.Frame(frame)
        geom_frame.pack(anchor='nw', padx=5, pady=5)

        disp_x, disp_y = self.display_position
        var_x = tk.StringVar(value=str(int(disp_x)))
        var_y = tk.StringVar(value=str(int(disp_y)))
        var_size = tk.StringVar(value=str(int(self.sel_font['size'])))
        # Références pour sync_param_zone() (modif souris → champs).
        self._param_vars = {'x': var_x, 'y': var_y, 'size': var_size}

        tk.Label(geom_frame, text=lbl_x).grid(row=0, column=0, sticky='e')
        entry_x = tk.Entry(geom_frame, textvariable=var_x, width=8)
        entry_x.grid(row=0, column=1, padx=2, pady=2)
        tk.Label(geom_frame, text=lbl_y).grid(row=0, column=2, sticky='e')
        entry_y = tk.Entry(geom_frame, textvariable=var_y, width=8)
        entry_y.grid(row=0, column=3, padx=2, pady=2)
        tk.Label(geom_frame, text=lbl_size).grid(row=1, column=0, sticky='e')
        entry_size = tk.Entry(geom_frame, textvariable=var_size, width=8)
        entry_size.grid(row=1, column=1, padx=2, pady=2)

        def _parse_values():
            """Parse les 3 champs. Lève ValueError si invalide."""
            def _num(var):
                return int(float(var.get().strip().replace(',', '.')))
            return _num(var_x), _num(var_y), _num(var_size)

        def _refresh_canvas():
            if self.parent is not None and hasattr(self.parent, 'update_canvas'):
                try:
                    self.parent.update_canvas()
                except Exception as exc:
                    logger.warning(f"update_canvas après édition texte: {exc}")

        def _push_clamped_size(new_size):
            """Repousse la taille bornée vers le champ (trace protégée)."""
            self._syncing = True
            try:
                var_size.set(str(new_size))
            except Exception:
                pass
            finally:
                self._syncing = False

        def _apply_live(*_args):
            """Mise à jour en direct pendant la frappe (silencieuse, bornée)."""
            if self._syncing:
                return
            try:
                new_x, new_y, new_size = _parse_values()
            except (ValueError, AttributeError):
                return
            new_size = self.clamp_font_size(new_size)
            self.set_position(new_x, new_y)
            try:
                self.set_font_size(new_size)
            except Exception:
                return
            _push_clamped_size(new_size)
            _refresh_canvas()

        def _apply(*_args):
            try:
                new_x, new_y, new_size = _parse_values()
            except (ValueError, AttributeError):
                messagebox.showerror("Valeur invalide",
                                     "Saisir des nombres entiers pour X, Y et Taille.",
                                     parent=self.tk_parent)
                return
            # Bornage silencieux (pas de popup) : la valeur est ramenée
            # dans [MIN, MAX] et réaffichée telle qu'appliquée.
            new_size = self.clamp_font_size(new_size)
            self.set_position(new_x, new_y)
            try:
                self.set_font_size(new_size)
            except Exception as exc:
                messagebox.showerror("Erreur", str(exc), parent=self.tk_parent)
                return
            _push_clamped_size(new_size)
            _refresh_canvas()

        # Mise à jour en direct (trace) + validation explicite sur
        # Entrée / sortie de champ. Pas de bouton : le live suffit.
        for entry in (entry_x, entry_y, entry_size):
            entry.bind('<Return>', _apply)
            entry.bind('<FocusOut>', _apply)
        for var in (var_x, var_y, var_size):
            var.trace_add('write', _apply_live)

        # Croix directionnelle (déplacement) + taille police +/-.
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
            try:
                self.set_font_size(self.sel_font['size'] + step)
            except Exception:
                return
            self.sync_param_zone()
            _refresh_canvas()

        _step = 5
        _bw = 2  # boutons carrés compacts (param_frame étroit : 250 px)
        tk.Button(pad_frame, text='˄', width=_bw,
                  command=lambda: _nudge(0, -_step)).grid(row=0, column=1)
        tk.Button(pad_frame, text='˂', width=_bw,
                  command=lambda: _nudge(-_step, 0)).grid(row=1, column=0)
        tk.Button(pad_frame, text='˃', width=_bw,
                  command=lambda: _nudge(_step, 0)).grid(row=1, column=2)
        tk.Button(pad_frame, text='˅', width=_bw,
                  command=lambda: _nudge(0, _step)).grid(row=2, column=1)
        tk.Button(pad_frame, text='+', width=_bw,
                  command=lambda: _zoom(2)).grid(row=0, column=3, padx=(6, 0))
        tk.Button(pad_frame, text='-', width=_bw,
                  command=lambda: _zoom(-2)).grid(row=1, column=3, padx=(6, 0))

    def sync_param_zone(self):
        """Repousse position/taille de police courantes vers les champs
        d'édition (appelé après drag/resize à la souris)."""
        vars = self._param_vars
        if not vars:
            return
        self._syncing = True
        try:
            vars['x'].set(str(int(self.display_position[0])))
            vars['y'].set(str(int(self.display_position[1])))
            vars['size'].set(str(int(self.sel_font['size'])))
        except Exception:
            pass
        finally:
            self._syncing = False

    def callback_font(self):
        """
        Lorsque le bouton Police est cliqué :
        ouvre la fenêtre ask_font() et charge la police sélectionnée
        depuis le répertoire Fonts/.
        """
        try:
            font_selected = ask_font(self.tk_parent,
                                     text=self.text.get(),
                                     title=t('layertext.msg.fontchooser.title'),
                                     family=self.sel_font['family'],
                                     size=self.sel_font['size'])

            if font_selected:
                self.sel_font = font_selected
                # Borne la taille choisie (le sélecteur permet de grandes valeurs).
                self.sel_font['size'] = self.clamp_font_size(self.sel_font.get('size', 32))
                family = self.sel_font['family']

                # Recherche dans le dossier Fonts
                font_name_found = self.find_font_path(family)
                if font_name_found:
                    self.font_name = font_name_found
                else:
                    messagebox.showwarning(t('layertext.msg.warn.font_not_found_title'),
                                           t('layertext.msg.warn.font_not_found_message', family=family))
                    self.font_name = str(resolve_file_in_package('Fonts') / "Anton-Regular.ttf")
                self._rebuild_fonts()

            self.parent.update_canvas()

        except Exception as e:
            messagebox.showerror("Erreur de font", f"Exception inattendue : {str(e)}")

    def find_font_path(self, font_name_to_find):
        """
        Trouve le chemin de la police dans le dossier Fonts.
        Renvoie le chemin complet si trouvé, sinon None.
        """
        try:
            if not path.isdir(self.fonts_dir):
                print(f"[AVERTISSEMENT] Dossier Fonts introuvable : {self.fonts_dir}")
                return None

            for file in listdir(str(self.fonts_dir)):
                if not file.lower().endswith(".ttf"):
                    continue
                name_no_ext = path.splitext(file)[0]
                # Correspondance tolérante : ignore les espaces / majuscules
                if name_no_ext.lower().replace(" ", "") == font_name_to_find.lower().replace(" ", ""):
                    return path.join(str(self.fonts_dir), file)

            return None

        except Exception as e:
            messagebox.showerror("Erreur de police", f"Exception inattendue: {str(e)}")
            return None

    def choisir_couleur(self):
        """Ouvre une boîte de dialogue de sélection de couleur."""
        try:
            couleur = colorchooser.askcolor(title=t('image.colorchooser.title'))
            # couleur peut être (None, None) si annulation => vérifier
            if couleur and couleur[1]:
                self.font_color = couleur[1]
                self.parent.update_canvas()
        except Exception as e:
            messagebox.showerror(t('image.msg.error.color'), f"Exception inattendue : {str(e)}")

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
            name=self.name + "_copie",
            base_dir=self.base_dir
        )
        new_layer.display_position = tuple(self.display_position)
        new_layer.image_position = tuple(self.image_position)
        new_layer.visible = self.visible
        new_layer.locked = self.locked
        new_layer.text.set(self.text.get())
        new_layer.font_color = self.font_color
        new_layer.sel_font = self.sel_font.copy()
        new_layer.font_name = self.font_name
        new_layer._rebuild_fonts()
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
            "font_name": Path(self.font_name).name,
        }

    @staticmethod
    def from_dict(dct, tk_parent, parent, canva_size, image_size, ratio, name=None, base_dir=None, frame_dir=None):
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
            base_dir (str or Path): Répertoire de base pour les chemins relatifs (optionnel).
            frame_dir (str or Path): Répertoire du cadre (non utilisé pour texte, pour compatibilité).

        Returns:
            LayerText: un nouveau calque texte restauré.
        """
        default_name = dct.get("name") or name
        if not default_name:
            try:
                default_name = t('layertext.default_name').replace('{n}', '')
            except Exception:
                default_name = name or 'Texte'

        obj = LayerText(
            tk_parent,
            parent,
            canva_size,
            image_size,
            ratio,
            name=default_name,
            base_dir=base_dir
        )
        obj.display_position = tuple(dct.get("display_position", (0, 0)))
        obj.image_position = tuple(dct.get("image_position", (0, 0)))
        obj.visible = dct.get("visible", True)
        obj.locked = dct.get("locked", False)
        try:
            fallback_text = t('layertext.default_text')
        except Exception:
            fallback_text = 'Texte'
        obj.text.set(dct.get("text", fallback_text))
        obj.font_color = dct.get("font_color", "#000000")
        obj.sel_font = dict(dct.get("sel_font", {"family": "arial", "size": 32}))
        # Désinfecte la taille chargée (un JSON avec une taille énorme
        # ferait exploser le rendu à chaque update_canvas).
        obj.sel_font['size'] = obj.clamp_font_size(obj.sel_font.get('size', 32))

        saved_font_filename = dct.get("font_name", "")
        if saved_font_filename:
            candidate = Path(obj.fonts_dir) / saved_font_filename
            if candidate.exists():
                obj.font_name = str(candidate)
            else:
                # fichier renommé ou absent : retenter via la famille
                obj.font_name = (obj.find_font_path(obj.sel_font['family']) or
                                 str(resolve_file_in_package('Fonts') / "Anton-Regular.ttf"))
        else:
            obj.font_name = (obj.find_font_path(obj.sel_font['family']) or
                             str(resolve_file_in_package('Fonts') / "Anton-Regular.ttf"))

        obj._rebuild_fonts()
        return obj
