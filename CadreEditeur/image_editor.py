# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth """

import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox, font
from PIL import Image, ImageDraw, ImageFont, ImageTk
from re import fullmatch
from os import path
import matplotlib.font_manager as fm

from tkfontchooser import askfont

class ImageEditorApp:
    """
    Une application d'édition d'image simple permettant aux utilisateurs
    d'importer des images, d'ajouter du texte, de déplacer/redimensionner les images,
    et d'enregistrer la composition finale.
    """

    def __init__(self, root, exclusion_zones):
        """
        Initialise l'application ImageEditorApp avec une fenêtre tkinter racine.

        Paramètres :
            root (tk.Tk) : La fenêtre tkinter racine.
        """

        # Dimension de l'interface, doit être de ratio 1.5
        self.CANVA_W = 600
        self.CANVA_H = 400
        # Dimension de l'image géneré
        self.IMAGE_W = 3600
        self.IMAGE_H = 2400
        self.RATIO = int(self.IMAGE_W / self.CANVA_W)
        self.FONT_PATH = "C:/Windows/Fonts"

        self.imported_image_path = None
        self.display_imported_image = None
        self.image_imported_image = None
        self.original_image = None
        self.background_couleur = '#FFFFFF'

        # variable pour la gestion du texte
        self.sel_font = font.Font(family="Helvetica", size=12, weight="bold")
        self.pil_font = ImageFont.truetype(font="msgothic.ttc")
        self.texte_position = (0, 0)

        # creation dun canva qui va afficher l'image
        # Créer un cadre (Frame)
        self.frame = tk.Frame(root, borderwidth=2, relief="solid")
        self.frame.pack()

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
        self.canvas_image_id = self.canvas.create_image(0,
                                                        0,
                                                        anchor=tk.NW,
                                                        image=self.tk_image)

        self.controls_frame = tk.Frame(root)
        self.controls_frame.pack()

        # configure la grille pour les boutons
        self.controls_frame.rowconfigure(0, weight=2)
        self.controls_frame.rowconfigure(1, weight=1)
        self.controls_frame.rowconfigure(2, weight=1)
        self.controls_frame.rowconfigure(3, weight=1)
        self.controls_frame.columnconfigure(0, weight=1)
        self.controls_frame.columnconfigure(1, weight=2)
        self.controls_frame.columnconfigure(2, weight=2)

        self.text = tk.StringVar()
        self.texte_background_value = tk.StringVar()

        # Créer un bouton pour ouvrir le sélecteur de couleur
        tk.Label(self.controls_frame, text="couleur du fond :").grid(column=0, row=0, sticky=tk.EW, padx=5, pady=5)
        self.texte_background = tk.Entry(self.controls_frame, textvariable=self.texte_background_value)
        self.texte_background.insert(0, self.background_couleur)
        self.texte_background.grid(column=2, row=0, sticky=tk.EW, padx=5, pady=5)
        # Créer un label pour afficher la couleur sélectionnée
        self.label_couleur = tk.Label(self.controls_frame, text=" ")
        self.label_couleur.grid(column=1, row=0, sticky=tk.EW, padx=5, pady=5)
        self.label_couleur.bind("<Button-1>", lambda event: self.choisir_couleur())
        # texte
        tk.Button(self.controls_frame, text="Ajouter le texte", command=self.add_text).grid(column=0, row=2, sticky=tk.EW, padx=5, pady=5)
        tk.Entry(self.controls_frame, textvariable=self.text).grid(column=1, row=2, sticky=tk.EW, padx=5, pady=5)
        tk.Button(self.controls_frame, text='Police', command=self.callback_font).grid(column=2, row=2, sticky=tk.EW, padx=5, pady=5)
        # import image
        tk.Button(self.controls_frame, text="Importer une image", command=self.import_image).grid(column=0, row=3, sticky=tk.EW, padx=5, pady=5)

        # Mettre à jour la couleur du label_couleur
        self.label_couleur.config(bg=self.background_couleur)

        # Variables pour déplacer l'image importée
        self.display_position = (150, 150)
        self.image_position = (self.display_position[0] * self.RATIO,
                               self.display_position[1] * self.RATIO)
        self.display_imported_image_size = (0, 0)
        self.image_imported_image_size = (0, 0)

        self.exclusion_zones = exclusion_zones

        # Événements de souris pour déplacer/redimensionner
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_image)
        self.canvas.bind("<MouseWheel>", self.resize_image)

        # Lier une fonction à la modification de la valeur de l'Entry
        self.texte_background_value.trace_add("write",
                                              self.on_color_entry_change)

        self.start_drag_position = None
        self.update_canvas()

    @staticmethod
    def find_font_path(font_name):
        """
        trouve le chemin de la police
        """
        # Obtenir la liste de toutes les polices système
        font_paths = fm.findSystemFonts(fontpaths=None, fontext='ttf')

        for font_path in font_paths:
            # Vérifier si le nom de la police correspond
            prop = fm.FontProperties(fname=font_path)
            if prop.get_name().lower() == font_name.replace('@','').lower():
                return font_path
        return None

    def add_text(self):
        """
        Ajoute du texte provenant du champ de texte
        à l'image à une position prédéfinie.

        see https://github.com/PrabhanjanJois/textEditor_using_Tkinter-jois_textEditor-

        """
        print(f'>>> font: {self.sel_font["family"]}')
        # Obtenir la police et sa taille
        font_name = self.find_font_path(self.sel_font['family'])
        font_size = self.sel_font['size']

        print(f'>>> {font_name} - {font_size} -> {self.text.get()}')

        if font_name is not None:
            self.pil_font = ImageFont.truetype(font=font_name, size=font_size)
        else:
            self.pil_font = ImageFont.truetype(font="msgothic.ttc")

        self.update_canvas()


    def callback_font(self):
        """
        lorsque le boutton font est cliquer lance l'interface
         de selection de police d'écriture
        """
        self.sel_font = askfont(self.controls_frame,
                       text=self.text.get(),
                       title="Police")



    def import_image(self):
        """
        Ouvre une boîte de dialogue pour importer une image et
        met à jour le canvas avec l'image importée,
        en conservant le ratio original.
        """
        self.imported_image_path = filedialog.askopenfilename()
        if self.imported_image_path:
            self.original_image = Image.open(self.imported_image_path).convert('RGBA')
            # Calculer la nouvelle taille en conservant le ratio
            original_width, original_height = self.original_image.size
            aspect_ratio = original_width / original_height

            desired_width = self.CANVA_W
            desired_height = int(desired_width / aspect_ratio)

            self.display_imported_image_size = (desired_width, desired_height)
            self.display_imported_image = self.original_image.resize(self.display_imported_image_size)
            self.image_imported_image = self.original_image.copy()
            self.update_canvas()


    def start_drag(self, event):
        """
        Initialise l'opération de glissement-déposé en enregistrant la position du curseur.

        Paramètres :
            event (tk.Event) : L'événement de clic de la souris.
        """
        self.start_drag_position = (event.x, event.y)


    def drag_image(self, event):
        """
        drag and drop de l'image importé avec la souris

        Paramètres :
            event (tk.Event) : L'événement de mouvement de la souris.
        """
        if self.start_drag_position:
            dx = event.x - self.start_drag_position[0]
            dy = event.y - self.start_drag_position[1]
            # met à jour la position de l'image importé dans le canva
            self.display_position = (self.display_position[0] + dx,
                                     self.display_position[1] + dy)
            # met à jour la position de l'image importé dans l'image'
            self.image_position = (self.display_position[0] * self.RATIO,
                                   self.display_position[1] * self.RATIO)
            self.start_drag_position = (event.x, event.y)
            self.update_canvas()


    def resize_image(self, event):
        """
        redimensionne l'image importé en fonction de la molette souris

        Paramètres :
            event (tk.Event) : L'événement de mouvement de la souris.
        """
        if self.original_image:
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

            self.update_canvas()


    def update_canvas(self):
        """
        Met à jour le canvas pour refléter l'état actuel de l'image.
        """

        self.image_de_font = Image.new('RGBA',
                                       (self.IMAGE_W, self.IMAGE_H),
                                       self.background_couleur)
        display_image = self.image_de_font.resize((self.CANVA_W,
                                                   self.CANVA_H))

        temp_image = display_image.copy()
        self.image_export = self.image_de_font.copy()

        if self.display_imported_image:
            temp_image.paste(self.display_imported_image,
                             self.display_position,
                             self.display_imported_image)
            self.image_export.paste(self.image_imported_image,
                                    self.image_position,
                                    self.image_imported_image)

        # insère le texte
        # Crée un objet ImageDraw pour dessiner sur l'image
        draw_d = ImageDraw.Draw(temp_image)
        draw_i = ImageDraw.Draw(self.image_export)

        draw_d.text((0, 0),
                       self.text.get(),
                       fill=(0, 0, 0, 255),
                       font=self.pil_font)
        draw_i.text((0, 0),
                       self.text.get(),
                       fill=(0, 0, 0, 255),
                       font=self.pil_font)

        # insère les zones transparentes (Display et Image)
        for zone in self.exclusion_zones:
            d_x, d_y, d_w, d_h = zone
            i_x, i_y, i_w, i_h = d_x*self.RATIO, d_y*self.RATIO, d_w*self.RATIO, d_h*self.RATIO
            draw_d.rectangle((d_x, d_y, d_x + d_w, d_y + d_h),
                           fill=(255, 255, 255, 0))
            draw_i.rectangle((i_x, i_y, i_x + i_w, i_y + i_h),
                           fill=(255, 255, 255, 0))

        # met a jour l'IHM
        self.tk_image = ImageTk.PhotoImage(temp_image)
        self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)


    def choisir_couleur(self, event=None):
        """ Ouvrir une boîte de dialogue de sélection de couleur """
        print(event)
        couleur = colorchooser.askcolor(title="Choisissez une couleur")
        if couleur[1] :
            self.background_couleur = couleur[1]
            # Mettre à jour la couleur et le texte du label
            self.label_couleur.config(bg=str(couleur[1]))
            self.texte_background.delete(0, tk.END)  # Efface le champ existant
            self.texte_background.insert(0, str(couleur[1]))
            self.update_canvas()


    def on_color_entry_change(self, *args):
        """
        une nouvelle valeur de couleur a été saisie, mettre à jour
        """

        color_code = self.texte_background_value.get()
        match = fullmatch(r'^#[0-9A-Fa-f]{6}$', color_code)
        if match:
            self.background_couleur = color_code
            self.label_couleur.config(bg=color_code)
            self.update_canvas()


    def save_image(self, out_path: str):
        """
        Ouvre une boîte de dialogue pour enregistrer l'image courante dans un fichier.
        """
        extension = str('_' + str(len(self.exclusion_zones)) + '.png')
        out_path = out_path + extension
        self.image_export.save(out_path)


def save_images(app_1, app_4):
    """
    lance l'enregistrement des deux fichiers
    """

    path_im = select_directory()
    if path_im is not None:
        app_1.save_image(path_im)
        app_4.save_image(path_im)


def select_directory():
    """
    sélectionne le repertoire de sortie
    et construction du path de sortie avec le nom du projet
    """

    tmp_prj_name = prj_name_var.get()

    if tmp_prj_name == "":
        messagebox.showerror(title='erreur nom du projet',
                             message="saisir le nom du projet")
        return None

    # Ouvre la boîte de dialogue pour la sélection du répertoire
    selected_dir = filedialog.askdirectory()
    path_prj_name = path.join(selected_dir, tmp_prj_name)

    if selected_dir :  # Vérifie si l'utilisateur a sélectionné un répertoire
        print(f"Répertoire de sortie sélectionné : {path_prj_name}")
        return path_prj_name
    else:
        messagebox.showerror(title='erreur repertoire',
                             message="selectionner un repertoire de sortie")
        return None


if __name__ == "__main__":
    # Définir des zones d'exclusion
    # <mxGeometry x="20" y="420" width="110" height="160" as="geometry" />
    # <mxGeometry x="145" y="420" width="110" height="160" as="geometry" />
    # <mxGeometry x="270" y="420" width="110" height="160" as="geometry" />
    # <mxGeometry x="20" y="20" width="280" height="350" as="geometry" />
    # Y X H W
    exclusion_zones_4 = [
        (420, 20, 160, 110),
        (420, 145, 160, 110),
        (420, 270, 160, 110),
        (20, 20, 350, 280)
    ]

    # <mxGeometry x="50" y="20" width="330" height="470" as="geometry" />
    # Y X H W
    exclusion_zones_1 = [
        (50, 20, 470, 330),
    ]

    # Dimension de la fenêtre
    WINDOWS = "1400x600"

    tk_root = tk.Tk()

    # Fixer la taille de la fenêtre
    tk_root.geometry(WINDOWS)  # Largeur = 700 pixels, Hauteur = 1200 pixels
    # Optionnel : Empêcher le redimensionnement de la fenêtre
    tk_root.resizable(False, False)
    tk_root.title("Créateur de cadre V0.1")

    # Création de frame parent
    main_frame = tk.Frame(tk_root)
    main_frame.pack(expand=True, fill='both')

    # App1 frame
    app1_frame = tk.Frame(main_frame)
    app1_frame.pack(side="left", fill="both", expand=True)
    app1 = ImageEditorApp(app1_frame, exclusion_zones_1)

    # App4 frame
    app4_frame = tk.Frame(main_frame)
    app4_frame.pack(side="left", fill="both", expand=True)
    app4 = ImageEditorApp(app4_frame, exclusion_zones_4)

    # import image
    prj_name = 'cadre_xxx'
    prj_name_var = tk.StringVar()
    # saisie du nom du pack cadre
    tk.Label(tk_root, text="Nom du set de cadre :").pack()
    texte_projet_name = tk.Entry(tk_root, textvariable=prj_name_var)
    texte_projet_name.insert(0, prj_name)
    texte_projet_name.pack()
    # Bouton pour enregistrer les cadres
    tk.Button(tk_root,
              text="enregistrer les cadres",
              command=lambda: save_images(app1, app4)).pack()

    tk_root.mainloop()