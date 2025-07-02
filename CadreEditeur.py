# -*- coding: utf-8 -*-
""" application d'édition de cadre pour PiBooth """
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

        # Dimension de l'interface
        self.window_width = 800
        self.window_height = 600
        self.canvas = tk.Canvas(root, width=self.window_width, height=self.window_height)
        self.canvas.pack()

        # Fond blanc
        self.image_de_font = Image.new('RGBA', (3600, 2400), (255, 255, 255, 255))
        self.draw = ImageDraw.Draw(self.image_de_font)

        # Redimensionnement pour affichage
        self.display_image = self.image_de_font.resize((self.window_width, self.window_height))
        self.tk_image = ImageTk.PhotoImage(self.display_image)
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        controls_frame = tk.Frame(root)
        controls_frame.pack()

        self.text = tk.StringVar()
        tk.Button(controls_frame, text="Importer une image", command=self.import_image).pack(side='left')
        tk.Entry(controls_frame, textvariable=self.text).pack(side='left')  # Aligner à gauche
        tk.Button(controls_frame, text="Ajouter le texte", command=self.add_text).pack(side='left')
        tk.Button(controls_frame, text="Enregistrer l'image", command=self.save_image).pack(side='left')

        self.imported_image = None
        self.imported_image_path = None
        self.original_image = None

        # Variables pour déplacer l'image importée
        self.image_position = (150, 150)  # Utiliser un tuple
        self.image_size = (100, 100)  # Utiliser un tuple

        # Définir des zones d'exclusion
        self.exclusion_zones = [
            (50, 50, 100, 100),
            (250, 200, 100, 50)
        ]

        # Événements de souris pour déplacer/redimensionner
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_image)
        self.canvas.bind("<MouseWheel>", self.resize_image)

        self.start_drag_position = None

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

            desired_width = self.window_width
            desired_height = int(desired_width / aspect_ratio)

            self.image_size = (desired_width, desired_height)
            self.imported_image = self.original_image.resize(self.image_size)

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
        Met à jour la position de l'image importée en fonction du mouvement du curseur.

        Paramètres :
            event (tk.Event) : L'événement de mouvement de la souris.
        """
        if self.start_drag_position:
            dx = event.x - self.start_drag_position[0]
            dy = event.y - self.start_drag_position[1]
            self.image_position = (self.image_position[0] + dx, self.image_position[1] + dy)
            self.start_drag_position = (event.x, event.y)
            self.update_canvas()

    def resize_image(self, event):
        """
        Redimensionne l'image importée en fonction de l'événement de la molette de la souris
        tout en conservant le ratio original.

        Paramètres :
            event (tk.Event) : L'événement de la molette de la souris.
        """
        if self.original_image:
            delta = 10 if event.delta > 0 else -10

            # Calculer la nouvelle taille en conservant le ratio
            original_width, original_height = self.original_image.size
            aspect_ratio = original_width / original_height

            new_width = self.image_size[0] + delta
            new_height = int(new_width / aspect_ratio)
            # min imagesize is 10/15px
            new_width = max(15, new_width)
            new_height = max(10, new_height)

            self.image_size = (new_width, new_height)
            self.imported_image = self.original_image.resize(self.image_size)

            self.update_canvas()

    def update_canvas(self):
        """
        Met à jour le canvas pour refléter l'état actuel de l'image avec les modifications.
        """
        display_image = self.image_de_font.resize((self.window_width, self.window_height))
        temp_image = display_image.copy()

        if self.imported_image:
            temp_image.paste(self.imported_image, self.image_position, self.imported_image)

        for zone in self.exclusion_zones:
            x, y, w, h = zone
            draw = ImageDraw.Draw(temp_image)
            draw.rectangle((x, y, x + w, y + h), fill=(255, 255, 255, 0))

        self.tk_image = ImageTk.PhotoImage(temp_image)
        self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)

    def save_image(self):
        """
        Ouvre une boîte de dialogue pour enregistrer l'image courante dans un fichier.
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")])
        if file_path:
            self.original_image.save(file_path)


if __name__ == "__main__":
    tk_root = tk.Tk()
    app = ImageEditorApp(tk_root)
    tk_root.mainloop()