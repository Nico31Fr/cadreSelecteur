# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |-> fenêtre principale de l'IHM  """

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, UnidentifiedImageError
from os import path
from json import dump, load, JSONDecodeError
import xml.etree.ElementTree as Et
from shutil import copy, Error

from imageeditor import ImageEditor


class ImageEditorApp:
    """
    Image editor avec les deux frames de modif de cadre
        + synchro D/G
        + sauvegarde restore
        + export
    """
    def __init__(self, root, exclusion_zones):

        try:
            # Dimension de la fenêtre
            self.WINDOWS = "1400x650"
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
            dropdown = tk.OptionMenu(self.main_frame, self.selected_template, *options)
            dropdown.grid(column=1, row=0, sticky=tk.W, padx=5, pady=5, columnspan=2)
            # Ajouter un traceur pour appeler la fonction lors du changement d'état
            self.selected_template.trace_add("write", self.on_template_change)

            # App1 frame
            self.app1_frame = tk.Frame(self.main_frame, borderwidth=2, relief='groove')
            self.app1_frame.grid(column=0, row=1, sticky=tk.EW, padx=5, pady=5)
            self.app1 = ImageEditor(self.app1_frame, exclusion_zones[0])

            # bouton synchronisation droite gauche
            button_load = tk.Button(self.main_frame, text='->', command=lambda: self.copy_conf('background', '1_4'))
            button_save = tk.Button(self.main_frame, text='<-', command=lambda: self.copy_conf('background', '4_1'))
            button_load.grid(column=1, row=1, sticky=tk.SE, padx=5, pady=10)
            button_save.grid(column=1, row=1, sticky=tk.SW, padx=5, pady=10)
            button_load = tk.Button(self.main_frame, text='->', command=lambda: self.copy_conf('image', '1_4'))
            button_save = tk.Button(self.main_frame, text='<-', command=lambda: self.copy_conf('image', '4_1'))
            button_load.grid(column=1, row=1, sticky=tk.SE, padx=5, pady=40)
            button_save.grid(column=1, row=1, sticky=tk.SW, padx=5, pady=40)
            button_load = tk.Button(self.main_frame, text='->', command=lambda: self.copy_conf('text', '1_4'))
            button_save = tk.Button(self.main_frame, text='<-', command=lambda: self.copy_conf('text', '4_1'))
            button_load.grid(column=1, row=1, sticky=tk.SE, padx=5, pady=70)
            button_save.grid(column=1, row=1, sticky=tk.SW, padx=5, pady=70)
            button_load = tk.Button(self.main_frame, text='->', command=lambda: self.copy_conf('all', '1_4'))
            button_save = tk.Button(self.main_frame, text='<-', command=lambda: self.copy_conf('all', '4_1'))
            button_load.grid(column=1, row=1, sticky=tk.E, padx=5, pady=5)
            button_save.grid(column=1, row=1, sticky=tk.W, padx=5, pady=5)

            # App4 frame
            self.app4_frame = tk.Frame(self.main_frame, borderwidth=2, relief='groove')
            self.app4_frame.grid(column=2, row=1, sticky=tk.EW, padx=5, pady=5)
            self.app4 = ImageEditor(self.app4_frame, exclusion_zones[1])

            # frame load save and export
            self.export_frame = tk.Frame(self.main_frame, borderwidth=2, relief='groove')
            self.export_frame.grid(column=0, row=2, columnspan=3, padx=5, pady=5)

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
            tk.Label(self.export_frame, text="Nom du set de cadre :").grid(column=0, row=1, sticky=tk.EW, padx=5, pady=5)
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
                path_to_xml = path.join("../Templates/", self.selected_template.get())
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

            # Ouvre la boîte de dialogue pour la sélection du répertoire
            selected_dir = filedialog.askdirectory()
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
            project_data = {
                "project_name": self.prj_name_var.get(),
                "app1": {
                    "text": self.app1.text.get(),
                    "font": self.app1.sel_font,
                    "font_color": self.app1.font_color,
                    "font_name": self.app1.font_name,
                    "background_color": self.app1.background_couleur,
                    "image_path": self.app1.imported_image_path,
                    "image_size": self.app1.display_imported_image_size,
                    "display_position": self.app1.img_display_position,
                    "text_display_position": self.app1.text_display_position,
                },
                "app4": {
                    "text": self.app4.text.get(),
                    "font": self.app4.sel_font,
                    "font_color": self.app4.font_color,
                    "font_name": self.app4.font_name,
                    "background_color": self.app4.background_couleur,
                    "image_path": self.app4.imported_image_path,
                    "image_size": self.app4.display_imported_image_size,
                    "display_position": self.app4.img_display_position,
                    "text_display_position": self.app4.text_display_position,
                }
            }

            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if file_path:
                with open(file_path, 'w') as file:
                    dump(project_data, file)
                messagebox.showinfo("Sauvegarde réussie", "Le projet a été sauvegardé avec succès.")
        except (FileNotFoundError, IsADirectoryError):
            messagebox.showerror("Erreur de fichier", "Impossible de sauvegarder le projet.")
        except Exception as e:
            messagebox.showerror("Erreur de sauvegarde", f"Une erreur inattendue s'est produite lors de la sauvegarde : {str(e)}")

    def load_project(self):
        """Charge un projet depuis un fichier JSON."""
        try:
            file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
            if file_path:
                with open(file_path, 'r') as file:
                    project_data = load(file)

                self.prj_name_var.set(project_data["project_name"])
                self._load_editor_state(self.app1, project_data["app1"])
                self._load_editor_state(self.app4, project_data["app4"])

                self.app1.on_text_change('from load')
                self.app4.on_text_change('from load')
        except (FileNotFoundError, IsADirectoryError):
            messagebox.showerror("Erreur de fichier", "Impossible de charger le projet.")
        except JSONDecodeError:
            messagebox.showerror("Erreur de JSON", "Le fichier est corrompu ou non valide.")
        except Exception as e:
            messagebox.showerror("Erreur de chargement", f"Une erreur inattendue s'est produite : {str(e)}")

    @staticmethod
    def _load_editor_state(editor, data):
        """Charge l'état d'un éditeur spécifique."""
        try:
            editor.text.set(data["text"])
            editor.sel_font = data["font"]
            editor.font_color = data["font_color"]
            editor.font_name = data["font_name"]
            editor.background_couleur = data["background_color"]
            editor.texte_background_value.set(data["background_color"])
            editor.label_couleur.config(bg=data["background_color"])

            if data["image_path"]:
                editor.imported_image_path = data["image_path"]
                try:
                    editor.original_image = Image.open(editor.imported_image_path).convert('RGBA')
                except UnidentifiedImageError:
                    messagebox.showerror("Erreur d'image", f"Le fichier image spécifié est introuvable ou corrompu.")
                    return

                editor.display_imported_image_size = data['image_size']
                editor.display_imported_image = editor.original_image.resize(editor.display_imported_image_size)
                editor.image_imported_image = editor.original_image.copy()
                editor.image_imported_image_size = (editor.display_imported_image_size[0] * editor.RATIO,
                                                    editor.display_imported_image_size[1] * editor.RATIO)
                editor.image_imported_image = editor.original_image.resize(editor.image_imported_image_size)

            editor.img_display_position = data["display_position"]
            editor.text_display_position = data["text_display_position"]
        except KeyError as e:
            messagebox.showerror("Erreur de données", f"La clé {str(e)} est manquante dans les données du projet.")

    # gestion de la synchro droite gauche
    def copy_conf(self, layer, direction):
        """
        copie la configuration d'une layer vers l'autre

        layer : calque à prendre en compte :
                'background', 'image', 'text' or 'all
        dir : copie de 1 vers 4 ou 4 vers 1 '1_4' or '4_1'
        """
        try:
            if layer == 'background' or layer == 'all':
                if direction == '1_4':
                    self.app4.background_couleur = self.app1.background_couleur
                elif direction == '4_1':
                    self.app1.background_couleur = self.app4.background_couleur
                else:
                    raise ValueError(f'ERROR: {direction} is not a valid DIR')
            if layer == 'image' or layer == 'all':
                if direction == '1_4':
                    self.app4.imported_image_path = self.app1.imported_image_path
                    self.app4.original_image = self.app1.original_image
                    self.app4.display_imported_image_size = self.app1.display_imported_image_size
                    self.app4.display_imported_image = self.app1.display_imported_image
                    self.app4.image_imported_image = self.app1.image_imported_image
                    self.app4.image_imported_image_size = self.app1.image_imported_image_size
                    self.app4.img_display_position = self.app1.img_display_position
                elif direction == '4_1':
                    self.app1.imported_image_path = self.app4.imported_image_path
                    self.app1.original_image = self.app4.original_image
                    self.app1.display_imported_image_size = self.app4.display_imported_image_size
                    self.app1.display_imported_image = self.app4.display_imported_image
                    self.app1.image_imported_image = self.app4.image_imported_image
                    self.app1.image_imported_image_size = self.app4.image_imported_image_size
                    self.app1.img_display_position = self.app4.img_display_position
                else:
                    raise ValueError(f'ERROR: {direction} is not a valid DIR')
            if layer == 'text' or layer == 'all':
                if direction == '1_4':
                    self.app4.text.set(self.app1.text.get())
                    self.app4.sel_font = self.app1.sel_font
                    self.app4.font_color = self.app1.font_color
                    self.app4.font_name = self.app1.font_name
                    self.app4.text_display_position = self.app1.text_display_position
                elif direction == '4_1':
                    self.app1.text.set(self.app4.text.get())
                    self.app1.sel_font = self.app4.sel_font
                    self.app1.font_color = self.app4.font_color
                    self.app1.font_name = self.app4.font_name
                    self.app1.text_display_position = self.app4.text_display_position
                else:
                    raise ValueError(f'ERROR: {direction} is not a valid DIR')

            self.app1.update_canvas()
            self.app4.update_canvas()
        except ValueError as e:
            messagebox.showerror("Erreur de direction", f"Une erreur s'est produite lors de la copie des couches : {str(e)}")

    # gestion des templates
    def on_template_change(self, *args):
        """
        appelé lors du changement de template
        charge le xml et met à jour les zones d'exclusion
        """
        try:
            # Charger et analyser le fichier XML
            path_to_xml = path.join("../Templates/", self.selected_template.get())
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
            self.app4.exclusion_zone = new_exc_zone4
            self.app1.update_canvas()
            self.app4.update_canvas()
        except (FileNotFoundError, IsADirectoryError):
            messagebox.showerror("Erreur de fichier", "Le fichier XML spécifié est introuvable.")
        except Et.ParseError:
            messagebox.showerror("Erreur de XML", "Le fichier XML est corrompu ou non valide.")
        except Exception as e:
            messagebox.showerror("Erreur de template", f"Une erreur inattendue s'est produite : {str(e)}")


if __name__ == "__main__":

    # <mxGeometry x="50" y="20" width="330" height="470" as="geometry" />
    # Y X H W
    exclusion_zones_1 = [
        (50, 20, 470, 330),
    ]

    tk_root = tk.Tk()
    ImageEditorApp(tk_root, (exclusion_zones_1, exclusion_zones_1))
    tk_root.mainloop()