# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |-> fenêtre principale de l'IHM  """

import tkinter as tk
from tkinter import filedialog, messagebox
from os import path
from json import dump, load
import xml.etree.ElementTree as Et
from shutil import copy, Error
from pathlib import Path
import logging

from .imageeditor import ImageEditor
from .layerexcluzone import LayerExcluZone
from .layertext import LayerText
from .layerimage import LayerImage
from CadreSelecteur import __version__
from CadreSelecteur.exceptions import ProjectError, FileOperationError
from CadreSelecteur.error_handler import handle_exception
from CadreSelecteur.validators import Validators, ValidationError
# Import du traducteur
from ..i18n.translator import _t


# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Ne pas ajouter de FileHandler local : la configuration centrale (logging_config)
# ajoute déjà un FileHandler vers resources/image_editor.log. Éviter d'ajouter
# un handler relatif ici pour prévenir les fichiers vides quand le cwd diffère.


def clean_all_layer(app):
    """ efface tous les calques """
    app.active_layer_idx = 0
    app.layers = []


def clean_editable_layer(app):
    """ efface tous les calques """
    for i in reversed(range(len(app.layers))):
        layer = app.layers[i]
        if layer.layer_type != 'ZoneEx':
            app.active_layer_idx = i
            app.delete_layer()


class ImageEditorApp:
    """
    Image editor avec les deux frames de modif de cadre
        + synchro D/G
        + sauvegarde restore
        + export
    """
    def __init__(self,
                 root,
                 template="../Templates/",
                 destination='../Cadres/',
                 standalone=True,
                 project=None):

        try:
            # recuperation des paramètres
            self.template = template
            self.destination = destination
            self.standalone = standalone
            # Dimension de la fenêtre
            self.prj_name = 'cadre_x'
            self.tk_root = root

            # Optionnel : Empêcher le redimensionnement de la fenêtre
            self.tk_root.resizable(False, False)
            self.tk_root.title(_t('editor.title', version=__version__))

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
                messagebox.showerror(_t('editor.msg.error.no_template_title'),
                                     _t('editor.msg.error.no_template_message', path=self.template))
                # Pour éviter un crash ultérieur, ajouter un template fictif
                options = ["template_1.xml"]

            # Variable pour stocker l'option sélectionnée
            self.selected_template = tk.StringVar()
            self.selected_template.set(options[0])  # Définir la valeur par défaut

            # Étiquette pour afficher l'option sélectionnée
            label = tk.Label(self.main_frame, text=_t('editor.label.template'))
            label.grid(column=0, row=0, sticky=tk.E, padx=5, pady=5)

            # Créer le menu déroulant
            self.dropdown = tk.OptionMenu(self.main_frame, self.selected_template, *options)
            self.dropdown.grid(column=1, row=0, sticky=tk.W, padx=5, pady=5, columnspan=2)
            # Ajouter un traceur pour appeler la fonction lors du changement d'état
            self.selected_template.trace_add("write", self.on_template_change)

            self.exclusion_zones = self.load_default_template()

            # App1 frame
            self.app1_frame = tk.Frame(self.main_frame, borderwidth=2, relief='groove')
            self.app1_frame.grid(column=0, row=1, padx=5, pady=5)
            self.app1 = ImageEditor(self.app1_frame, self.exclusion_zones[0])

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
            self.app4 = ImageEditor(self.app4_frame, self.exclusion_zones[1])

            # frame load save and export
            self.export_frame = tk.Frame(self.main_frame, borderwidth=2, relief='groove')
            self.export_frame.grid(column=0, row=2, columnspan=3, padx=10, pady=10)

            # configure la grille pour les boutons 4 lignes x 3 colonnes
            self.export_frame.rowconfigure(0, weight=2)
            self.export_frame.rowconfigure(1, weight=1)
            self.export_frame.columnconfigure(0, weight=1)
            self.export_frame.columnconfigure(1, weight=2)
            self.export_frame.columnconfigure(2, weight=2)

            # charger / sauvegarder le projet
            button_load = tk.Button(self.export_frame, text=_t('editor.button.load'),
                                    command=lambda: self.load_project())
            button_save = tk.Button(self.export_frame, text=_t('editor.button.save'),
                                    command=lambda: self.save_project())
            button_load.grid(column=1, row=0, sticky=tk.EW, padx=5, pady=5)
            button_save.grid(column=2, row=0, sticky=tk.EW, padx=5, pady=5)

            # export / nom du projet
            self.prj_label = tk.Label(self.export_frame,
                                      text=_t('editor.label.template').replace('template : ',
                                                                               'Nom du set de cadre :'))
            self.prj_label.grid(column=0,
                                row=1,
                                sticky=tk.EW,
                                padx=5,
                                pady=5)
            self.prj_name_var = tk.StringVar()
            self.texte_projet_name = tk.Entry(self.export_frame, textvariable=self.prj_name_var)
            self.texte_projet_name.insert(0, self.prj_name)
            self.texte_projet_name.grid(column=1, row=1, sticky=tk.EW, padx=5, pady=5)
            # export / Bouton pour générer les cadres
            button_export = tk.Button(self.export_frame,
                                      text=_t('editor.button.generate'),
                                      command=lambda: self.gen_images(self.app1, self.app4))
            button_export.grid(column=2, row=1, sticky=tk.EW, padx=5, pady=5)

            if project:
                self.load_project(project)

        except Exception as e:
            handle_exception(e, operation="initialize_editor",
                           log_level='exception')

    # export du set de cadre (2 .png + XML)
    def gen_images(self, app_1, app_4):
        """
        lance l'enregistrement des deux fichiers
        """
        try:
            path_im = self.select_directory()
            if path_im is not None:
                # exporte les images
                app_1.save_image(path_im)
                app_4.save_image(path_im)
                logger.info(f"Frame images exported to {path_im}")
        except FileOperationError as e:
            handle_exception(e, operation="export_images", log_level='exception')
            return
        except Exception as e:
            handle_exception(e, operation="export_images", log_level='exception')
            return

        # copie et renomme le XML de template
        try:
            path_to_xml = path.join(self.template, self.selected_template.get())
            dest_xml = path_im + '.xml'
            copy(path_to_xml, dest_xml)
            logger.info(f"Template XML copied to {dest_xml}")
            messagebox.showinfo(_t('editor.msg.info.export_ok_title'), _t('editor.msg.info.export_ok_message'))
        except FileNotFoundError as e:
            handle_exception(e, operation="copy_template_xml",
                           context={'source': path_to_xml},
                           log_level='warning')
        except (OSError, Error) as e:
            handle_exception(e, operation="copy_template_xml",
                           context={'source': path_to_xml, 'dest': dest_xml},
                           log_level='exception')

    def select_directory(self):
        """
        sélectionne le repertoire de sortie
        et construction du path de sortie avec le nom du projet
        """
        try:
            tmp_prj_name = self.prj_name_var.get()
            if tmp_prj_name == "":
                messagebox.showerror(title=_t('editor.msg.error.no_project_name_title'),
                                     message=_t('editor.msg.error.no_project_name_message'))
                return None

            # Valider le nom du projet (prévention chemin traversal)
            try:
                tmp_prj_name = Validators.validate_project_name(tmp_prj_name)
            except ValidationError as e:
                messagebox.showerror(title=_t('editor.msg.error.no_project_name_title'),
                                   message=f"Nom de projet invalide: {str(e)}")
                return None

            if self.standalone:
                # Ouvre la boîte de dialogue pour la sélection du répertoire
                selected_dir = filedialog.askdirectory()
            else:
                selected_dir = self.template

            path_prj_name = path.join(selected_dir, tmp_prj_name)

            if selected_dir:  # Vérifie si l'utilisateur à sélectionner un répertoire
                return path_prj_name
            else:
                messagebox.showerror(title=_t('editor.msg.error.no_dir_title'),
                                     message=_t('editor.msg.error.no_dir_message'))
                return None
        except tk.TclError as e:
            handle_exception(e, operation="select_directory", log_level='warning')
            return None
        except Exception as e:
            handle_exception(e, operation="select_directory", log_level='exception')
            return None

    # section pour la sauvegarde recharge d'un projet
    def save_project(self):
        """Sauvegarde l'état actuel du projet dans un fichier JSON."""
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if not file_path:
                return
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
            messagebox.showinfo(_t('editor.msg.info.save_ok_title'), _t('editor.msg.info.save_ok_message'))

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

    def load_project(self, project=None):
        """Charge un projet depuis un fichier JSON."""

        try:
            if project:
                file_path = project
            else:
                file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])

            if not file_path:
                return

            with open(file_path, 'r', encoding='utf-8') as file:
                project_data = load(file)

            # Clean tous les layers (hors ZoneEx !)
            clean_all_layer(self.app1)
            clean_all_layer(self.app4)

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

            logger.info(f"Project loaded from {file_path}")
            messagebox.showinfo(_t('editor.msg.info.load_ok_title'), _t('editor.msg.info.load_ok_message'))

        except FileNotFoundError as e:
            handle_exception(e, operation="load_project",
                           context={'file': file_path},
                           log_level='warning')
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
                    clean_editable_layer(self.app4)
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
                    clean_editable_layer(self.app1)
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
    def load_default_template(self):
        """
        appelé à l'initialisation pour charger le template par défaut
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
            logger.debug(f"Template file not found: {path_to_xml}")
            messagebox.showerror(_t('editor.msg.error.file'), _t('editor.msg.error.file'))
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

            self.app1.exclusion_zone = new_exc_zone1
            self.app1.update_zone_exclu_layer(new_exc_zone1)
            self.app4.exclusion_zone = new_exc_zone4
            self.app4.update_zone_exclu_layer(new_exc_zone4)
            self.app1.update_canvas()
            self.app4.update_canvas()
            logger.debug(f"Template changed to {self.selected_template.get()}")
        except FileNotFoundError as e:
            logger.debug(f"Template file not found: {path_to_xml}")
        except Et.ParseError as e:
            handle_exception(e, operation="parse_template_xml_on_change",
                           context={'file': path_to_xml},
                           log_level='warning')
        except (ValueError, AttributeError) as e:
            handle_exception(e, operation="extract_template_coordinates_on_change",
                           log_level='warning')
        except Exception as e:
            handle_exception(e, operation="on_template_change", log_level='warning')


if __name__ == "__main__":

    tk_root = tk.Tk()
    ImageEditorApp(tk_root)
    tk_root.mainloop()
