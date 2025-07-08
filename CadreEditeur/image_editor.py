# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth """

import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont, ImageTk


class ImageEditorApp:
    """
    Une application d'édition d'image simple permettant aux utilisateurs
    d'importer des images, d'ajouter du texte, de déplacer/redimensionner les images,
    et d'enregistrer la composition finale.
    """

    def __init__(self, root):
        """
        Initialise l'application ImageEditorApp avec une fenêtre tkinter racine.

        Paramètres :
            root (tk.Tk) : La fenêtre tkinter racine.
        """
        self.root = root
        self.root.title("Éditeur d'image")
        # Dimension de l'interface, doit être de ratio 1.5
        self.WINDOWS_W = 600
        self.WINDOWS_H = 400
        self.IMAGE_W = 3600
        self.IMAGE_H = 2400
        self.RATIO = int(self.IMAGE_W / self.WINDOWS_W)
        self.canvas = tk.Canvas(root, width=self.WINDOWS_W, height=self.WINDOWS_H)
        self.canvas.pack()
        # Fond blanc
        self.image_de_font = Image.new('RGBA',
                                       (self.IMAGE_W, self.IMAGE_H),
                                       (255, 255, 255, 255))
        self.draw = ImageDraw.Draw(self.image_de_font)
        # Redimensionnement pour affichage
        self.image_export = self.image_de_font.copy()
        self.display_image = self.image_export.resize((self.WINDOWS_W, self.WINDOWS_H))
        self.tk_image = ImageTk.PhotoImage(self.display_image)
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        controls_frame = tk.Frame(root)
        controls_frame.pack()

        self.text = tk.StringVar()
        tk.Button(controls_frame, text="Importer une image", command=self.import_image).pack(side='left')
        tk.Entry(controls_frame, textvariable=self.text).pack(side='left')
        tk.Button(controls_frame, text="Ajouter le texte", command=self.add_text).pack(side='left')
        tk.Button(controls_frame, text="Enregistrer l'image", command=self.save_image).pack(side='left')

        self.imported_image_path = None
        self.display_imported_image = None
        self.image_imported_image = None
        self.original_image = None

        # Variables pour déplacer l'image importée
        self.display_position = (150, 150)
        self.image_position = (self.display_position[0] * self.RATIO,
                               self.display_position[1] * self.RATIO)
        self.display_imported_image_size = (0, 0)
        self.image_imported_image_size = (0, 0)

        # Définir des zones d'exclusion
        # <mxGeometry x="20" y="420" width="110" height="160" as="geometry" />
        # <mxGeometry x="145" y="420" width="110" height="160" as="geometry" />
        # <mxGeometry x="270" y="420" width="110" height="160" as="geometry" />
        # <mxGeometry x="20" y="20" width="280" height="350" as="geometry" />
        # Y X H W
        self.exclusion_zones = [
            (420, 20, 160, 110),
            (420, 145, 160, 110),
            (420, 270, 160, 110),
            (20, 20, 350, 280)
        ]

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

            desired_width = self.WINDOWS_W
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
        if self.start_drag_position:
            dx = event.x - self.start_drag_position[0]
            dy = event.y - self.start_drag_position[1]
            self.display_position = (self.display_position[0] + dx,
                                     self.display_position[1] + dy)
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
        display_image = self.image_de_font.resize((self.WINDOWS_W,
                                                   self.WINDOWS_H))

        temp_image = display_image.copy()
        self.image_export = self.image_de_font.copy()

        if self.display_imported_image:
            temp_image.paste(self.display_imported_image,
                             self.display_position,
                             self.display_imported_image)
            self.image_export.paste(self.image_imported_image,
                                    self.image_position,
                                    self.image_imported_image)

        # insère les zones tranparentes (Display et Image)
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


    def save_image(self):
        """
        Ouvre une boîte de dialogue pour enregistrer l'image courante dans un fichier.
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png")])
        if file_path:
            self.image_export.save(file_path)

if __name__ == "__main__":
    tk_root = tk.Tk()
    app = ImageEditorApp(tk_root)
    tk_root.mainloop()