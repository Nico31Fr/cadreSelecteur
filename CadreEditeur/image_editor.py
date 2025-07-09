# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth """

import tkinter as tk
from tkinter import filedialog, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageTk


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

        # creation dun canva qui va afficher l'image
        # Créer un cadre (Frame)
        self.frame = tk.Frame(root, borderwidth=2, relief="solid")
        self.frame.pack()

        self.canvas = tk.Canvas(self.frame, width=self.CANVA_W, height=self.CANVA_H)
        self.canvas.pack()
        # Fond blanc
        self.image_de_font = Image.new('RGBA',
                                       (self.IMAGE_W, self.IMAGE_H),
                                       (255, 255, 255, 255))
        self.draw = ImageDraw.Draw(self.image_de_font)
        # Redimensionnement pour affichage
        self.image_export = self.image_de_font.copy()
        self.display_image = self.image_export.resize((self.CANVA_W, self.CANVA_H))
        self.tk_image = ImageTk.PhotoImage(self.display_image)
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        self.controls_frame = tk.Frame(root)
        self.controls_frame.pack()

        # configure la grille pour les boutons
        self.controls_frame.rowconfigure(0, weight=2)
        self.controls_frame.rowconfigure(1, weight=1)
        self.controls_frame.rowconfigure(2, weight=1)
        self.controls_frame.rowconfigure(3, weight=1)
        self.controls_frame.columnconfigure(0, weight=1)
        self.controls_frame.columnconfigure(1, weight=2)

        self.text = tk.StringVar()
        # Créer un bouton pour ouvrir le sélecteur de couleur
        self.bouton = tk.Button(self.controls_frame, text="couleur du fond", command=self.choisir_couleur)
        self.bouton.grid(column=0, row=0, sticky=tk.EW, padx=5, pady=5)
        # Créer un label pour afficher la couleur sélectionnée
        self.label_couleur = tk.Label(self.controls_frame, text=" ", width=10, height=5)
        self.label_couleur.grid(column=1, row=0, sticky=tk.EW, padx=5, pady=5)
        tk.Entry(self.controls_frame, textvariable=self.text).grid(column=1, row=2, sticky=tk.EW, padx=5, pady=5)
        tk.Button(self.controls_frame, text="Ajouter le texte", command=self.add_text).grid(column=0, row=2, sticky=tk.EW, padx=5, pady=5)
        tk.Button(self.controls_frame, text="Importer une image", command=self.import_image).grid(column=0, row=3, sticky=tk.EW, padx=5, pady=5)
        tk.Button(self.controls_frame, text="Enregistrer l'image", command=self.save_image).grid(column=0, row=4, sticky=tk.EW, padx=5, pady=5)

        self.imported_image_path = None
        self.display_imported_image = None
        self.image_imported_image = None
        self.original_image = None
        self.background_couleur = '#FFFFFF'

        # Mettre à jour la couleur et le texte du label_couleur
        # avec la valeur par default
        self.label_couleur.config(bg=self.background_couleur)
        self.label_couleur.config(text=self.background_couleur)

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

        self.start_drag_position = None
        self.update_canvas()

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

    def add_text(self):
        """
        Ajoute du texte provenant du champ de texte à l'image à une position prédéfinie.
        """
        self.draw.text((200, 150), self.text.get(), fill=(0, 0, 0, 255), font=ImageFont.load_default())
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

        # insère les zones transparentes (Display et Image)
        for zone in self.exclusion_zones:
            d_x, d_y, d_w, d_h = zone
            i_x, i_y, i_w, i_h = d_x*self.RATIO, d_y*self.RATIO, d_w*self.RATIO, d_h*self.RATIO
            draw_d = ImageDraw.Draw(temp_image)
            draw_d.rectangle((d_x, d_y, d_x + d_w, d_y + d_h),
                           fill=(255, 255, 255, 0))
            draw_i = ImageDraw.Draw(self.image_export)
            draw_i.rectangle((i_x, i_y, i_x + i_w, i_y + i_h),
                           fill=(255, 255, 255, 0))

        # met a jour l'IHM
        self.tk_image = ImageTk.PhotoImage(temp_image)
        self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)

    def choisir_couleur(self):
        """ Ouvrir une boîte de dialogue de sélection de couleur """
        couleur = colorchooser.askcolor(title="Choisissez une couleur")
        if couleur[1]:
            self.background_couleur = couleur[1]
            # Mettre à jour la couleur et le texte du label
            self.label_couleur.config(bg=str(couleur[1]))
            self.label_couleur.config(text=str(couleur[1]))
            self.update_canvas()

    def save_image(self):
        """
        Ouvre une boîte de dialogue pour enregistrer l'image courante dans un fichier.
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png")])
        if file_path:
            self.image_export.save(file_path)

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
    # <mxGeometry x="20" y="420" width="110" height="160" as="geometry" />
    # <mxGeometry x="145" y="420" width="110" height="160" as="geometry" />
    # <mxGeometry x="270" y="420" width="110" height="160" as="geometry" />
    # <mxGeometry x="20" y="20" width="280" height="350" as="geometry" />
    # Y X H W
    exclusion_zones_4 = [
        (420, 20, 160, 110),
        (420, 145, 160, 110),
        (420, 270, 160, 110),
        (20, 20, 350, 280)]
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

    tk_root.mainloop()