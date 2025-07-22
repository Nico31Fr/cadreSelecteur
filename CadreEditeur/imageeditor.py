# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |-> fenêtre d'édition d'un cadre  """

import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageTk, UnidentifiedImageError
from re import fullmatch
from pathlib import Path

import matplotlib.font_manager as fm

from text import askfont


class ImageEditor:
    """
    Une application d'édition d'image simple permettant aux utilisateurs
    d'importer des images, d'ajouter du texte, de déplacer/redimensionner les images,
    et d'enregistrer la composition finale.
    """

    def __init__(self, root, exclusion_zone):
        """
        Initialise l'application ImageEditor avec une fenêtre tkinter racine.

        Paramètres :
            root (tk.Tk) : La fenêtre tkinter racine.
            Exclusion_zone : liste contenant les zone à garder en transparent
        """
        try:
            # Dimension de l'interface, doit être de ratio 1.5
            self.CANVA_W = 600
            self.CANVA_H = 400
            # Dimension de l'image générée
            self.IMAGE_W = 3600
            self.IMAGE_H = 2400
            self.RATIO = int(self.IMAGE_W / self.CANVA_W)
            self.exclusion_zone = exclusion_zone
            self.imported_image_path = None
            self.display_imported_image = None
            self.image_imported_image = None
            self.original_image = None
            self.background_couleur = '#FFFFFF'

            # variable pour la gestion du texte
            self.sel_font = {'family': "arial", 'size': 12}
            self.font_name: str = "msgothic.ttc"
            self.pil_font = ImageFont.truetype(self.font_name, self.sel_font['size'])
            self.font_color = '#000000'
            # Variables pour déplacer le texte
            self.text_display_position = (0, 0)
            self.text_image_position = (self.text_display_position[0] * self.RATIO,
                                        self.text_display_position[1] * self.RATIO)

            # Variables pour déplacer l'image importée
            self.img_display_position = (150, 150)
            self.img_image_position = (self.img_display_position[0] * self.RATIO,
                                       self.img_display_position[1] * self.RATIO)
            self.display_imported_image_size = (0, 0)
            self.image_imported_image_size = (0, 0)

            # creation dun canva qui va afficher l'image
            # Créer un cadre (Frame)
            self.frame = tk.Frame(root, borderwidth=2, relief="solid")
            self.frame.pack(side='top')
            self.canvas = tk.Canvas(self.frame,
                                    width=self.CANVA_W,
                                    height=self.CANVA_H)
            self.canvas.pack()
            # Fond blanc
            self.image_de_font = Image.new('RGBA',
                                           (self.IMAGE_W, self.IMAGE_H),
                                           (255, 255, 255, 255))
            self.draw = ImageDraw.Draw(self.image_de_font)

            # Redimensionnement pour affichage
            self.image_export = self.image_de_font.copy()
            self.display_image = self.image_export.resize((self.CANVA_W,
                                                           self.CANVA_H))
            self.tk_image = ImageTk.PhotoImage(self.display_image)
            self.canvas_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

            # affichage de l'image des layers
            try:
                # Charger l'image à l'aide de PIL
                img_layer = Image.open("./layers.png")
                img_layer = img_layer.resize((75, 75))
                self.img_layer_tk = ImageTk.PhotoImage(img_layer)
                # Créer un Canvas
                canvas_img_layer = tk.Canvas(root, width=80, height=80)
                canvas_img_layer.pack(side='right', fill='x')
                # Ajoute l'image au Canvas
                canvas_img_layer.create_image(5, 5, anchor='nw', image=self.img_layer_tk)
            except FileNotFoundError:
                messagebox.showerror("Erreur", "Le fichier layers.png est introuvable.")
            except UnidentifiedImageError:
                messagebox.showerror("Erreur", "Le fichier layers.png n'est pas une image valide.")

            # creation de la 'control frame'
            self.controls_frame = tk.Frame(root)
            self.controls_frame.pack(fill='x')

            # variables texte
            self.text = tk.StringVar()
            # variable pour afficher le code couleur
            self.texte_background_value = tk.StringVar()

            # configure la grille pour les boutons 4 lignes x 3 colonnes
            self.controls_frame.rowconfigure(0, weight=2)
            self.controls_frame.rowconfigure(1, weight=1)
            self.controls_frame.rowconfigure(2, weight=1)
            self.controls_frame.rowconfigure(3, weight=1)
            self.controls_frame.columnconfigure(0, weight=1)
            self.controls_frame.columnconfigure(1, weight=2)
            self.controls_frame.columnconfigure(2, weight=1)
            self.controls_frame.columnconfigure(3, weight=1)

            # bouton et saisie pour le texte
            tk.Button(self.controls_frame,
                      text='Police',
                      command=self.callback_font).grid(column=0, row=0, sticky=tk.EW, padx=5, pady=5)
            tk.Entry(self.controls_frame,
                     textvariable=self.text).grid(column=1, row=0, sticky=tk.EW, padx=5, pady=5)
            tk.Button(self.controls_frame,
                      text='Couleur',
                      command=lambda: self.choisir_couleur('font')).grid(column=2, row=0, sticky=tk.EW, padx=5, pady=5)

            # bouton pour import image
            tk.Button(self.controls_frame,
                      text='Image',
                      command=self.import_image).grid(column=0, row=1, sticky=tk.EW, padx=5, pady=5)
            self.label_image = tk.Label(self.controls_frame, text='')
            self.label_image.grid(column=1, row=1, sticky=tk.EW, padx=5, pady=5)
            tk.Button(self.controls_frame,
                      text='Effacer',
                      command=self.remove_image).grid(column=2, row=1, sticky=tk.EW, padx=5, pady=5)

            # bouton et saisie pour la couleur de fond
            # Créer un bouton pour ouvrir le sélecteur de couleur
            tk.Label(self.controls_frame, text="couleur du fond :").grid(column=0, row=2, sticky=tk.EW, padx=5, pady=5)
            self.texte_background = tk.Entry(self.controls_frame, textvariable=self.texte_background_value, width=8)
            self.texte_background.insert(0, self.background_couleur)
            self.texte_background.grid(column=2, row=2, sticky=tk.EW, padx=5, pady=5)
            # Créer un label pour afficher la couleur sélectionnée
            self.label_couleur = tk.Label(self.controls_frame, text=" ")
            self.label_couleur.grid(column=1, row=2, sticky=tk.EW, padx=5, pady=5)
            self.label_couleur.bind("<Button-1>", lambda event: self.choisir_couleur('background'))
            # Mettre à jour la couleur du label_couleur
            self.label_couleur.config(bg=self.background_couleur)

            # bouton radio pour selection calque actif
            # Variable pour stocker la sélection
            self.selection = tk.StringVar(value='C_Image')
            self.radio_image = tk.Radiobutton(self.controls_frame,
                                              variable=self.selection,
                                              text='Calque Image',
                                              value='C_Image')
            self.radio_image.grid(column=3, row=1, sticky=tk.EW, padx=5, pady=5)
            self.radio_texte = tk.Radiobutton(self.controls_frame,
                                              variable=self.selection,
                                              text='Calque Texte',
                                              value='C_Texte')
            self.radio_texte.grid(column=3, row=0, sticky=tk.EW, padx=5, pady=5)

            # Événements de souris pour déplacer/redimensionner
            self.canvas.bind("<Button-1>", self.start_drag)
            self.canvas.bind("<B1-Motion>", self.drag_drop)
            self.canvas.bind("<MouseWheel>", self.resize)

            # Lier une fonction à la modification de la valeur de l'Entry
            self.texte_background_value.trace_add("write",
                                                  self.on_color_entry_change)
            self.text.trace_add("write", self.on_text_change)
            self.img_start_drag_pos = None
            self.txt_start_drag_pos = None
            self.update_canvas()
        except Exception as e:
            messagebox.showerror("Erreur Initialization", f"Une erreur inattendue s'est produite : {str(e)}")

    # Gestion du Texte
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

    def on_text_change(self, *args):
        """
        Ajoute du texte provenant du champ de texte
        à l'image à une position prédéfinie.
        """
        try:
            if args:
                self.update_canvas()
        except Exception as e:
            messagebox.showerror("Erreur de texte", f"Exception inattendue : {str(e)}")

    def callback_font(self):
        """
        lorsque le bouton font est cliqué lance l'interface
         de selection de police d'écriture
        """
        try:
            font_selected = askfont(self.controls_frame,
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
                # mise à jour de l'IHM
                self.on_text_change('from selector')
        except Exception as e:
            messagebox.showerror("Erreur de font", f"Exception inattendue : {str(e)}")

    # Gestion de l'image
    def import_image(self):
        """
        Ouvre une boîte de dialogue pour importer une image et
        met à jour le canvas avec l'image importée,
        en conservant le ratio original.
        """
        try:
            self.imported_image_path = filedialog.askopenfilename()
            if self.imported_image_path:
                try:
                    self.original_image = Image.open(self.imported_image_path).convert('RGBA')
                except UnidentifiedImageError:
                    messagebox.showerror("Erreur d'image", f"Le fichier image spécifié est introuvable ou corrompu.")
                    return

                # Calculer la nouvelle taille en conservant le ratio
                original_width, original_height = self.original_image.size
                aspect_ratio = original_width / original_height

                desired_width = self.CANVA_W
                desired_height = int(desired_width / aspect_ratio)

                self.display_imported_image_size = (desired_width, desired_height)
                self.display_imported_image = self.original_image.resize(self.display_imported_image_size)
                self.image_imported_image = self.original_image.copy()
                self.image_imported_image_size = (desired_width*self.RATIO,
                                                  desired_height*self.RATIO)
                self.image_imported_image = self.original_image.resize(self.image_imported_image_size)

                self.update_canvas()
        except FileNotFoundError:
            messagebox.showerror("Erreur de fichier", "Le fichier image spécifié est introuvable.")
        except Exception as e:
            messagebox.showerror("Erreur d'importation", f"Exception inattendue : {str(e)}")

    def remove_image(self):
        """
        efface l'image importé lorsqu'on clique sur le bouton
        """
        try:
            self.display_imported_image = None
            self.update_canvas()
        except Exception as e:
            messagebox.showerror("Erreur de suppression", f"Exception inattendue : {str(e)}")

    # gestion souri drag and drop / zoom molette
    def start_drag(self, event):
        """
        Initialise l'opération de glissement-déposé en enregistrant la position du curseur.

        Paramètres :
            event (tk.Event) : L'événement de clic de la souris.
        """
        try:
            if self.selection.get() == 'C_Image':
                self.img_start_drag_pos = (event.x, event.y)
            else:
                self.txt_start_drag_pos = (event.x, event.y)
        except Exception as e:
            messagebox.showerror("Erreur de démarrage", f"Exception inattendue : {str(e)}")

    def drag_drop(self, event):
        """
        gestion du drag and drop

        Paramètres :
            event (tk.Event) : L'événement de mouvement de la souris.
        """
        try:
            if self.img_start_drag_pos and self.selection.get() == 'C_Image':
                dx = event.x - self.img_start_drag_pos[0]
                dy = event.y - self.img_start_drag_pos[1]

                new_disp_x = self.img_display_position[0] + dx
                new_disp_y = self.img_display_position[1] + dy

                # met à jour la position de l'image importé dans le canva
                self.img_display_position = (new_disp_x,
                                             new_disp_y)

                self.img_start_drag_pos = (event.x, event.y)
                self.update_canvas()

            if self.txt_start_drag_pos and self.selection.get() == 'C_Texte':

                dx = event.x - self.txt_start_drag_pos[0]
                dy = event.y - self.txt_start_drag_pos[1]

                new_disp_x = self.text_display_position[0] + dx
                new_disp_y = self.text_display_position[1] + dy

                # met à jour la position du texte dans le canva
                self.text_display_position = (new_disp_x,
                                              new_disp_y)

                self.txt_start_drag_pos = (event.x, event.y)
                self.update_canvas()
        except Exception as e:
            messagebox.showerror("Erreur de déplacement", f"Exception inattendue : {str(e)}")

    def resize(self, event):
        """
        redimensionne l'image importée en fonction de la molette souris

        Paramètres :
            event (tk.Event) : L'événement de mouvement de la souris.
        """
        try:
            if self.original_image and self.selection.get() == 'C_Image':
                delta = 10 if event.delta > 0 else -10
                # Calculer la nouvelle taille en conservant le ratio
                original_width, original_height = self.original_image.size
                aspect_ratio = original_width / original_height

                new_width = self.display_imported_image_size[0] + delta
                new_height = int(new_width / aspect_ratio)
                # min imagesize is 10/15px
                new_width = max(15, new_width)
                new_height = max(10, new_height)

                self.display_imported_image_size = (new_width, new_height)
                self.image_imported_image_size = (new_width*self.RATIO,
                                                  new_height*self.RATIO)
                self.display_imported_image = self.original_image.resize(self.display_imported_image_size)
                self.image_imported_image = self.original_image.resize(self.image_imported_image_size)
            elif self.selection.get() == 'C_Texte':
                delta = 2 if event.delta > 0 else -2
                self.sel_font['size'] = max(4, self.sel_font['size'] + delta)
            self.update_canvas()
        except Exception as e:
            messagebox.showerror("Erreur de redimensionnement", f"Exception inattendue : {str(e)}")

    # gestion background
    def choisir_couleur(self, event):
        """ Ouvrir une boîte de dialogue de sélection de couleur """
        try:
            couleur = colorchooser.askcolor(title="Choisissez une couleur")
            if couleur[1] and event == 'background':
                self.background_couleur = couleur[1]
                self.update_canvas()
            if couleur[1] and event == 'font':
                self.font_color = couleur[1]
                # Mettre à jour la couleur et le texte du label
                self.update_canvas()
        except Exception as e:
            messagebox.showerror("Erreur de couleur", f"Exception inattendue : {str(e)}")

    def on_color_entry_change(self, *args):
        """
        une nouvelle valeur de couleur a été saisie, mettre à jour
        """
        try:
            if args:
                color_code = self.texte_background_value.get()
                match = fullmatch(r'^#[0-9A-Fa-f]{6}$', color_code)
                if match:
                    self.background_couleur = color_code
                    self.update_canvas()
        except Exception as e:
            messagebox.showerror("Erreur de couleur", f"Exception inattendue : {str(e)}")

    # export de l'image
    def save_image(self, out_path: str):
        """
        Ouvre une boîte de dialogue pour enregistrer l'image courante dans un fichier.
        """
        try:
            # couleur du fond
            # génère une image avec la couleur de fond sélectionnée
            self.image_de_font = Image.new('RGBA',
                                           (self.IMAGE_W, self.IMAGE_H),
                                           self.background_couleur)

            # évite l'effacement par le garbage collector
            self.image_export = self.image_de_font.copy()

            # mise à jour des positions texte et image dans l'image exporté
            self.text_image_position = (self.text_display_position[0] * self.RATIO,
                                        self.text_display_position[1] * self.RATIO)
            self.img_image_position = (self.img_display_position[0] * self.RATIO,
                                       self.img_display_position[1] * self.RATIO)

            # insère l'image importée
            if self.display_imported_image:
                self.image_export.paste(self.image_imported_image,
                                        self.img_image_position,
                                        self.image_imported_image)

            # insère le texte
            draw_i = ImageDraw.Draw(self.image_export)
            pil_font_i = ImageFont.truetype(font=self.font_name,
                                            size=(self.sel_font['size'] * self.RATIO))
            draw_i.text(self.text_image_position,
                        self.text.get(),
                        fill=self.font_color,
                        font=pil_font_i)

            # insère les zones transparentes (Display et Image)
            for d_x, d_y, d_w, d_h in self.exclusion_zone:
                i_x, i_y, i_w, i_h = (d_x * self.RATIO, d_y * self.RATIO, d_w * self.RATIO, d_h * self.RATIO)
                draw_i.rectangle((i_x, i_y, i_x + i_w, i_y + i_h), fill=(255, 255, 255, 0))

            # Enregistre le fichier image.
            extension = str('_' + str(len(self.exclusion_zone)) + '.png')
            out_path = out_path + extension
            self.image_export.save(out_path)
        except Exception as e:
            messagebox.showerror("Erreur d'enregistrement", f"Exception inattendue : {str(e)}")

    # mise à jour de la prévisualisation IHM
    def update_canvas(self):
        """
        Met à jour le canvas pour refléter l'état actuel de l'image.
        """
        try:
            # couleur du fond
            # met à jour le label (couleur et texte)
            self.label_couleur.config(bg=self.background_couleur)
            self.texte_background.delete(0, tk.END)  # Efface le champ existant
            self.texte_background.insert(0, self.background_couleur)
            # génère une image avec la couleur sélectionnée
            display_image = Image.new('RGBA',
                                      (self.CANVA_W, self.CANVA_H),
                                      self.background_couleur)

            # évite l'effacement par le garbage collector
            temp_image = display_image.copy()

            # insère l'image importée
            if self.display_imported_image:
                temp_image.paste(self.display_imported_image,
                                 self.img_display_position,
                                 self.display_imported_image)
                self.label_image.config(text=Path(self.imported_image_path).name)
            else:
                self.label_image.config(text='')

            # insère le texte
            # Crée un objet ImageDraw pour dessiner sur l'image
            draw_d = ImageDraw.Draw(temp_image)
            self.pil_font = ImageFont.truetype(font=self.font_name,
                                               size=self.sel_font['size'])
            draw_d.text(self.text_display_position,
                        self.text.get(),
                        fill=self.font_color,
                        font=self.pil_font)

            # insère les zones transparentes (Display et Image)
            for zone in self.exclusion_zone:
                d_x, d_y, d_w, d_h = zone
                draw_d.rectangle((d_x, d_y, d_x + d_w, d_y + d_h),
                                 fill=(255, 255, 255, 0))

            # met a jour l'IHM
            self.tk_image = ImageTk.PhotoImage(temp_image)
            self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)
        except Exception as e:
            messagebox.showerror("Erreur de mise à jour", f"Exception inattendue : {str(e)}")