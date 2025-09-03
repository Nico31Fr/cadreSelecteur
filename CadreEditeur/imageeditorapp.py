# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |-> fenêtre principale de l'IHM  """

import tkinter as tk
from tkinter import filedialog, messagebox
from os import path
from json import dump, load
import xml.etree.ElementTree as Et
from shutil import copy, Error

from .imageeditor import ImageEditor
from .layerexcluzone import LayerExcluZone
from .layertext import LayerText
from .layerimage import LayerImage

def clean_all_layer(app):
    """ efface tous les calques """
    app.active_layer_idx = 0
    app.layers = []

def clean_editable_layer(app):
    """ efface tous les calques """
    for i in reversed(range(len(app.layers))):
        l = app.layers[i]
        if l.layer_type != 'ZoneEx':
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
                 resources='../resources/',
                 standalone=True):

        try:
            # recuperation des paramètres
            self.template = template
            self.destination = destination
            self.resources = resources
            self.standalone = standalone
            # Dimension de la fenêtre
            self.WINDOWS = "1400x750"
            self.prj_name = 'cadre_xxx'
            self.tk_root = root

            # Fixer la taille de la fenêtre
            self.tk_root.geometry(self.WINDOWS)  # Largeur = 700 pixels, Hauteur = 1200 pixels
            # Optionnel : Empêcher le redimensionnement de la fenêtre
            self.tk_root.resizable(False, False)
            self.tk_root.title("Créateur de cadre V0.1")

            # Création de frame parent
            self.main_frame = tk.Frame(self.tk_root)
            self.main_frame.pack(side='top', expand=True, fill='both')

            # configure la grille pour les boutons 4 lignes x 3 colonnes
            self.main_frame.rowconfigure(0, weight=2)
            self.main_frame.rowconfigure(1, weight=1)
            self.main_frame.rowconfigure(2, weight=1)
            self.main_frame.columnconfigure(0, weight=2)
            self.main_frame.columnconfigure(1, weight=2)
            self.main_frame.columnconfigure(2, weight=1)

            # Liste des options pour le menu déroulant
            options = ["template_std.xml", "cadre-mariage1.xml"]

            # Variable pour stocker l'option sélectionnée
            self.selected_template = tk.StringVar()
            self.selected_template.set(options[0])  # Définir la valeur par défaut

            # Étiquette pour afficher l'option sélectionnée
            label = tk.Label(self.main_frame, text="template : ")
            label.grid(column=0, row=0, sticky=tk.E, padx=5, pady=5)

            # Créer le menu déroulant
            self.dropdown = tk.OptionMenu(self.main_frame, self.selected_template, *options)
            self.dropdown.grid(column=1, row=0, sticky=tk.W, padx=5, pady=5, columnspan=2)
            # Ajouter un traceur pour appeler la fonction lors du changement d'état
            self.selected_template.trace_add("write", self.on_template_change)

            self.exclusion_zones = self.load_default_template()

            # App1 frame
            self.app1_frame = tk.Frame(self.main_frame, borderwidth=2, relief='groove')
            self.app1_frame.grid(column=0, row=1, sticky=tk.EW, padx=5, pady=5)
            self.app1 = ImageEditor(self.app1_frame, self.exclusion_zones[0], self.resources)

            # bouton synchronisation droite gauche
            button_l = tk.Button(self.main_frame, text='->', command=lambda: self.copy_conf('layer', '1_4'))
            button_r = tk.Button(self.main_frame, text='<-', command=lambda: self.copy_conf('layer', '4_1'))
            button_l.grid(column=1, row=1, sticky=tk.SE, padx=5, pady=150)
            button_r.grid(column=1, row=1, sticky=tk.SW, padx=5, pady=150)
            button_l = tk.Button(self.main_frame, text='->', command=lambda: self.copy_conf('background', '1_4'))
            button_r = tk.Button(self.main_frame, text='<-', command=lambda: self.copy_conf('background', '4_1'))
            button_l.grid(column=1, row=1, sticky=tk.SE, padx=5, pady=40)
            button_r.grid(column=1, row=1, sticky=tk.SW, padx=5, pady=40)
            button_l = tk.Button(self.main_frame, text='->', command=lambda: self.copy_conf('all', '1_4'))
            button_r = tk.Button(self.main_frame, text='<-', command=lambda: self.copy_conf('all', '4_1'))
            button_l.grid(column=1, row=1, sticky=tk.NE, padx=5, pady=200)
            button_r.grid(column=1, row=1, sticky=tk.NW, padx=5, pady=200)

            # App4 frame
            self.app4_frame = tk.Frame(self.main_frame, borderwidth=2, relief='groove')
            self.app4_frame.grid(column=2, row=1, sticky=tk.EW, padx=10, pady=10)
            self.app4 = ImageEditor(self.app4_frame, self.exclusion_zones[1], self.resources)

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
            button_load = tk.Button(self.export_frame, text='charger', command=lambda: self.load_project())
            button_save = tk.Button(self.export_frame, text='Sauvegarder', command=lambda: self.save_project())
            button_load.grid(column=1, row=0, sticky=tk.EW, padx=5, pady=5)
            button_save.grid(column=2, row=0, sticky=tk.EW, padx=5, pady=5)

            # export / nom du projet
            tk.Label(self.export_frame, text="Nom du set de cadre :").grid(column=0,
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
                                      text="Générer les cadres",
                                      command=lambda: self.gen_images(self.app1, self.app4))
            button_export.grid(column=2, row=1, sticky=tk.EW, padx=5, pady=5)
        except Exception as e:
            messagebox.showerror("Erreur Initialization", f"Une erreur inattendue s'est produite : {str(e)}")

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
                # copie et renomme le XML de template
                path_to_xml = path.join(self.template, self.selected_template.get())
                dest_xml = path_im + '.xml'
                copy(path_to_xml, dest_xml)
                messagebox.showinfo("export réussie", "Les fichiers on été générés avec succès.")
        except (FileNotFoundError, IsADirectoryError):
            messagebox.showerror("Erreur de fichier", "Impossible de générer les fichiers.")
        except Error as e:
            messagebox.showerror("Erreur de copie", f"Une erreur est survenue lors de la copie du XML : {str(e)}")

    def select_directory(self):
        """
        sélectionne le repertoire de sortie
        et construction du path de sortie avec le nom du projet
        """
        try:
            tmp_prj_name = self.prj_name_var.get()
            if tmp_prj_name == "":
                messagebox.showerror(title='erreur nom du projet',
                                     message="saisir le nom du projet")
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
                messagebox.showerror(title='erreur repertoire',
                                     message="selectionner un repertoire de sortie")
                return None
        except Exception as e:
            messagebox.showerror("Erreur de sélection", f"Une erreur inattendue s'est produite : {str(e)}")
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
                app1_layer_tmp.append(layer)
            for layer in self.app4.layers:
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
            messagebox.showinfo("Sauvegarde réussie", "Le projet a été sauvegardé avec succès.")

        except Exception as e:
            messagebox.showerror("Erreur de sauvegarde", f"Une erreur inattendue s'est produite : {str(e)}")

    def load_project(self):
        """Charge un projet depuis un fichier JSON."""

        try:
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
                    app.layers.append(layer)
                # Restaure couleur de fond
                app.background_couleur = project_data[key].get("background_couleur", "#FFFFFF")

                app.refresh_listbox()
                app.update_canvas()

            # Mise à jour du template sélectionné dans le menu déroulant
            template_name = project_data["template"]
            self.selected_template.set(template_name)

            messagebox.showinfo("Chargement réussi", "Le projet a été chargé avec succès.")

        except Exception as e:
            messagebox.showerror(
                "Erreur de chargement",
                f"Une erreur inattendue s'est produite : {str(e)}"
            )

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
                    n = len([l for l in self.app4.layers if l.layer_type == new_layer.layer_type]) + 1
                    new_layer.name = f"{new_layer.layer_type} {n}"
                    self.app4.layers.append(new_layer)
                elif direction == '4_1':
                    new_layer = self.app4.layers[self.app4.active_layer_idx].clone(self.app1_frame, self.app1)
                    n = len([l for l in self.app1.layers if l.layer_type == new_layer.layer_type]) + 1
                    new_layer.name = f"{new_layer.layer_type} {n}"
                    self.app1.layers.append(new_layer)
                else:
                    raise ValueError(f'ERROR: {direction} is not a valid DIR')
            if layer == 'all':
                if direction == '1_4':
                    clean_editable_layer(self.app4)
                    # copie tou les calques editable
                    for l in self.app1.layers:
                        if l.layer_type != 'ZoneEx':
                            new_layer = l.clone(self.app4_frame, self.app4)
                            new_layer.name = l.name
                            self.app4.layers.append(new_layer)
                elif direction == '4_1':
                    #efface tous les calques editable
                    clean_editable_layer(self.app1)
                    # copie tou les calques
                    for l in self.app4.layers:
                        if l.layer_type != 'ZoneEx':
                            new_layer = l.clone(self.app1_frame, self.app1)
                            new_layer.name = l.name
                            self.app1.layers.append(new_layer)
                else:
                    raise ValueError(f'ERROR: {direction} is not a valid DIR')
            if layer == 'background' or layer == 'all':
                if direction == '1_4':
                    self.app4.background_couleur = self.app1.background_couleur
                elif direction == '4_1':
                    self.app1.background_couleur = self.app4.background_couleur
                else:
                    raise ValueError(f'ERROR: {direction} is not a valid DIR')

            self.app1.refresh_listbox()
            self.app4.refresh_listbox()
            self.app1.update_canvas()
            self.app4.update_canvas()
        except ValueError as e:
            messagebox.showerror("Erreur de direction",
                                 f"Une erreur s'est produite lors de la copie des couches : {str(e)}")

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

        except (FileNotFoundError, IsADirectoryError):
            messagebox.showerror("Erreur de fichier", "Le fichier XML spécifié est introuvable.")
        except Et.ParseError:
            messagebox.showerror("Erreur de XML", "Le fichier XML est corrompu ou non valide.")
        except Exception as e:
            messagebox.showerror("Erreur de template", f"Une erreur inattendue s'est produite : {str(e)}")

    # gestion des templates
    def on_template_change(self, *args):
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
        except (FileNotFoundError, IsADirectoryError):
            messagebox.showerror("Erreur de fichier", "Le fichier XML spécifié est introuvable.")
        except Et.ParseError:
            messagebox.showerror("Erreur de XML", "Le fichier XML est corrompu ou non valide.")
        except Exception as e:
            messagebox.showerror("Erreur de template", f"Une erreur inattendue s'est produite : {str(e)}")


if __name__ == "__main__":

    tk_root = tk.Tk()
    ImageEditorApp(tk_root)
    tk_root.mainloop()
