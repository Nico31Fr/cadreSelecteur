# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |-> fenêtre principale de l'IHM  """

import tkinter as tk
from tkinter import messagebox
from tkinter.simpledialog import askstring
from os import path
from json import dump, load
import xml.etree.ElementTree as Et
from shutil import copy, Error
from pathlib import Path
import logging
from enum import Enum, auto

from .imageeditor import ImageEditor
from .layerexcluzone import LayerExcluZone
from .layertext import LayerText
from .layerimage import LayerImage
from CadreSelecteur import __version__
from CadreSelecteur.ttk_theme import apply_clam_theme
from CadreSelecteur.exceptions import FileOperationError
from CadreSelecteur.error_handler import handle_exception
# Import du traducteur
from ..i18n.translator import t

# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Ne pas ajouter de FileHandler local : la configuration centrale (logging_config)
# ajoute déjà un FileHandler vers resources/image_editor.log. Éviter d'ajouter
# un handler relatif ici pour prévenir les fichiers vides quand le cwd diffère.


class ImageEditorApp:
    """
    Image editor avec les deux frames de modif de cadre
        + synchro D/G
        + sauvegarde restore
        + export
    """

    class Mode(Enum):
        NONE = auto()
        EDIT = auto()
        CREATION = auto()


    def __init__(self,
                 root,
                 template="../Templates/",
                 destination='../Cadres/',
                 project=None):

        try:
            # recuperation des paramètres
            self.template = template
            self.destination = destination
            self.frame_name = None
            self.frame_dir = None
            self.mode = self.Mode.NONE

            # Calculer base_dir (répertoire courant)
            self.base_dir = Path.cwd()

            if project is None:
                # Demander le nom du cadre à l'utilisateur

                root.withdraw()  # Masquer la fenêtre principale temporairement

                self.prj_name = askstring(
                    t('editor.dialog.frame_name_title'),
                    t('editor.dialog.frame_name_message')
                )
                root.deiconify()  # Restaurer la fenêtre principale

                if not self.prj_name:
                    # L'utilisateur a annulé le dialogue
                    messagebox.showerror(
                        t('editor.msg.error.frame_name_required_title'),
                        t('editor.msg.error.frame_name_required_message')
                    )
                    raise ValueError("Frame name is required")

                # Créer le répertoire du cadre si nécessaire
                self.frame_dir = Path(self.template) / self.prj_name
                self.mode = self.Mode.CREATION
            else:
                self.frame_dir = Path(project).parent
                self.prj_name = Path(project).stem
                self.mode = self.Mode.EDIT

            # Dimension de la fenêtre
            self.project_file_path = None  # Chemin du fichier projet actuellement ouvert
            self.tk_root = root

            # Apply ttk clam theme
            apply_clam_theme(self.tk_root)

            # Optionnel : Empêcher le redimensionnement de la fenêtre
            self.tk_root.resizable(False, False)
            self.tk_root.title(t('editor.title', version=__version__)+' ( '+self.prj_name+' )')

            # Création de frame parent
            self.main_frame = tk.Frame(self.tk_root)
            self.main_frame.pack(side='top', expand=True, fill='both')

            # configure la grille pour les boutons 4 lignes x 3 colonnes
            self.main_frame.rowconfigure(0)
            self.main_frame.rowconfigure(1)
            self.main_frame.rowconfigure(2)
            self.main_frame.columnconfigure(0)
            self.main_frame.columnconfigure(1)
            self.main_frame.columnconfigure(2)

            # Liste des options pour le menu déroulant
            options = [f.name for f in Path(self.template).glob('template_*.xml')]

            # Gérer le cas où aucun template n'est trouvé
            if not options:
                messagebox.showerror(t('editor.msg.error.no_template_title'),
                                     t('editor.msg.error.no_template_message', path=self.template))
                # Pour éviter un crash ultérieur, ajouter un template fictif
                options = ["template_1.xml"]

            # Variable pour stocker l'option sélectionnée
            self.selected_template = tk.StringVar()
            self.selected_template.set(options[0])  # Définir la valeur par défaut

            # Étiquette pour afficher l'option sélectionnée
            label = tk.Label(self.main_frame, text=t('editor.label.template'))
            label.grid(column=0, row=0, sticky=tk.E, padx=5, pady=5)

            # Créer le menu déroulant
            self.dropdown = tk.OptionMenu(self.main_frame, self.selected_template, *options)
            self.dropdown.grid(column=1, row=0, sticky=tk.W, padx=5, pady=5, columnspan=2)
            # Ajouter un traceur pour appeler la fonction lors du changement d'état
            self.selected_template.trace_add("write", self.on_template_change)

            self.exclusion_zones = self.load_template()

            # App1 frame
            self.app1_frame = tk.Frame(self.main_frame, borderwidth=2, relief='groove')
            self.app1_frame.grid(column=0, row=1, padx=5, pady=5)
            self.app1 = ImageEditor(self.app1_frame,
                                    self.exclusion_zones[0],
                                    base_dir=self.base_dir,
                                    frame_dir=self.frame_dir,
                                    prj_name=self.prj_name)

            # bouton synchronisation droite gauche
            self.arrow_frame = tk.Frame(self.main_frame)
            self.arrow_frame.grid(column=1, row=1, padx=5)
            self.arrow_frame_a = tk.Frame(self.arrow_frame)
            self.arrow_frame_a.grid(column=1, row=0, padx=5, pady=150)
            self.arrow_frame_l = tk.Frame(self.arrow_frame)
            self.arrow_frame_l.grid(column=1, row=1, padx=5, pady=5)
            self.arrow_frame_b = tk.Frame(self.arrow_frame)
            self.arrow_frame_b.grid(column=1, row=2, padx=5, pady=5)

            button_l_all = tk.Button(self.arrow_frame_a, text='->',
                                     command=lambda: self.copy_conf('all', '1_4'))
            button_r_all = tk.Button(self.arrow_frame_a, text='<-',
                                     command=lambda: self.copy_conf('all', '4_1'))
            button_l_all.pack(padx=5, pady=5, anchor='center')
            button_r_all.pack(padx=5, pady=5, anchor='center')
            button_l_layer = tk.Button(self.arrow_frame_l, text='->',
                                       command=lambda: self.copy_conf('layer', '1_4'))
            button_r_layer = tk.Button(self.arrow_frame_l, text='<-',
                                       command=lambda: self.copy_conf('layer', '4_1'))
            button_l_layer.pack(padx=5, pady=5)
            button_r_layer.pack(padx=5, pady=5)
            button_l_back = tk.Button(self.arrow_frame_b, text='->',
                                      command=lambda: self.copy_conf('background', '1_4'))
            button_r_back = tk.Button(self.arrow_frame_b, text='<-',
                                      command=lambda: self.copy_conf('background', '4_1'))
            button_l_back.pack(padx=5, pady=5)
            button_r_back.pack(padx=5, pady=5)

            # App4 frame
            self.app4_frame = tk.Frame(self.main_frame, borderwidth=2, relief='groove')
            self.app4_frame.grid(column=2, row=1, padx=10, pady=10)
            self.app4 = ImageEditor(self.app4_frame,
                                    self.exclusion_zones[1],
                                    base_dir=self.base_dir,
                                    frame_dir=self.frame_dir,
                                    prj_name=self.prj_name)

            # frame load save and export
            self.export_frame = tk.Frame(self.main_frame, borderwidth=2, relief='groove')
            self.export_frame.grid(column=0, row=2, columnspan=3, padx=10, pady=10)

            # configure la grille pour les boutons 4 lignes x 3 colonnes
            self.export_frame.rowconfigure(0, weight=2)
            self.export_frame.rowconfigure(1, weight=1)
            self.export_frame.columnconfigure(0, weight=1)
            self.export_frame.columnconfigure(1, weight=2)
            self.export_frame.columnconfigure(2, weight=2)

            # Bouton sauvegarder
            button_save = tk.Button(self.export_frame,
                                    text=t('editor.button.save'),
                                    command=lambda: self.save_project())
            button_save.grid(column=1, row=0, sticky=tk.EW, padx=5, pady=5)

            if self.mode == self.Mode.EDIT:
                self.load_project()

        except Exception as e:
            handle_exception(e, operation="initialize_editor",
                             log_level='exception')

    # export du set de cadre (2 .png + XML)
    def gen_images(self):
        """
        lance l'enregistrement des deux fichiers
        """
        try:
            # exporte les images avec le nom du projet
            self.app1.save_image()
            self.app4.save_image()
            logger.info(f"Frame images exported to {self.frame_dir}")
        except FileOperationError as e:
            handle_exception(e, operation="export_images", log_level='exception')
            return
        except Exception as e:
            handle_exception(e, operation="export_images", log_level='exception')
            return

        # copie et renomme le XML de template
        try:
            path_to_xml = path.join(self.template, self.selected_template.get())
            dest_xml = self.frame_dir / f"{self.prj_name}.xml"
            copy(path_to_xml, dest_xml)
            logger.info(f"Template XML copied to {dest_xml}")
        except FileNotFoundError as e:
            handle_exception(e, operation="copy_template_xml",
                             context={'source': path_to_xml},
                             log_level='warning')
        except (OSError, Error) as e:
            handle_exception(e, operation="copy_template_xml",
                             context={'source': path_to_xml, 'dest': self.base_dir},
                             log_level='exception')

        # Copier les images utilisées dans les calques
        try:
            for app in [self.app1, self.app4]:
                for layer in app.layers:
                    if hasattr(layer, 'imported_image_path') and layer.imported_image_path:
                        image_path = layer.imported_image_path
                        if self.base_dir and not Path(image_path).is_absolute():
                            image_path = str(Path(self.base_dir) / image_path)
                        if Path(image_path).exists():
                            copy(image_path, self.base_dir)
                            logger.info(f"Image copied to {self.base_dir}")
        except Exception as e:
            handle_exception(e, operation="copy_used_images", log_level='exception')


    def save_project(self):
        """Sauvegarde l'état actuel du projet dans un fichier JSON.

        """

        try:

            file_path = self.project_file_path

            # crée le repêrtoire projet s'il n'existe pas
            if file_path is None:
                project_dir = self.base_dir
                project_dir.mkdir(parents=True, exist_ok=True)
                file_path = project_dir / f"{self.prj_name}.json"
                self.project_file_path = file_path  # sauvegarder le chemin du fichier projet

            app1_layer_tmp = []
            app4_layer_tmp = []

            for layer in self.app1.layers:
                if layer is not None:
                    app1_layer_tmp.append(layer)
            for layer in self.app4.layers:
                if layer is not None:
                    app4_layer_tmp.append(layer)

            project_data = {
                "app1": {
                    "layers": [layer.to_dict() for layer in app1_layer_tmp],
                    "background_couleur": self.app1.background_couleur,
                },
                "app4": {
                    "layers": [layer.to_dict() for layer in app4_layer_tmp],
                    "background_couleur": self.app4.background_couleur,
                },
                "template": self.selected_template.get()
            }

            with open(file_path, 'w', encoding='utf-8') as file:
                dump(project_data, file, indent=2, ensure_ascii=False)  # pretty print
            logger.info(f"Project saved to {file_path}")

        except (OSError, IOError) as e:
            handle_exception(e, operation="save_project",
                             context={'file': file_path},
                             log_level='exception')
            return None
        except (TypeError, ValueError) as e:
            handle_exception(e, operation="serialize_project_data",
                             log_level='exception')
            return None
        except Exception as e:
            handle_exception(e, operation="save_project", log_level='exception')
            return None

        self.gen_images()
        messagebox.showinfo(t('editor.msg.info.save_ok_title'), t('editor.msg.info.save_ok_message'))

    def load_project(self):
        """Charge un projet depuis un fichier JSON."""

        try:
            file_path = self.frame_dir / f"{self.prj_name}.json"

            with open(file_path, 'r', encoding='utf-8') as file:
                project_data = load(file)

            # Clean tous les layers (hors ZoneEx !)
            self.clean_all_layer(1)
            self.clean_all_layer(4)

            # Grammaire des Layer : type => class
            type2class = {
                'Image': LayerImage,
                'Texte': LayerText,
                'ZoneEx': LayerExcluZone
            }
            app_list = [(self.app1, self.app1_frame, 'app1'), (self.app4, self.app4_frame, 'app4')]

            for app, parent, key in app_list:
                for layer_dict in project_data[key]["layers"]:
                    cls = type2class[layer_dict["layer_type"]]
                    layer = cls.from_dict(layer_dict, parent, app,
                                          (app.CANVA_W, app.CANVA_H),
                                          (app.IMAGE_W, app.IMAGE_H),
                                          app.RATIO)
                    try:
                        # utiliser l'API d'ajout pour valider le layer
                        app.add_layer(layer)
                    except Exception:
                        # fallback : append direct (compatibilité)
                        app.layers.append(layer)
                # Restaure couleur de fond
                app.background_couleur = project_data[key].get("background_couleur", "#FFFFFF")

                app.refresh_listbox()
                app.update_canvas()

            # Mise à jour du template sélectionné dans le menu déroulant
            template_name = project_data["template"]
            self.selected_template.set(template_name)

            # Mise à jour du nom du projet
            project_name = Path(file_path).stem  # Extrait le nom du fichier sans extension
            self.prj_name = project_name
            self.project_file_path = file_path  # sauvegarder le chemin du fichier ouvert
            logger.debug(f"Project name updated to: {project_name}")
            logger.debug(f"Project file path set to: {file_path}")

        except (KeyError, ValueError) as e:
            handle_exception(e, operation="parse_project_data",
                             log_level='exception')
        except Exception as e:
            handle_exception(e, operation="load_project", log_level='exception')

    # gestion de la synchro droite gauche
    def copy_conf(self, layer, direction):
        """
        copie la configuration d'une layer vers l'autre

        layer : calque à prendre en compte :
                'background', 'image', 'text' or 'all
        dir : copie de 1 vers 4 ou 4 vers 1 '1_4' or '4_1'
        """
        try:
            if layer == 'layer':
                if direction == '1_4':
                    new_layer = self.app1.layers[self.app1.active_layer_idx].clone(self.app4_frame, self.app4)
                    n = len([layer for layer in self.app4.layers
                             if layer is not None and getattr(layer, 'layer_type', None) == new_layer.layer_type]) + 1
                    new_layer.name = f"{new_layer.layer_type} {n}"
                    try:
                        added = self.app4.add_layer(new_layer)
                        if not added:
                            logger.warning(f"add_layer refused new_layer when copying 1->4: {new_layer}")
                    except Exception as e:
                        logger.warning(f"Exception while adding new_layer to app4: {e}")
                elif direction == '4_1':
                    new_layer = self.app4.layers[self.app4.active_layer_idx].clone(self.app1_frame, self.app1)
                    n = len([layer for layer in self.app1.layers
                             if layer is not None and getattr(layer, 'layer_type', None) == new_layer.layer_type]) + 1
                    new_layer.name = f"{new_layer.layer_type} {n}"
                    try:
                        added = self.app1.add_layer(new_layer)
                        if not added:
                            logger.warning(f"add_layer refused new_layer when copying 4->1: {new_layer}")
                    except Exception as e:
                        logger.warning(f"Exception while adding new_layer to app1: {e}")
                else:
                    raise ValueError(f'Invalid direction: {direction}')
            if layer == 'all':
                if direction == '1_4':
                    self.clean_all_layer(1)
                    for layer_obj in self.app1.layers:
                        if layer_obj is None:
                            continue
                        if layer_obj.layer_type != 'ZoneEx':
                            new_layer = layer_obj.clone(self.app4_frame, self.app4)
                            new_layer.name = layer_obj.name
                            try:
                                added = self.app4.add_layer(new_layer)
                                if not added:
                                    logger.warning(f"add_layer refused new_layer in all-copy 1->4: {new_layer}")
                            except Exception as e:
                                logger.warning(f"Exception while adding new_layer to app4 in all-copy: {e}")
                    self.app4.background_couleur = self.app1.background_couleur
                elif direction == '4_1':
                    self.clean_editable_layer(1)
                    for layer_obj in self.app4.layers:
                        if layer_obj is None:
                            continue
                        if layer_obj.layer_type != 'ZoneEx':
                            new_layer = layer_obj.clone(self.app1_frame, self.app1)
                            new_layer.name = layer_obj.name
                            try:
                                added = self.app1.add_layer(new_layer)
                                if not added:
                                    logger.warning(f"add_layer refused new_layer in all-copy 4->1: {new_layer}")
                            except Exception as e:
                                logger.warning(f"Exception while adding new_layer to app1 in all-copy: {e}")
                    self.app1.background_couleur = self.app4.background_couleur
                else:
                    raise ValueError(f'Invalid direction: {direction}')
            if layer == 'background' or layer == 'all':
                if direction == '1_4':
                    self.app4.background_couleur = self.app1.background_couleur
                elif direction == '4_1':
                    self.app1.background_couleur = self.app4.background_couleur
                else:
                    raise ValueError(f'Invalid direction: {direction}')

            self.app1.refresh_listbox()
            self.app4.refresh_listbox()
            self.app1.update_canvas()
            self.app4.update_canvas()
            logger.debug(f"Configuration synced: layer={layer}, direction={direction}")
        except ValueError as e:
            logger.warning(f"Invalid copy_conf parameters: {e}")
        except Exception as e:
            handle_exception(e, operation="copy_configuration",
                             context={'layer': layer, 'direction': direction},
                             log_level='warning')

    # gestion des templates
    def load_template(self):
        """
        appelé à pour charger le template sélectionné
        charge le xml et met à jour les zones d'exclusion
        """

        try:
            # Charger et analyser le fichier XML
            path_to_xml = path.join(self.template, self.selected_template.get())
            tree = Et.parse(path_to_xml)
            root_xml = tree.getroot()
            new_exc_zone1 = []
            new_exc_zone4 = []

            # Trouver l'élément mxGeometry
            for elem in root_xml.iter():
                if 'diagram' not in elem.tag:
                    continue
                for diagram in elem.iter():
                    if diagram.get('name') == 'Page-5':
                        for item in diagram.iter():
                            if 'mxGeometry' in item.tag:
                                x = float(item.get('x'))
                                y = float(item.get('y'))
                                width = float(item.get('width'))
                                height = float(item.get('height'))
                                new_exc_zone1 = [(x, y, width, height)]
                                break
                    if diagram.get('name') == 'Page-8':
                        number_of_coord = 1
                        for item in diagram.iter():
                            if 'mxGeometry' in item.tag:
                                x = float(item.get('x'))
                                y = float(item.get('y'))
                                width = float(item.get('width'))
                                height = float(item.get('height'))
                                new_exc_zone4.append((x, y, width, height))
                                number_of_coord += 1
                                if number_of_coord >= 5:
                                    break
            return [new_exc_zone1, new_exc_zone4]

        except FileNotFoundError as e:
            logger.debug(f"Template file not found: {path_to_xml} - {e}")
            messagebox.showerror(t('editor.msg.error.file'), t('editor.msg.error.file'))
            return [[], []]
        except Et.ParseError as e:
            handle_exception(e, operation="parse_template_xml",
                             context={'file': path_to_xml},
                             log_level='warning')
            return [[], []]
        except (ValueError, AttributeError) as e:
            handle_exception(e, operation="extract_template_coordinates",
                             log_level='warning')
            return [[], []]
        except Exception as e:
            handle_exception(e, operation="load_default_template", log_level='exception')
            return [[], []]


    # gestion des templates
    def on_template_change(self, *_args):
        """
        appelé lors du changement de template
        charge le xml et met à jour les zones d'exclusion
        """

        new_exc_zone1, new_exc_zone4 = self.load_template()

        self.app1.exclusion_zone = new_exc_zone1
        self.app1.update_zone_exclu_layer(new_exc_zone1)
        self.app4.exclusion_zone = new_exc_zone4
        self.app4.update_zone_exclu_layer(new_exc_zone4)
        self.app1.update_canvas()
        self.app4.update_canvas()
        logger.debug(f"Template changed to {self.selected_template.get()}")


    def clean_all_layer(self, layer_nb) -> None:
        """ efface tous les calques """
        if layer_nb == 1:
            app = self.app1
        elif layer_nb == 4:
            app = self.app4
        else:
            raise ValueError(f"Invalid layer number: {layer_nb}")
        app.active_layer_idx = 0
        app.layers = []


    def clean_editable_layer(self, layer_nb) -> None:
        """ efface tous les calques """
        if layer_nb == 1:
            app = self.app1
        elif layer_nb == 4:
            app = self.app4
        else:
            raise ValueError(f"Invalid layer number: {layer_nb}")

        for i in reversed(range(len(app.layers))):
            layer = app.layers[i]
            if layer.layer_type != 'ZoneEx':
                app.active_layer_idx = i
                app.delete_layer()


if __name__ == "__main__":

    tk_root = tk.Tk()
    ImageEditorApp(tk_root)
    tk_root.mainloop()
